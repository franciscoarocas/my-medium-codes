from django.utils.text import get_valid_filename
from rest_framework import serializers

from excel.constants import (
    DEFAULT_CSV_EXPORT_FILENAME,
    DEFAULT_EXPORT_FILENAME,
    EXPORT_COLUMNS,
)
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


class LightweightExampleExportSerializer(serializers.Serializer):
    filename = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default='lightweight_examples.xlsx',
    )

    def validate_filename(self, filename):
        filename = get_valid_filename(filename or 'lightweight_examples.xlsx')
        if not filename.lower().endswith('.xlsx'):
            filename = f'{filename}.xlsx'
        return filename


class ExampleCSVExportSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default=DEFAULT_CSV_EXPORT_FILENAME,
    )

    class Meta:
        model = Example
        fields = (*EXPORT_COLUMNS, 'filename')

    def validate_filename(self, filename):
        filename = get_valid_filename(filename or DEFAULT_CSV_EXPORT_FILENAME)
        if not filename.lower().endswith('.csv'):
            filename = f'{filename}.csv'
        return filename
