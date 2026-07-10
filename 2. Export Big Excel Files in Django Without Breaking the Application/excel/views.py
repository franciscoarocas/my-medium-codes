from io import BytesIO

from django.http import HttpResponse
from django.utils.http import content_disposition_header
from openpyxl import Workbook
from rest_framework.decorators import api_view

from excel.constants import EXCEL_CONTENT_TYPE, EXPORT_COLUMNS
from excel.models import Example
from excel.serializers import ExampleExportSerializer


@api_view(['GET'])
def export_examples_v1(request):
    serializer = ExampleExportSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    filename = serializer.validated_data.get('filename')
    filters = {
        column: serializer.validated_data[column]
        for column in EXPORT_COLUMNS
    }
    queryset = Example.objects.filter(**filters).order_by('id')

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Examples'
    worksheet.append(EXPORT_COLUMNS)

    rows = queryset.values_list(*EXPORT_COLUMNS)
    for row in rows:
        worksheet.append(row)

    output = BytesIO()
    workbook.save(output)

    response = HttpResponse(
        output.getvalue(),
        content_type=EXCEL_CONTENT_TYPE,
    )
    response['Content-Disposition'] = content_disposition_header(
        as_attachment=True,
        filename=filename,
    )
    return response
