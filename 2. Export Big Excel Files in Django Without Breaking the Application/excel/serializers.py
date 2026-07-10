from django.utils.text import get_valid_filename
from rest_framework import serializers

from excel.constants import DEFAULT_EXPORT_FILENAME, EXPORT_COLUMNS
from excel.models import Example


class ExampleExportSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default=DEFAULT_EXPORT_FILENAME,
    )

    class Meta:
        model = Example
        fields = (*EXPORT_COLUMNS, 'filename')

    def validate_filename(self, filename):
        filename = get_valid_filename(filename or DEFAULT_EXPORT_FILENAME)
        if not filename.lower().endswith('.xlsx'):
            filename = f'{filename}.xlsx'
        return filename
