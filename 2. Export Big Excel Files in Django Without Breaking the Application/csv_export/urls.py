from django.urls import path

from csv_export.views import (
    export_examples_v1,
    export_examples_v2,
    export_lightweight_examples_v1,
)


urlpatterns = [
    path('examples/export/v1/', export_examples_v1, name='export_examples_v1'),
    path('examples/export/v2/', export_examples_v2, name='export_examples_v2'),
    path(
        'examples/lightweight/v1/',
        export_lightweight_examples_v1,
        name='export_lightweight_examples_v1',
    ),
]
