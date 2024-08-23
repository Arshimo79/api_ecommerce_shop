from django.db import models
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

    def default_discounted_price(self):
        first_attribute = next((attr for attr in self.attributes.all() if attr.quantity > 0), None)
        if first_attribute.discount_active == True:
            return first_attribute.discounted_price

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
    title = models.CharField(max_length=300)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name="products", blank=True)
    price = models.PositiveIntegerField(default=0)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    discount = models.ForeignKey(Discount, on_delete=models.PROTECT, related_name="products", null=True, blank=True)
    discount_amount = models.FloatField(blank=True, null=True)
    discount_active = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.title = self.product.title

        if self.discount_active:
            self.discounted_price = self.calculate_discounted_price()
            self.discount_amount = self.discount.discount
        else:
            self.discounted_price = None
            self.discount_amount = None
        
        super().save(*args, **kwargs)

    def calculate_discounted_price(self):
        return self.price - (self.price * (self.discount.discount/100))

    class Meta:
        verbose_name_plural='6. ProductAttributes'


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


class WishlistItem(models.Model):
    wish_list = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wish_items")

    class Meta:
        unique_together = [['wish_list', 'product']]


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    is_paid = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [['cart', 'product']]


class Order(models.Model):
    ORDER_STATUS_PAID = 'p'
    ORDER_STATUS_UNPAID = 'u'
    ORDER_STATUS_CANCELED = 'c'

    ORDER_STATUS = [
        (ORDER_STATUS_PAID, 'Paid'),
        (ORDER_STATUS_UNPAID, 'Unpaid'),
        (ORDER_STATUS_CANCELED, 'Canceled'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="orders")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=800)
    order_notes = models.CharField(max_length=500, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(choices=ORDER_STATUS, max_length=2, default=ORDER_STATUS_UNPAID)
    datetime_created = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(ProductAttribute, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    variant = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        unique_together = [['order', 'product']]
