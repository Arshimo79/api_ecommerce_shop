from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import ProductAttribute, CartItem, OrderItem, Image

@receiver([post_save, post_delete], sender=ProductAttribute)
def update_product_dynamic_fields(sender, instance, **kwargs):
    product = instance.product  # Adjust this if your FK is named differently

    attributes = product.attributes.all()
    product.update_dynamic_fields(attributes=attributes)
    product.calculate_total_sold(attributes=attributes)
    product.calculate_stock_quantity(attributes=attributes)

    # Use update to avoid triggering save()
    product.__class__.objects.filter(pk=product.pk).update(
        price=product.price,
        discounted_price=product.discounted_price,
        discount_amount=product.discount_amount,
        has_discount=product.has_discount,
        number_of_reviews=product.number_of_reviews,
        rates_average=product.rates_average,
        total_sold=product.total_sold,
        in_stock=product.in_stock,
        stock_quantity=product.stock_quantity,
    )

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

@receiver(post_save, sender=ProductAttribute)
def update_order_items(sender, instance, **kwargs):
    """
    Update the OrderItem instances when a Product is saved.
    """
    order_items = OrderItem.objects.filter(product=instance, order__is_paid=False)
    product = ProductAttribute.objects.get(id=instance.id)

    for order_item in order_items:
        if product.quantity == 0:
            order_item.delete()
        elif product.quantity < order_item.quantity:
            order_item.quantity = product.quantity
            order_item.save()

    for order_item in order_items:
        if (product.discount_active==True) and (product.discount_amount):
            order_item.price = product.price
            order_item.discounted_price = product.discounted_price
            order_item.discount = product.discount.discount
            order_item.discount_active = True
            order_item.save()
        else:
            order_item.price = product.price
            order_item.discounted_price = None
            order_item.discount = None
            order_item.discount_active = False
            order_item.save()
