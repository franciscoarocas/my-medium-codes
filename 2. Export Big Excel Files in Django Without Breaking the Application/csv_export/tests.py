import csv
from io import StringIO

from django.test import TestCase
from django.urls import reverse

from csv_export.constants import CSV_CONTENT_TYPE
from csv_export.models import Example, LightweightExample


def parse_csv(content):
    return list(csv.reader(StringIO(content.decode('utf-8-sig'))))


class ExampleExportViewTests(TestCase):
    def setUp(self):
        Example.objects.create(col_a='A1', col_b='B1', col_c='C1', col_d='D1')
        Example.objects.create(col_a='A2', col_b='B2', col_c='C2', col_d='D2')
        self.params = {
            'col_a': 'A1',
            'col_b': 'B1',
            'col_c': 'C1',
            'col_d': 'D1',
        }

    def test_v1_exports_filtered_examples_as_csv(self):
        response = self.client.get(reverse('export_examples_v1'), self.params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], CSV_CONTENT_TYPE)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="example.csv"',
        )
        self.assertEqual(parse_csv(response.content), [
            ['col_a', 'col_b', 'col_c', 'col_d'],
            ['A1', 'B1', 'C1', 'D1'],
        ])

    def test_v2_streams_filtered_examples_from_bucket(self):
        params = {**self.params, 'filename': 'streamed examples'}
        response = self.client.get(reverse('export_examples_v2'), params)
        content = b''.join(response.streaming_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], CSV_CONTENT_TYPE)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="streamed_examples.csv"',
        )
        self.assertEqual(parse_csv(content), [
            ['col_a', 'col_b', 'col_c', 'col_d'],
            ['A1', 'B1', 'C1', 'D1'],
        ])


class LightweightExampleExportViewTests(TestCase):
    def test_exports_lightweight_examples_as_csv(self):
        LightweightExample.objects.create(name='item-01', value=40)
        LightweightExample.objects.create(name='item-02', value=80)

        response = self.client.get(reverse('export_lightweight_examples_v1'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], CSV_CONTENT_TYPE)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="lightweight_examples.csv"',
        )
        self.assertEqual(parse_csv(response.content), [
            ['name', 'value'],
            ['item-01', '40'],
            ['item-02', '80'],
        ])
