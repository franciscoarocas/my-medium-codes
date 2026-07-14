from celery import shared_task

from csv_export.services import export_examples_to_bucket


@shared_task
def celery_health_check():
    return {'status': 'ok'}


@shared_task(bind=True)
def export_examples_task(self, filename, filters=None):
    stored_file = export_examples_to_bucket(filename, filters)
    return {
        'key': stored_file.key,
        'filename': filename,
    }
