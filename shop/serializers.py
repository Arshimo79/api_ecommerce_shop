from rest_framework import serializers
from .models import Product, ProductAttribute, Discount, Category, SubCategory


class DiscountOfProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ["discount", ]


class ProductAttributeSerializer(serializers.ModelSerializer):
    price_after_off = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    class Meta:
        model = ProductAttribute
        fields = ['price', 'price_after_off', 'quantity', 'discount', ]

    def get_price_after_off(self, obj):
        if obj.discount_active:
            return obj.price_after_off()
        return None

    def get_discount(self, obj):
        if obj.discount_active:
            return DiscountOfProductAttributeSerializer(obj.discount).data
            # return obj.discount
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not instance.discount_active:
            representation.pop('discount', None)
            representation.pop('price_after_off', None)

        return representation


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    default_price_after_off = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['title', 'description', 'in_stock', 'slug', "price", "default_price_after_off", "discount", ]

    def get_price(self, obj):
        return obj.default_price()

    def get_discount(self, obj):
        return obj.default_off_count()

    def get_default_price_after_off(self, obj):
        return obj.default_price_after_off()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.has_default_off() == False:
            representation.pop('default_price_after_off', None)
            representation.pop('discount', None)

        return representation


class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['title', 'description', 'in_stock', ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['slug', "title", ]


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['slug', "title", "category", ]
