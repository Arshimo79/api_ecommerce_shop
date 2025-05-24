from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ProductAttribute, CartItem


@receiver(post_save, sender=ProductAttribute)
def update_product_stock(sender, instance, **kwargs):
    product = instance.product

    if product.stock_quantity() == 0:
        product.in_stock = False
    else:
        product.in_stock = True

    product.save()

@receiver(post_save, sender=ProductAttribute)
def update_cart_items(sender, instance, **kwargs):
    """
    Update the CartItem instances when a Product is saved.
    """
    cart_items = CartItem.objects.filter(product=instance)
    product = ProductAttribute.objects.get(id=instance.id)
    if product.discount_active:
        for cart_item in cart_items:
            cart_item.price = product.discounted_price
            cart_item.save()
    else:
        for cart_item in cart_items:
            cart_item.price = product.price
            cart_item.save()

    for cart_item in cart_items:
        if product.quantity == 0:
            cart_item.delete()
        elif product.quantity < cart_item.quantity:
            cart_item.quantity = product.quantity
            cart_item.save()
