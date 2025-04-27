from django.urls import path

from .views import get_invoice


urlpatterns = [
    path('<int:invoice_id>/', get_invoice, name='get_invoice'),
]
