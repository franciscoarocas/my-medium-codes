
import copy
import os

from django.conf import settings

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS


from invoices.types import PDF_File, HtmlCssPathType, InvoiceType


def attach_total_prices_to_invoice_data(data: InvoiceType) -> InvoiceType:
    """
        Attaching the total price. 
        This price is the sum of the total items multiplied by the price
        Params:
            - data: Data which contains all data to calculate the total price
        Returns:
            Returns the same dict with the key 'total_price' attached
    """

    data = copy.deepcopy(data)

    total = 0

    for item in data['purchased_items']:
        total_price_item = item['item']['price'] * item['total_items']
        item['total_price'] = total_price_item
        total += total_price_item

    data['total_price'] = total

    return data


def generate_html_and_css(data: InvoiceType) -> HtmlCssPathType:
    """
        Generate the HTML and CSS files to be used in the PDF generation.
        This function uses the Jinja2 template engine to generate the HTML file
        and the WeasyPrint library to generate the CSS file.
        Params:
            - data: Data which contains all data to generate the HTML and CSS
        Returns:
            Returns a dict with the keys 'html' and 'css' which contains the
            paths to the HTML and CSS files
    """

    template_dir = os.path.join(settings.BASE_DIR, 'invoices', 'templates')

    style_file = os.path.join(
        settings.BASE_DIR,
        'invoices',
        'templates',
        'style.css'
    )

    env = Environment(loader=FileSystemLoader(template_dir))

    template = env.get_template('invoice.html')

    html_content = template.render(data)

    return {
        'html': html_content,
        'css': style_file
    }


def generate_invoice_document(data: InvoiceType) -> PDF_File:
    """
        Generate the PDF file from the data.
        This function uses the WeasyPrint library to generate the PDF file.
        Params:
            - data: Data which contains all data to generate the PDF file
        Returns:
            Returns the PDF file as bytes
    """

    files_path = generate_html_and_css(data)

    pdf_bytes = HTML(
                    string=files_path['html']
                ).write_pdf(
                    stylesheets=[CSS(files_path['css'])]
                )

    return pdf_bytes
