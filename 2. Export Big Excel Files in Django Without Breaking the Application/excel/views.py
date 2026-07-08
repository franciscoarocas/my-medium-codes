from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from excel.models import Example
from excel.serializers import ExampleExportSerializer


@api_view(['GET'])
def export_examples(request):
    serializer = ExampleExportSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    queryset = Example.objects.filter(**serializer.validated_data).order_by('id')

    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet(title='Examples')
    worksheet.append(['col_a', 'col_b', 'col_c', 'col_d'])

    for row in queryset.values_list('col_a', 'col_b', 'col_c', 'col_d'):
        worksheet.append(row)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="examples.xlsx"'
    return response
