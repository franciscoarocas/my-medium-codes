from django.urls import path

from excel.views import export_examples


urlpatterns = [
    path('examples/export/', export_examples, name='example-export'),
]
