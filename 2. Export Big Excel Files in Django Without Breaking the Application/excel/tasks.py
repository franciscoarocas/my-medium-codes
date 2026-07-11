from celery import shared_task


@shared_task
def celery_health_check():
    return {'status': 'ok'}
