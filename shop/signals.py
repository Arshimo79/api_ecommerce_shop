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
    Uses bulk operations for better performance.
    """
    # Get all unpaid order items for this product in a single query
    order_items = OrderItem.objects.filter(
        product=instance,
        order__is_paid=False
    ).select_related('order')

    if not order_items.exists():
        return

    # Handle zero quantity case - delete all related order items
    if instance.quantity == 0:
        order_items.delete()
        return

    # Prepare bulk update data
    items_to_update = []

    # Update quantity
    for order_item in order_items:
        if instance.quantity < order_item.quantity:
            order_item.quantity = instance.quantity
            items_to_update.append(order_item)
        else:
            items_to_update.append(order_item)

    # Update prices and discounts for all items
    for order_item in items_to_update:
        order_item.price = instance.price
        if instance.discount_active and instance.discount_amount:
            order_item.discounted_price = instance.discounted_price
            order_item.discount = instance.discount.discount
            order_item.discount_active = True
        else:
            order_item.discounted_price = None
            order_item.discount = None
            order_item.discount_active = False

    # Bulk update all modified items
    if items_to_update:
        OrderItem.objects.bulk_update(
            items_to_update,
            fields=['quantity', 'price', 'discounted_price', 'discount', 'discount_active', ]
        )
