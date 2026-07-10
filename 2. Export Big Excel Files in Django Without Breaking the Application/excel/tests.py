from io import BytesIO

from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from excel.models import Example


class ExampleExportViewTests(TestCase):
    def test_exports_filtered_examples_as_xlsx(self):
        Example.objects.create(col_a='A1', col_b='B1', col_c='C1', col_d='D1')
        Example.objects.create(col_a='A2', col_b='B2', col_c='C2', col_d='D2')

        response = self.client.get(reverse('example-export'), {
            'col_a': 'A1',
            'col_b': 'B1',
            'col_c': 'C1',
            'col_d': 'D1',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="example.xlsx"',
        )

        workbook = load_workbook(BytesIO(response.content))
        worksheet = workbook['Examples']
        rows = list(worksheet.values)

        self.assertEqual(rows[0], ('col_a', 'col_b', 'col_c', 'col_d'))
        self.assertEqual(rows[1], ('A1', 'B1', 'C1', 'D1'))
        self.assertEqual(len(rows), 2)

    def test_uses_filename_query_param_for_download(self):
        Example.objects.create(col_a='A1', col_b='B1', col_c='C1', col_d='D1')

        response = self.client.get(reverse('example-export'), {
            'col_a': 'A1',
            'col_b': 'B1',
            'col_c': 'C1',
            'col_d': 'D1',
            'filename': 'filtered examples',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="filtered_examples.xlsx"',
        )

    def test_rejects_filename_over_limit(self):
        response = self.client.get(reverse('example-export'), {
            'col_a': 'A1',
            'col_b': 'B1',
            'col_c': 'C1',
            'col_d': 'D1',
            'filename': 'a' * 101,
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('filename', response.json())
