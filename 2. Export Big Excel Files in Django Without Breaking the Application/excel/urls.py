from django.urls import path

from excel.views import export_examples_v1


urlpatterns = [
    path('examples/export/v1/', export_examples_v1, name='export_examples_v1'),
]
