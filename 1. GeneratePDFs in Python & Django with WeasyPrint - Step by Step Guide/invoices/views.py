from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.request import Request

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from invoices.models import Invoice
from invoices.serializer import InvoiceSerializer
from invoices.service import (
    attach_total_prices_to_invoice_data,
    generate_invoice_document
)

@api_view(['GET'])
def get_invoice(request: Request, invoice_id: int) -> Response:
    """
        Get invoice by ID and generate a PDF document.
        Parameters:
            - invoice_id: The ID of the invoice to retrieve.
        Returns:
            - Response: A PDF document containing the invoice details.
    """

    user_id = request.user.id

    invoice = get_object_or_404(Invoice, owner_id=user_id, id=invoice_id)

    invoice_data = InvoiceSerializer(invoice).data
    invoice_data = attach_total_prices_to_invoice_data(invoice_data)
    invoice_document = generate_invoice_document(invoice_data)

    response = HttpResponse(invoice_document, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{invoice_id}.pdf"'
    return response
