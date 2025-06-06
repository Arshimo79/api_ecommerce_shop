from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import ProductAttribute, CartItem, Image


@receiver(post_save, sender=ProductAttribute)
def update_product_stock(sender, instance, **kwargs):
    product = instance.product

    if product.stock_quantity() == 0:
        product.in_stock = False
    else:
        product.in_stock = True

    product.save()

@receiver([post_save, post_delete], sender=Image)
def update_product_main_image(sender, instance, **kwargs):
    """Signal to update product's main image when Image objects change."""
    product = instance.product
    # Clear the cached main image
    if hasattr(product, '_main_image'):
        delattr(product, '_main_image')
    # Trigger main_image update
    product.main_image()

@receiver(post_save, sender=ProductAttribute)
def update_cart_items(sender, instance, **kwargs):
    """
    Update the CartItem instances when a Product is saved.
    """
    cart_items = CartItem.objects.filter(product=instance)
    product = ProductAttribute.objects.get(id=instance.id)

    for cart_item in cart_items:
        if product.quantity == 0:
            cart_item.delete()
        elif product.quantity < cart_item.quantity:
            cart_item.quantity = product.quantity
            cart_item.save()
