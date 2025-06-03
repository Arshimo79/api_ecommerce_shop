from .models import *

from dal import autocomplete

from datetime import timedelta

from django import forms
from django.contrib import admin
from django.db.models import Count, Prefetch
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from typing import Any


class CommentStatusFilter(admin.SimpleListFilter):
    WAITING        = 'Waiting'
    APPROVED       = 'Approved'
    NOT_APPROVED   = 'Not-Approved'
    title          = 'Approved, Not Approved Or Waiting Status Comments'
    parameter_name = 'status'

    def lookups(self, request: Any, model_admin):
        return [
            (CommentStatusFilter.WAITING     , 'Waiting'),
            (CommentStatusFilter.APPROVED    , 'Approved'),
            (CommentStatusFilter.NOT_APPROVED, 'Not-Approved')
        ]

    def queryset(self, request, queryset):
        if self.value() == CommentStatusFilter.WAITING:
            return queryset.filter(status=Comment.COMMENT_STATUS_WAITING)
        if self.value() == CommentStatusFilter.APPROVED:
            return queryset.filter(status=Comment.COMMENT_STATUS_APPROVED)
        if self.value() == CommentStatusFilter.NOT_APPROVED:
            return queryset.filter(status=Comment.COMMENT_STATUS_NOT_APPROVED)


class DiscountActiveFilter(admin.SimpleListFilter):
    title = 'discount active'
    parameter_name = 'discount_active'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Active'),
            ('no', 'Not Active')
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(discount_active=True)
        if self.value() == 'no':
            return queryset.filter(discount_active=False)


class QuantityFilter(admin.SimpleListFilter):
    title = 'Quantity'
    parameter_name = 'quantity'

    def lookups(self, request, model_admin):
        return (
            ('H', 'High quantity'),
            ('M', 'Medium quantity'),
            ('L', 'Low quantity')
        )

    def queryset(self, request, queryset):
        if self.value() == 'H':
            return queryset.filter(quantity__gt=10)
        if self.value() == 'M':
            return queryset.filter(quantity__gte=5, quantity__lte=10)
        if self.value() == "L":
            return queryset.filter(quantity__lt=5)


class OrderStatusFilter(admin.SimpleListFilter):
    CANCELED = 'Canceled'
    DELIVERED = 'Delivered'
    NOT_DELIVERED = 'Not Delivered'
    title = 'Canceled, Not Delivered Or Delivered Status Orders'
    parameter_name = 'status'

    def lookups(self, request: Any, model_admin):
        return [
            (OrderStatusFilter.CANCELED, 'Canceled'),
            (OrderStatusFilter.DELIVERED, 'Delivered'),
            (OrderStatusFilter.NOT_DELIVERED, 'Not Delivered')
        ]

    def queryset(self, request, queryset):
        if self.value() == OrderStatusFilter.CANCELED:
            return queryset.filter(status=Order.ORDER_STATUS_CANCELED)
        if self.value() == OrderStatusFilter.DELIVERED:
            return queryset.filter(status=Order.ORDER_STATUS_DELIVERED)
        if self.value() == OrderStatusFilter.NOT_DELIVERED:
            return queryset.filter(status=Order.ORDER_STATUS_NOT_DELIVERED)


class OrderPaidStatusFilter(admin.SimpleListFilter):
    title = 'IsPaid'
    parameter_name = 'is_paid'

    def lookups(self, request: Any, model_admin):
        return [
            ('p', 'Paid'),
            ('np', 'Not Paid'),
            ]

    def queryset(self, request, queryset):
        if self.value() == 'p':
            return queryset.filter(is_paid=True)
        if self.value() == 'np':
            return queryset.filter(is_paid=False)


