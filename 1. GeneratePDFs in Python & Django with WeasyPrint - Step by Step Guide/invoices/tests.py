from PyPDF2 import PdfReader
import io

from rest_framework.test import APITestCase
from rest_framework import status
from invoices.models import Invoice
from django.contrib.auth.models import User
from django.urls import reverse

from django.test import TestCase
from unittest.mock import patch, MagicMock
from invoices.service import (
    attach_total_prices_to_invoice_data,
    generate_html_and_css,
    generate_invoice_document
)

import os


class ServiceTests(TestCase):

    def test_attach_total_prices_to_invoice_data(self):
        data = {
            'purchased_items': [
                {'item': {'price': 10}, 'total_items': 2},
                {'item': {'price': 5}, 'total_items': 4}
            ]
        }

        expected_result = {
            'purchased_items': [
                {'item': {'price': 10}, 'total_items': 2, 'total_price': 20},
                {'item': {'price': 5}, 'total_items': 4, 'total_price': 20}
            ],
            'total_price': 40
        }

        result = attach_total_prices_to_invoice_data(data)
        self.assertEqual(result, expected_result)

    @patch('invoices.service.Environment')
    @patch('invoices.service.settings')
    def test_generate_html_and_css(self, mock_settings, mock_environment):
        mock_settings.BASE_DIR = os.path.join('fake', 'base', 'dir')
        mock_env = MagicMock()
        mock_environment.return_value = mock_env
        mock_template = mock_env.get_template.return_value
        mock_template.render.return_value = '<html>Rendered HTML</html>'

        data = {'key': 'value'}
        result = generate_html_and_css(data)

        self.assertEqual(result['html'], '<html>Rendered HTML</html>')
        self.assertEqual(
            result['css'],
            os.path.join(
                'fake',
                'base',
                'dir',
                'invoices',
                'templates',
                'style.css'
            )
        )
        mock_env.get_template.assert_called_once_with('invoice.html')
        mock_template.render.assert_called_once_with(data)

    @patch('invoices.service.HTML')
    @patch('invoices.service.CSS')
    @patch('invoices.service.generate_html_and_css')
    def test_generate_invoice_document(
        self,
        mock_generate_html_and_css,
        mock_css,
        mock_html
    ):
        mock_generate_html_and_css.return_value = {
            'html': '<html>Rendered HTML</html>',
            'css': os.path.join('fake', 'path', 'style.css')
        }
        mock_pdf = MagicMock()
        mock_html.return_value.write_pdf.return_value = mock_pdf

        data = {'key': 'value'}
        result = generate_invoice_document(data)

        self.assertEqual(result, mock_pdf)
        mock_generate_html_and_css.assert_called_once_with(data)
        mock_html.assert_called_once_with(string='<html>Rendered HTML</html>')
        mock_html.return_value.write_pdf.assert_called_once_with(
            stylesheets=[mock_css(os.path.join('fake', 'path', 'style.css'))]
        )


class GetinvoiceViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@email.com'
        )
        self.client.force_authenticate(user=self.user)

        self.invoice = Invoice.objects.create(owner=self.user)

    @patch('invoices.views.InvoiceSerializer')
    @patch('invoices.views.attach_total_prices_to_invoice_data')
    def test_get_invoice(
        self,
        mock_attach_total_prices,
        mock_invoice_serializer
    ):
        mock_invoice_serializer.return_value.data = {
            'id': self.invoice.id,
            'purchased_items': []
        }

        mock_attach_total_prices.return_value = {
            'id': self.invoice.id,
            'purchased_items': [],
            'total_price': 100
        }

        url = reverse("get_invoice", args=[self.invoice.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('Content-Disposition', response)
        self.assertTrue(response['Content-Disposition'].startswith(
            'inline; filename="invoice_'
        ))

        mock_invoice_serializer.assert_called_once_with(self.invoice)
        mock_attach_total_prices.assert_called_once()

        pdf_stream = io.BytesIO(response.content)
        pdf_reader = PdfReader(pdf_stream)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

        self.assertIn("100", pdf_text)
        self.assertIn(str(self.invoice.id), pdf_text)
