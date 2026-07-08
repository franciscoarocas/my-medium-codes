from rest_framework import serializers


class ExampleExportSerializer(serializers.Serializer):
    col_a = serializers.CharField(max_length=255)
    col_b = serializers.CharField(max_length=255)
    col_c = serializers.CharField(max_length=255)
    col_d = serializers.CharField(max_length=255)
