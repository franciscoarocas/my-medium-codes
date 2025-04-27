from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class Invoice(models.Model):
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    date = models.DateField(auto_now_add=True)


class Product(models.Model):
    name = models.CharField(
                max_length=256,
                blank=False,
                null=False,
                unique=True
    )
    price = models.FloatField(blank=False, null=False)


class PurchasedProduct(models.Model):
    invoice = models.ForeignKey(
                Invoice,
                null=False,
                related_name='purchased_items',
                blank=False,
                on_delete=models.CASCADE
    )
    item = models.ForeignKey(
                Product,
                null=False,
                blank=False,
                on_delete=models.CASCADE
    )
    total_items = models.IntegerField(null=False, blank=False)
