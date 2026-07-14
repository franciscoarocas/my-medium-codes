import csv

from core.bucket.bucketLocal import BucketLocal
from csv_export.constants import EXPORT_COLUMNS
from csv_export.models import Example


EXPORT_CHUNK_SIZE = 5_000


def export_examples_to_bucket(filename, filters=None):
    filters = filters or {}
    queryset = Example.objects.filter(**filters).order_by('id')
    bucket = BucketLocal()
    stored_file = bucket.create_file(filename)

    try:
        with stored_file.path.open(
            'w',
            encoding='utf-8-sig',
            newline='',
        ) as output:
            writer = csv.writer(output)
            writer.writerow(EXPORT_COLUMNS)
            rows = queryset.values_list(*EXPORT_COLUMNS).iterator(
                chunk_size=EXPORT_CHUNK_SIZE,
            )
            writer.writerows(rows)
    except Exception:
        bucket.delete(stored_file.key)
        raise

    return stored_file