class ImageInLine(admin.TabularInline):
    model  = Image
    fields = ["image", "title", "is_main", ]
    extra  = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['id', 'title', 'num_of_products', ]
    search_fields = ['title', ]

    prepopulated_fields = {
        'slug': ['title', ]
    }

    def get_queryset(self, request):
        return super().get_queryset(request) \
                      .prefetch_related('products') \
                      .annotate(num_of_products=Count('products'))
    
    @admin.display(description='# products', ordering='num_of_products')
    def num_of_products(self, category: Category):
        url = (
            reverse('admin:shop_product_changelist') 
            + '?'
            + urlencode({
                'category__id': category.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, category.num_of_products)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display        = ['id', 'title', 'category', 'num_of_products', ]
    list_select_related = ['category', ]
    autocomplete_fields = ['category', ]
    search_fields       = ['title', ]

    prepopulated_fields = {
        'slug': ['title', ]
    }

    def get_queryset(self, request):
        return super().get_queryset(request) \
                      .prefetch_related('products') \
                      .annotate(num_of_products=Count('products'))
    
    @admin.display(description='# products', ordering='num_of_products')
    def num_of_products(self, subcategory: SubCategory):
        url = (
            reverse('admin:shop_product_changelist') 
            + '?'
            + urlencode({
                'subcategory__id': subcategory.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, subcategory.num_of_products)


class SubcategoryChoiceField(forms.ModelChoiceField):
    '''if we want to show the each subcategory's category title, we should first make this class then 
       in ProductAdminForm class make a subcategory variable as below
       subcategory = SubcategoryChoiceField(queryset=SubCategory.objects.select_related('category').all())'''

    def label_from_instance(self, obj: SubCategory):
        return f"{obj.title} ({obj.category.title})"


class ProductAdminForm(forms.ModelForm):
    subcategory = SubcategoryChoiceField(queryset=SubCategory.objects.select_related('category').all(),
                                         widget=autocomplete.ModelSelect2)
    class Meta:
        model  = Product
        fields = ["title", "description", "slug", "subcategory", "in_stock", "total_sold", ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ["id", 
                     "title",
                     "image",
                     "category",
                     "product_subcategory",
                     "price",
                     "discounted_price",
                     "discount_amount",
                     "has_discount",
                     "rates_average",
                     "number_of_reviews",
                     "num_of_attributes",
                     "num_of_comments",
                     "num_of_reviews",
                     "stock_quantity", 
                     "in_stock",
                     "total_sold", ]

    list_filter   = ['datetime_created', ]
    search_fields = ['title', ]
    inlines       = [ImageInLine, ]
    form          = ProductAdminForm
    list_per_page = 20

    prepopulated_fields = {
        'slug': ['title', ]
    }

    @admin.display(description='# attributes', ordering='attributes_count')
    def num_of_attributes(self, product: Product):
        url = (
            reverse('admin:shop_productattribute_changelist') 
            + '?'
            + urlencode({
                'product__id': product.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, product.attributes_count)

    @admin.display(description='# comments', ordering='comments_count')
    def num_of_comments(self, product: Product):
        url = (
            reverse('admin:shop_comment_changelist') 
            + '?'
            + urlencode({
                'product__id': product.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, product.comments_count)

    @admin.display(description='# reviews', ordering='reviews_count')
    def num_of_reviews(self, product: Product):
        url = (
            reverse('admin:shop_productreview_changelist') 
            + '?'
            + urlencode({
                'product__id': product.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, product.reviews_count)

    @admin.display(description='subcategory', ordering='subcategory__title')
    def product_subcategory(self, product: Product):
        return product.subcategory.title
    
    def get_queryset(self, request):
        return super().get_queryset(request) \
                      .prefetch_related(Prefetch("attributes", queryset=ProductAttribute.objects.select_related("variable", "discount"))) \
                      .prefetch_related("comments") \
                      .annotate(attributes_count=Count('attributes', distinct=True), 
                                comments_count=Count('comments', distinct=True), 
                                reviews_count=Count('reviews', distinct=True)) \

    def save_model(self, request, obj: Product, form, change):
        subcategories = obj.subcategory.id
        if subcategories:
            try:
                category     = Category.objects.get(subcategories=subcategories)
                obj.category = category
            except Category.DoesNotExist:
                pass
        return super().save_model(request, obj, form, change)


class ProductAttributeAdminForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        fields = ["title", "product", "variable", "price", "quantity", "total_sold", "discount", "discount_active", ]


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    form                = ProductAttributeAdminForm
    list_display        = ["id", "title", "product", "variable", "price", "total_sold", "quantity", "discounted_price", "discount_amount", "discount_active", ]
    list_filter         = ['datetime_created', DiscountActiveFilter, QuantityFilter, ]
    autocomplete_fields = ["product", ]
    list_editable = ["price", "quantity", ]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "image", "title", "is_main", "datetime_created", "datetime_modified", ]
    list_select_related = ["product", ]
    search_fields = ["title", ]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display        = ['id', 'user', 'product', 'body', 'status', 'datetime_created', 'datetime_modified', ]
    list_filter         = [CommentStatusFilter, ]
    autocomplete_fields = ['product', ]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display        = ["id", "user", "product", "review_rating", "datetime_created", "datetime_modified", ]
    autocomplete_fields = ['product', ]


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['id', 'discount', 'description', ]
    

@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ["id", "variable_type", "title", "color_code", ]
    list_editable = ["title", "color_code", ]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', ]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["id", "wish_list", "product", ]


class ShippingMethodForm(forms.ModelForm):
    delivery_time_hours = forms.IntegerField(label="Delivery Time (Hours)", min_value=0)

    class Meta:
        model = ShippingMethod
        fields = ["shipping_method", "price", "delivery_time_hours", "shipping_method_active", ]


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ["id", "shipping_method", "price", "delivery_time", "shipping_method_active", "datetime_created", "datetime_modified", ]
    form = ShippingMethodForm

    def save_model(self, request, obj, form, change):
        hours = form.cleaned_data['delivery_time_hours']
        obj.delivery_time = timedelta(hours=hours)
        super().save_model(request, obj, form, change)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["id",
                    "user", 
                    "receiver_name", 
                    "receiver_family", 
                    "receiver_phone_number", 
                    "receiver_city", 
                    "receiver_address", 
                    "receiver_postal_code", 
                    "receiver_latitude", 
                    "receiver_longitude", 
                    "datetime_created", 
                    "datetime_modified", ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.select_related("user")


class CartItemInLine(admin.TabularInline):
    model  = CartItem
    fields = ["cart", "product", "quantity", ]
    raw_id_fields = ["product", ]
    extra  = 1

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "num_of_items", "datetime_created", "datetime_modified", ]

    @admin.display(description='# items', ordering='items_count')
    def num_of_items(self, cart: Cart):
        url = (
            reverse('admin:shop_cartitem_changelist') 
            + '?'
            + urlencode({
                'cart__id': cart.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, cart.items_count)
    
    def get_queryset(self, request):
        return super().get_queryset(request) \
                      .prefetch_related('items') \
                      .annotate(items_count=Count('items')) \


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', "quantity", ]

    def get_queryset(self, request):
        return super().get_queryset(request)\
                      .select_related("product", "cart")\
                      .select_related("product__variable")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id",
                    "num_of_items",
                    "user", 
                    "receiver_name", 
                    "receiver_family", 
                    "receiver_phone_number", 
                    "receiver_city", 
                    "receiver_address", 
                    "receiver_postal_code",
                    "receiver_latitude",
                    "receiver_longitude",
                    "status",
                    "is_paid",
                    "number",
                    "tracking_code",
                    "shipping_method",
                    "shipping_price",
                    "total_price",
                    "total_discount_amount",
                    "datetime_modified",
                    "datetime_created",
                    ]
    list_filter = [OrderPaidStatusFilter, OrderStatusFilter, ]
    search_fields = ["number", "receiver_name", "receiver_family", ]

    @admin.display(description='# items', ordering='items_count')
    def num_of_items(self, order: Order):
        url = (
            reverse('admin:shop_orderitem_changelist') 
            + '?'
            + urlencode({
                'order__id': order.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, order.items_count)
    
    def get_queryset(self, request):
        return super().get_queryset(request) \
                      .prefetch_related('items') \
                      .annotate(items_count=Count('items')) \


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "product", "quantity", "variable", "get_item_total_price", ]
