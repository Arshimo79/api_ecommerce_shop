from .managers import ProductManager

from core.models import CustomUser

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg

from uuid import uuid4
import uuid


class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural='1. Categories'

    def __str__(self):
        return f"{self.title}"


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='subcategories')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural='2. SubCategories'

    def __str__(self):
        return f"{self.title}"


class Discount(models.Model):
    discount = models.DecimalField(max_digits=3, decimal_places=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="discount_amount")
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

    variable_type = models.CharField(max_length=100, choices=VARIABLE_TYPE)
    title = models.CharField(max_length=100)
    color_code = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name_plural='4. Variables'

    def __str__(self):
        return f"{self.title}"


class Product(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    slug = models.CharField(max_length=400, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.PROTECT, related_name='products')
    price = models.DecimalField(max_digits=9, decimal_places=0, null=True, blank=True)
    discounted_price = models.DecimalField(max_digits=9, decimal_places=0, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=3, decimal_places=0, null=True, blank=True)
    has_discount = models.BooleanField(default=False)
    rates_average = models.FloatField(null=True, blank=True)
    number_of_reviews = models.IntegerField(null=True, blank=True)
    in_stock = models.BooleanField(default=True)
    total_sold = models.PositiveIntegerField(default=0)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    def variables(self):
        return self.attributes.values_list('variable__title', flat=True).distinct() or None

    def default_attribute(self):
        discounted_attrs = self.attributes.filter(
            discount_active=True,
            discounted_price__isnull=False,
            quantity__gt=0
        ).order_by('discounted_price')

        if discounted_attrs.exists():
            return discounted_attrs.first() or None

        regular_attrs = self.attributes.filter(
            quantity__gt=0
        ).order_by('price')

        if regular_attrs.exists():
            return regular_attrs.first() or None

    def stock_quantity(self):
        return sum([item.quantity for item in self.attributes.all()])
    
    def calculate_total_sold(self):
        self.total_sold = sum([item.total_sold for item in self.attributes.all()])

    def update_dynamic_fields(self):
        from .models import ProductAttribute

        discounted_attrs = ProductAttribute.objects.filter(
            product=self,
            quantity__gt=0,
            discount_active=True,
            discounted_price__isnull=False
        ).order_by('discounted_price')

        normal_attrs = ProductAttribute.objects.filter(
            product=self,
            quantity__gt=0,
            discount_active=False
        ).order_by('price')

        discounted = discounted_attrs.first()
        normal = normal_attrs.first()

        self.price = int(discounted.price) if discounted else int(normal.price) if normal else None
        self.discounted_price = int(discounted.discounted_price) if discounted else None
        self.discount_amount = discounted.discount_amount if discounted else 0
        self.has_discount = bool(discounted)

        reviews = self.reviews.all()
        self.number_of_reviews = reviews.count()
        self.rates_average = reviews.aggregate(avg=Avg('review_rating'))['avg']

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            super().save(*args, **kwargs)

            self.update_dynamic_fields()
            self.calculate_total_sold()

            self.__class__.objects.filter(pk=self.pk).update(
                price=self.price,
                discounted_price=self.discounted_price,
                discount_amount=self.discount_amount,
                has_discount=self.has_discount,
                number_of_reviews=self.number_of_reviews,
                rates_average=self.rates_average,
                total_sold=self.total_sold
            )
        else:
            self.update_dynamic_fields()
            self.calculate_total_sold()
            super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural='5. Products'

    def __str__(self):
        return f"{self.title}"
    
    objects = ProductManager()


class ProductAttribute(models.Model):
    title = models.CharField(max_length=300)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name="products", blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=0, default=0)
    total_sold = models.PositiveIntegerField(default=0)
    discounted_price = models.DecimalField(max_digits=9, decimal_places=0, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    discount = models.ForeignKey(Discount, on_delete=models.PROTECT, related_name="products", null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=3, decimal_places=0, validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    discount_active = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    def calculate_discounted_price(self):
        if not self.discount or not self.discount_active:
            return None
        
        discount_value = (self.price) * (self.discount.discount / 100)
        return self.price - discount_value

    def save(self, *args, **kwargs):
        if self.discount_active and self.discount:
            self.discounted_price = self.calculate_discounted_price()
            self.discount_amount = self.discount.discount
        else:
            self.discounted_price = None
            self.discount_amount = None
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural='6. ProductAttributes'

    def __str__(self):
        return f"{self.title}"


class Image(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='product_images/')
    title = models.CharField(max_length=250, blank=True, null=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)


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
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural='8. Reviews'


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [['cart', 'product']]


class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wishlist")
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)


class WishlistItem(models.Model):
    wish_list = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wish_items")

    class Meta:
        unique_together = [['wish_list', 'product']]


class ShippingMethod(models.Model):
    shipping_method = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=0, blank=True, null=True)
    delivery_time = models.DurationField()
    shipping_method_active = models.BooleanField(default=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.shipping_method


class Address(models.Model):
    TEHRAN = 'Tehran'
    KARAJ = 'Karaj'
    CITIES = [
        (TEHRAN, 'Tehran'),
        (KARAJ, 'Karaj'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    receiver_name = models.CharField(max_length=100)
    receiver_family = models.CharField(max_length=150)
    receiver_phone_number = models.CharField(max_length=13)
    receiver_city = models.CharField(max_length=85, choices=CITIES)
    receiver_address = models.TextField()
    receiver_postal_code = models.CharField(max_length=20)
    receiver_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    receiver_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural='9. Addresses'

    def __str__(self) -> str:
        return f"address: {self.receiver_address}."


class Order(models.Model):
    ORDER_STATUS_CANCELED = 'c'
    ORDER_STATUS_NOT_DELIVERED = 'nd'
    ORDER_STATUS_DELIVERED = 'd'
    ORDER_STATUS = [
        (ORDER_STATUS_CANCELED, 'Canceled'),
        (ORDER_STATUS_NOT_DELIVERED, 'Not Delivered'),
        (ORDER_STATUS_DELIVERED, 'Delivered'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="orders")
    receiver_name = models.CharField(max_length=100)
    receiver_family = models.CharField(max_length=150)
    receiver_phone_number = models.CharField(max_length=13)
    receiver_city = models.CharField(max_length=85)
    receiver_address = models.TextField()
    receiver_postal_code = models.CharField(max_length=20)
    receiver_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    receiver_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    status = models.CharField(choices=ORDER_STATUS, max_length=2, default=ORDER_STATUS_NOT_DELIVERED)
    is_paid = models.BooleanField(default=False)
    number = models.CharField(max_length=50, unique=True, editable=False)
    tracking_code = models.CharField(max_length=15, unique=True, blank=True, null=True)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.PROTECT, related_name="orders")
    shipping_price = models.DecimalField(max_digits=6, decimal_places=0, default=None, blank=True, null=True)
    total_price = models.DecimalField(max_digits=9, decimal_places=0)
    total_discount_amount = models.DecimalField(max_digits=9, decimal_places=0, blank=True, null=True)
    datetime_modified = models.DateTimeField(auto_now=True)
    datetime_created = models.DateTimeField(auto_now_add=True)

    def generate_unique_order_number(self):
        return str(12345 + self.id)

    def generate_unique_tracking_code(self):
        while True:
            code = uuid.uuid4().hex[:15].upper()    
            if not Order.objects.filter(tracking_code=code).exists():
                return code

    def get_products_total_price(self):
        calculate_item_prices = [item.calculate_discounted_price() * 
                                 item.quantity if (item.discount_active and item.discount) else item.price * item.quantity for item in self.items.all()]

        return sum(calculate_item_prices)

    def get_order_total_price(self):
        calculate_item_prices = [item.calculate_discounted_price() * 
                                 item.quantity if (item.discount_active and item.discount) else item.price * item.quantity for item in self.items.all()]
        
        if self.shipping_price == None:
            return sum(calculate_item_prices)
        else:
            return sum(calculate_item_prices) + self.shipping_method.price

    def get_order_total_discount(self):
        return sum(
            (item.price - (item.calculate_discounted_price()) * item.quantity)
            for item in self.items.all() if (item.discount_active and item.discount)
        )

    def save(self, *args, **kwargs):
        if not self.number:
            super().save(*args, **kwargs)
            self.number = self.generate_unique_order_number()
            self.save(update_fields=['number'])
        else:
            super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural='Orders'

    def __str__(self):
        return f"Order {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductAttribute, on_delete=models.PROTECT, related_name='order_items')
    price = models.DecimalField(max_digits=9, decimal_places=0)
    variable = models.CharField(max_length=250, blank=True, null=True)
    quantity = models.PositiveSmallIntegerField()
    discount = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True)
    discounted_price = models.DecimalField(max_digits=9, decimal_places=0, blank=True, null=True)
    discount_active = models.BooleanField(default=False)

    def get_item_total_price(self):
        if self.discount_active and self.discount:
            return self.discounted_price * self.quantity
        return self.price * self.quantity

    def calculate_discounted_price(self):
        if not self.discount or not self.discount_active:
            return None

        discount_value = (self.price) * (self.discount / 100)
        return self.price - discount_value

    def save(self, *args, **kwargs):
        self.title = self.product.title
        super().save(*args, **kwargs)

        if self.discount_active and self.discount:
            self.discounted_price = self.calculate_discounted_price()
        else:
            self.discounted_price = None

    class Meta:
        unique_together = [['order', 'product']]
        verbose_name_plural='OrderItems'

    def __str__(self):
        return f"OrderItem {self.id}: {self.product}({self.variable}) X {self.quantity}."
