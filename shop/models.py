from django.db import models
from django.urls import reverse
from uuid import uuid4

from core.models import CustomUser


class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural='1. Categories'

    def __str__(self):
        return self.title


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='subcategories')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural='2. SubCategories'

    def __str__(self):
        return f'{self.title}'


class Discount(models.Model):
    discount = models.FloatField()
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural='3. Discounts'

    def __str__(self):
        return f"{self.discount}"


class Variable(models.Model):
    COLOR_TYPE = 'color'
    SIZE_TYPE = 'size'
    VARIABLE_TYPE = [
        (COLOR_TYPE, 'color'),
        (SIZE_TYPE, 'size'),
    ]
    varaible_type = models.CharField(max_length=100, choices=VARIABLE_TYPE)
    title = models.CharField(max_length=100)
    color_code = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural='4. Variables'


class Product(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    slug = models.CharField(max_length=400, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.PROTECT, related_name='products')
    in_stock = models.BooleanField(default=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    def variables(self):
        variables = self.attributes.filter(quantity__gt=0).values_list('variable__title', flat=True).distinct()
        return variables

    def default_variable(self):
        first_attribute = next((attr for attr in self.attributes.all() if attr.quantity > 0), None)
        return first_attribute

    def default_price(self):
        first_attribute = next((attr for attr in self.attributes.all() if attr.quantity > 0), None)
        return first_attribute.price

    def has_default_off(self):
        first_attribute = next((attr for attr in self.attributes.all() if attr.quantity > 0), None)
        if first_attribute.discount_active == True:
            return True

        return False

    def default_off_count(self):
        first_attribute = next((attr for attr in self.attributes.all() if attr.quantity > 0), None)
        if first_attribute.discount_active == True:
            return first_attribute.discount.discount
        
        return None

    def default_price_after_off(self):
        first_attribute = next((attr for attr in self.attributes.all() if attr.quantity > 0), None)
        if first_attribute.discount_active == True:
            discount_amount = first_attribute.discount.discount
            default_price = first_attribute.price
            return default_price - (default_price * (discount_amount/100))
            
        return None

    def stock_quantity(self):
        stock_quantity = []
        for item in self.attributes.all():
            stock_quantity.append(item.quantity)
        return sum(stock_quantity)

    class Meta:
        verbose_name_plural='5. Products'

    def __str__(self):
        return self.title


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name="products", blank=True)
    price = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=0)
    discount = models.ForeignKey(Discount, on_delete=models.PROTECT, related_name="products", null=True, blank=True)
    discount_active = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    def price_after_off(self):
        return self.price - (self.price * (self.discount.discount/100))

    class Meta:
        verbose_name_plural='6. ProductAttributes'

    def __str__(self):
        return self.product.title


class Comment(models.Model):
    COMMENT_STATUS_WAITING      = 'w'
    COMMENT_STATUS_APPROVED     = 'a'
    COMMENT_STATUS_NOT_APPROVED = 'na'
    COMMENT_STATUS = [
        (COMMENT_STATUS_WAITING     , 'Waiting'),
        (COMMENT_STATUS_APPROVED    , 'Approved'),
        (COMMENT_STATUS_NOT_APPROVED, 'Not Approved'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    status = models.CharField(max_length=2, choices=COMMENT_STATUS, default=COMMENT_STATUS_WAITING)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural='7. Comments'


class ProductReview(models.Model):
    STAR_1 = '1'
    STAR_2 = '2'
    STAR_3 = '3'
    STAR_4 = '4'
    STAR_5 = '5'
    STAR = [
        (STAR_1, '1'),
        (STAR_2, '2'),
        (STAR_3, '3'),
        (STAR_4, '4'),
        (STAR_5, '5'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    review_rating = models.CharField(choices=STAR, max_length=2)

    class Meta:
        verbose_name_plural='8. Reviews'

    def get_review_rating(self):
        return self.review_rating


class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural='9. Wishlist'


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)

    def get_cart_total_price(self):
        cart_total_price = []

        for item in self.items.all():
            cart_total_price.append(item.price * item.quantity)
        return sum(cart_total_price)

    def __str__(self):
        return str(self.id)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductAttribute, on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.CharField(max_length=250, blank=True, null=True)
    price = models.PositiveIntegerField()
    quantity = models.PositiveSmallIntegerField(default=1)

    def get_item_total_price(self):
        return self.price * self.quantity


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=800)
    order_notes = models.CharField(max_length=500, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True) 
    datetime_modified = models.DateTimeField(auto_now=True)

    def get_order_total_price(self):
        order_total_price = []

        for item in self.items.all():
            order_total_price.append(item.price * item.quantity)
        return sum(order_total_price)

    def __str__(self):
        return f"Order {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductAttribute, on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.CharField(max_length=250, blank=True, null=True)
    price = models.PositiveIntegerField()
    quantity = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"OrderItem {self.id}: {self.product} X {self.quantity}."

    def get_item_total_price(self):
        return self.price * self.quantity
