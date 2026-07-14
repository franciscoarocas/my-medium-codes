import csv
from io import StringIO

from django.http import FileResponse, HttpResponse
from django.urls import reverse
from django.utils.http import content_disposition_header
from celery.result import AsyncResult
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.bucket.bucketLocal import BucketLocal
from csv_export.constants import CSV_CONTENT_TYPE, EXPORT_COLUMNS
from csv_export.models import Example, LightweightExample
from csv_export.serializers import (
    ExampleExportSerializer,
    LightweightExampleExportSerializer,
)
from csv_export.services import export_examples_to_bucket
from csv_export.tasks import export_examples_task


class DeletingFileResponse(FileResponse):
    def __init__(self, *args, delete_callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.delete_callback = delete_callback

    def close(self):
        try:
            super().close()
        finally:
            if self.delete_callback is not None:
                callback, self.delete_callback = self.delete_callback, None
                callback()


@api_view(['GET'])
def export_examples_v1(request):
    serializer = ExampleExportSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    filename = serializer.validated_data['filename']
    filters = {
        column: serializer.validated_data[column]
        for column in EXPORT_COLUMNS
        if column in serializer.validated_data
    }
    queryset = Example.objects.filter(**filters).order_by('id')

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(EXPORT_COLUMNS)
    writer.writerows(queryset.values_list(*EXPORT_COLUMNS))

    response = HttpResponse(output.getvalue(), content_type=CSV_CONTENT_TYPE)
    response['Content-Disposition'] = content_disposition_header(
        as_attachment=True,
        filename=filename,
    )
    return response


@api_view(['GET'])
def export_examples_v2(request):
    serializer = ExampleExportSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    filename = serializer.validated_data['filename']
    filters = {
        column: serializer.validated_data[column]
        for column in EXPORT_COLUMNS
        if column in serializer.validated_data
    }
    stored_file = export_examples_to_bucket(filename, filters)
    bucket = BucketLocal()

    return DeletingFileResponse(
        bucket.open(stored_file.key),
        as_attachment=True,
        filename=filename,
        content_type=CSV_CONTENT_TYPE,
        delete_callback=lambda: bucket.delete(stored_file.key),
    )


@api_view(['POST'])
def create_examples_export_job(request):
    serializer = ExampleExportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    filename = serializer.validated_data['filename']
    filters = {
        column: serializer.validated_data[column]
        for column in EXPORT_COLUMNS
        if column in serializer.validated_data
    }
    task = export_examples_task.delay(filename, filters)

    return Response(
        {
            'id': task.id,
            'state': task.state,
            'status_url': request.build_absolute_uri(
                reverse('export_examples_job_status', args=(task.id,))
            ),
        },
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['GET'])
def get_examples_export_job(request, task_id):
    task = AsyncResult(task_id)
    payload = {'id': task.id, 'state': task.state}

    if task.successful():
        payload['download_url'] = request.build_absolute_uri(
            reverse('export_examples_job_download', args=(task.id,))
        )
    elif task.failed():
        payload['error'] = 'The export could not be generated.'

    return Response(payload)


@api_view(['GET'])
def download_examples_export_job(request, task_id):
    task = AsyncResult(task_id)
    if not task.successful():
        return Response(
            {'id': task.id, 'state': task.state},
            status=status.HTTP_409_CONFLICT,
        )

    result = task.result
    bucket = BucketLocal()
    try:
        file_handle = bucket.open(result['key'])
    except FileNotFoundError:
        return Response(
            {'detail': 'The export file is no longer available.'},
            status=status.HTTP_410_GONE,
        )

    return DeletingFileResponse(
        file_handle,
        as_attachment=True,
        filename=result['filename'],
        content_type=CSV_CONTENT_TYPE,
        delete_callback=lambda: bucket.delete(result['key']),
    )


@api_view(['GET'])
def export_lightweight_examples_v1(request):
    serializer = LightweightExampleExportSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    filename = serializer.validated_data['filename']

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(('name', 'value'))
    writer.writerows(
        LightweightExample.objects.order_by('id').values_list('name', 'value')
    )

    response = HttpResponse(output.getvalue(), content_type=CSV_CONTENT_TYPE)
    response['Content-Disposition'] = content_disposition_header(
        as_attachment=True,
        filename=filename,
    )
    return response
