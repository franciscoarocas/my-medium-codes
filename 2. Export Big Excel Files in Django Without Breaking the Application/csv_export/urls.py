from django.urls import path

from csv_export.views import (
    create_examples_export_job,
    download_examples_export_job,
    export_examples_v1,
    export_examples_v2,
    export_lightweight_examples_v1,
    get_examples_export_job,
)


urlpatterns = [
    path('examples/export/v1/', export_examples_v1, name='export_examples_v1'),
    path('examples/export/v2/', export_examples_v2, name='export_examples_v2'),
    path(
        'examples/export/v2/jobs/',
        create_examples_export_job,
        name='create_examples_export_job',
    ),
    path(
        'examples/export/v2/jobs/<str:task_id>/',
        get_examples_export_job,
        name='export_examples_job_status',
    ),
    path(
        'examples/export/v2/jobs/<str:task_id>/download/',
        download_examples_export_job,
        name='export_examples_job_download',
    ),
    path(
        'examples/lightweight/v1/',
        export_lightweight_examples_v1,
        name='export_lightweight_examples_v1',
    ),
]
