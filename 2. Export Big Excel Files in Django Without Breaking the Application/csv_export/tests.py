import csv
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.bucket.bucketLocal import BucketLocal
from csv_export.constants import CSV_CONTENT_TYPE
from csv_export.models import Example, LightweightExample
from csv_export.tasks import export_examples_task


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
        bucket = BucketLocal()
        files_before = set(bucket.root.iterdir())
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
        response.close()
        self.assertEqual(set(bucket.root.iterdir()), files_before)

    def test_celery_task_uses_the_memory_efficient_export(self):
        result = export_examples_task.run(
            'async.csv',
            {'col_a': 'A1'},
        )
        bucket = BucketLocal()

        try:
            self.assertEqual(result['filename'], 'async.csv')
            with bucket.open(result['key']) as exported:
                self.assertEqual(parse_csv(exported.read()), [
                    ['col_a', 'col_b', 'col_c', 'col_d'],
                    ['A1', 'B1', 'C1', 'D1'],
                ])
        finally:
            bucket.delete(result['key'])

    @patch('csv_export.views.export_examples_task.delay')
    def test_creates_an_async_export_job(self, delay):
        delay.return_value = SimpleNamespace(id='task-123', state='PENDING')

        response = self.client.post(
            reverse('create_examples_export_job'),
            {'filename': 'async export', 'col_a': 'A1'},
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()['id'], 'task-123')
        self.assertIn('/csv/examples/export/v2/jobs/task-123/', response.json()['status_url'])
        delay.assert_called_once_with('async_export.csv', {'col_a': 'A1'})

    @patch('csv_export.views.AsyncResult')
    def test_reports_a_completed_async_export(self, async_result):
        task = SimpleNamespace(
            id='task-123',
            state='SUCCESS',
            successful=lambda: True,
            failed=lambda: False,
        )
        async_result.return_value = task

        response = self.client.get(
            reverse('export_examples_job_status', args=('task-123',))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['state'], 'SUCCESS')
        self.assertIn('/download/', response.json()['download_url'])

    @patch('csv_export.views.AsyncResult')
    def test_downloads_and_deletes_a_completed_async_export(self, async_result):
        result = export_examples_task.run('async.csv', {'col_a': 'A1'})
        task = SimpleNamespace(
            id='task-123',
            state='SUCCESS',
            result=result,
            successful=lambda: True,
        )
        async_result.return_value = task
        bucket = BucketLocal()

        response = self.client.get(
            reverse('export_examples_job_download', args=('task-123',))
        )
        content = b''.join(response.streaming_content)
        response.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse_csv(content)[1], ['A1', 'B1', 'C1', 'D1'])
        with self.assertRaises(FileNotFoundError):
            bucket.open(result['key'])


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
