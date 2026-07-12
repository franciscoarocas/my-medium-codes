import csv
from io import StringIO

from django.http import FileResponse, HttpResponse
from django.utils.http import content_disposition_header
from rest_framework.decorators import api_view

from core.bucket.bucketLocal import BucketLocal
from csv_export.constants import CSV_CONTENT_TYPE, EXPORT_COLUMNS
from csv_export.models import Example, LightweightExample
from csv_export.serializers import (
    ExampleExportSerializer,
    LightweightExampleExportSerializer,
)


EXPORT_CHUNK_SIZE = 5_000


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
    queryset = Example.objects.filter(**filters).order_by('id')

    bucket = BucketLocal()
    stored_file = bucket.create_file(filename)

    try:
        with stored_file.path.open(
            'w',
            encoding='utf-8-sig',
            newline='',
        ) as output:
            writer = csv.writer(output)
            writer.writerow(EXPORT_COLUMNS)
            rows = queryset.values_list(*EXPORT_COLUMNS).iterator(
                chunk_size=EXPORT_CHUNK_SIZE,
            )
            writer.writerows(rows)
    except Exception:
        bucket.delete(stored_file.key)
        raise

    return FileResponse(
        bucket.open(stored_file.key),
        as_attachment=True,
        filename=filename,
        content_type=CSV_CONTENT_TYPE,
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
