from rest_framework import serializers
from django.utils.text import get_valid_filename

from excel.constants import DEFAULT_EXPORT_FILENAME


class ExampleExportSerializer(serializers.Serializer):
    col_a = serializers.CharField(max_length=255)
    col_b = serializers.CharField(max_length=255)
    col_c = serializers.CharField(max_length=255)
    col_d = serializers.CharField(max_length=255)
    filename = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default=DEFAULT_EXPORT_FILENAME,
    )

    def validate_filename(self, filename):
        filename = get_valid_filename(filename or DEFAULT_EXPORT_FILENAME)
        if not filename.lower().endswith('.xlsx'):
            filename = f'{filename}.xlsx'
        return filename
