from rest_framework import serializers
from .models import Product, ProductAttribute, Category, SubCategory, Cart, CartItem


class ProductAttributeSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    class Meta:
        model = ProductAttribute
        fields = ['price', 'discounted_price', 'quantity', 'discount', ]

    def get_discounted_price(self, obj):
        if obj.discount_active:
            return obj.discounted_price
        return None

    def get_discount(self, obj):
        if obj.discount_active:
            return obj.discount_amount
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not instance.discount_active:
            representation.pop('discount', None)
            representation.pop('discounted_price', None)

        return representation


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['title', 'description', 'in_stock', 'slug', "price", "discounted_price", "discount", ]

    def get_price(self, obj):
        return obj.default_price()

    def get_discount(self, obj):
        return obj.default_off_count()

    def get_discounted_price(self, obj):
        return obj.default_discounted_price()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.has_default_off() == False:
            representation.pop('discounted_price', None)
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


class CartProductSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()
    variable = serializers.SerializerMethodField()
    class Meta:
        model = ProductAttribute
        fields = ['title', 'variable', 'final_price', ]

    def get_final_price(self, obj):
        if obj.discount_active:
            return obj.discounted_price
        return obj.price

    def get_variable(self, obj):
        return obj.variable.title


class ChangeCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', ]

    def create(self, validated_data):
        cart_id = self.context["cart_pk"]
        product = validated_data.get('product')
        quantity = validated_data.get('quantity')

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product.id)
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart_id=cart_id, **validated_data)

        self.instance = cart_item
        return cart_item


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    item_total_price = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'item_total_price', ]

    def get_item_total_price(self, obj: CartItem):
        if obj.product.discount_active:
            return obj.product.discounted_price * obj.quantity
        return obj.product.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ['id', "items", "total_price"]
        read_only_fields = ["id", ]

    def get_total_price(self, cart: Cart):
        return sum([item.quantity * item.product.discounted_price\
                    if item.product.discount_active\
                    else item.quantity * item.product.price\
                    for item in cart.items.all()])
