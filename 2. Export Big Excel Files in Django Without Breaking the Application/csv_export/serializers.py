from django.utils.text import get_valid_filename
from rest_framework import serializers

from csv_export.constants import (
    DEFAULT_EXPORT_FILENAME,
    DEFAULT_LIGHTWEIGHT_EXPORT_FILENAME,
    EXPORT_COLUMNS,
)
from csv_export.models import Example


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
        extra_kwargs = {
            column: {'required': False}
            for column in EXPORT_COLUMNS
        }

    def validate_filename(self, filename):
        filename = get_valid_filename(filename or DEFAULT_EXPORT_FILENAME)
        if not filename.lower().endswith('.csv'):
            filename = f'{filename}.csv'
        return filename


class LightweightExampleExportSerializer(serializers.Serializer):
    filename = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default=DEFAULT_LIGHTWEIGHT_EXPORT_FILENAME,
    )

    def validate_filename(self, filename):
        filename = get_valid_filename(
            filename or DEFAULT_LIGHTWEIGHT_EXPORT_FILENAME,
        )
        if not filename.lower().endswith('.csv'):
            filename = f'{filename}.csv'
        return filename
