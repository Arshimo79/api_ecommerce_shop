from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Product, ProductAttribute


@receiver(post_save, sender=ProductAttribute)
def update_product_stock(sender, instance, **kwargs):
    product = instance.product

    if product.stock_quantity() == 0:
        product.in_stock = False
    else:
        product.in_stock = True

    product.save()
