from django            import forms
from django.contrib    import admin
from django.db.models  import Count
from django.urls       import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from dal import autocomplete

from typing import Any

from .models import *


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


class ProductAttributeInLine(admin.TabularInline):
    model  = ProductAttribute
    fields = ["variable", "price", "quantity", "discount_active", "discount", ]
    extra  = 1


class ProductReviewInLine(admin.TabularInline):
    model  = ProductReview
    fields = ["review_rating", "user", ]
    extra  = 1


class SubCategoryInLine(admin.TabularInline):
    model  = SubCategory
    fields = ['id', 'title', ]
    extra  = 1


class CommentInLine(admin.TabularInline):
    model  = Comment
    fields = ['id', 'user', 'body', "status", ]
    extra  = 1


class WishlistItemInLine(admin.TabularInline):
    model  = WishlistItem
    fields = ["id", "product", ]
    extra  = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['id', 'title', 'num_of_products', ]
    inlines       = [SubCategoryInLine, ]
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
        fields = ["title", "description", "slug", "subcategory", "in_stock", ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ["id", 
                     "title",
                     "category",
                     "product_subcategory", 
                     "num_of_attributes",
                    #  "num_of_comments",
                     "stock_quantity", ]

    list_filter   = ['datetime_created', ]
    inlines       = [ProductAttributeInLine, CommentInLine, ProductReviewInLine, ]
    search_fields = ['name', ]
    form          = ProductAdminForm
    list_per_page = 20

    prepopulated_fields = {
        'slug': ['title', ]
    }
    
    # @admin.display(description='# comments', ordering='comments_count')
    # def num_of_comments(self, product: Product):
    #     url = (
    #         reverse('admin:products_comment_changelist') 
    #         + '?'
    #         + urlencode({
    #             'product__id': product.id,
    #         })
    #     )
    #     return format_html('<a href="{}">{}</a>', url, product.comments_count)
    
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

    @admin.display(description='subcategory', ordering='subcategory__title')
    def product_subcategory(self, product: Product):
        return product.subcategory.title
    
    def get_queryset(self, request):
        return super().get_queryset(request) \
                      .prefetch_related('attributes') \
                      .annotate(attributes_count=Count('attributes')) \
    
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
        fields = ["product", "variable", "price", "quantity", "discount", "discount_active", ]


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    form                = ProductAttributeAdminForm
    list_display        = ["id", "title", "product", "variable", "price", "discounted_price", "quantity", "discount_active", ]
    list_filter         = ['datetime_created', ]
    autocomplete_fields = ["product", ]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display        = ['id', 'user', 'product', 'body', 'status', ]
    list_filter         = [CommentStatusFilter, ]
    autocomplete_fields = ['product', ]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display        = ["id", "user", "product", "review_rating", ]
    autocomplete_fields = ['product', ]


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['id', 'discount', 'description', ]
    

@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ["id", "varaible_type", "title", "color_code", ]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', ]
    inlines = [WishlistItemInLine, ]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["id", "wish_list", "product", ]


class CartItemInLine(admin.TabularInline):
    model  = CartItem
    fields = ["cart", "product", "quantity", ]
    extra  = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "is_paid", "datetime_created", "datetime_modified", ]
    inlines = [CartItemInLine, ]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', "quantity", ]


class OrderItemInLine(admin.TabularInline):
    model  = OrderItem
    fields = ["order", "product", "variant", "price", "quantity", ] 
    extra  = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["user", "first_name", "last_name", "email", "phone_number", "address", "order_notes", "is_paid", "status", ]

    inlines = [
        OrderItemInLine,
    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "product", "quantity", "variant", ]
