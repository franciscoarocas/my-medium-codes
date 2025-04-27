
from rest_framework.serializers import (
    ModelSerializer,
    StringRelatedField,
    SerializerMethodField
)

from invoices.models import Invoice, Product, PurchasedProduct


class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']


class PurchasedProductSerializer(ModelSerializer):
    item = ProductSerializer(read_only=True)

    class Meta:
        model = PurchasedProduct
        fields = ['item', 'total_items']


class InvoiceSerializer(ModelSerializer):
    purchased_items = PurchasedProductSerializer(many=True, read_only=True)
    owner = StringRelatedField()
    email = SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ['id', 'owner', 'email', 'date', 'purchased_items']

    def get_email(self, obj: Invoice) -> str:
        return obj.owner.email
