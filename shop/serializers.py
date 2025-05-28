from rest_framework import serializers

import re

from core.models import CustomUser

from .models import Product,\
    ProductAttribute,\
    Category,\
    SubCategory,\
    Cart,\
    CartItem,\
    Order,\
    OrderItem,\
    Wishlist,\
    WishlistItem,\
    Comment,\
    ProductReview,\
    Address,\
    ShippingMethod


class ProductAttributeSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField(read_only=True)
    discount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductAttribute
        fields = ['price', 'discounted_price', 'discount', 'quantity',  ]

    def get_discounted_price(self, obj):
        return obj.discounted_price if obj.discount_active and obj.quantity > 0 else None

    def get_discount(self, obj):
        return obj.discount_amount if obj.discount_active and obj.quantity > 0 else None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.quantity == 0:
            representation['price'] = 'This product is not in stock'

        return {key: val for key, val in representation.items() if val is not None}


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.IntegerField(read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_amount = serializers.FloatField(read_only=True)
    rates_average = serializers.SerializerMethodField()
    number_of_reviews = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id', 
                  'title', 'description', 'price', 'discounted_price', 'discount_amount', 'in_stock', 'slug', 'rates_average', 'number_of_reviews', 'has_discount', 
                 ]

    def get_rates_average(self, obj):
        return obj.rates_average

    def get_number_of_reviews(self, obj):
        return obj.number_of_reviews

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.has_discount == False:
            representation.pop('has_discount', None)
            representation.pop('discount_amount', None)
            representation.pop('discounted_price', None)

        return representation


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username")
    class Meta:
        model = Comment
        fields = ["id", "user_name", "body", ]


class AddCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "body", ]

    def create(self, validated_data):
        request = self.context.get("request")
        slug = self.context.get("slug")
        user = request.user

        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise serializers.ValidationError({
                'product': "Product not found."
            })

        return Comment.objects.create(user=user, product=product, **validated_data)


class ProductAttributeInProductDetailSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField(read_only=True)
    discount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductAttribute
        fields = ['id', 'price', 'discounted_price', 'discount', 'quantity', 'discount_active', ]

    def get_discounted_price(self, obj):
        return obj.discounted_price if obj.discount_active and obj.quantity > 0 else None

    def get_discount(self, obj):
        return obj.discount_amount if obj.discount_active and obj.quantity > 0 else None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.quantity == 0:
            representation['price'] = 'This product is not in stock'

        if instance.discount_active == False:
            representation.pop('discounted_price')
            representation.pop('discount')

        if instance.variable.varaible_type == 'size':
            representation['size'] = instance.variable.title
        else:
            representation['color'] = instance.variable.title

        return {key: val for key, val in representation.items() if val is not None}


class ProductDetailSerializer(serializers.ModelSerializer):
    attributes = ProductAttributeInProductDetailSerializer(many=True)
    rates_average = serializers.SerializerMethodField()
    number_of_reviews = serializers.SerializerMethodField()
    default_attribute = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'in_stock', 'rates_average', 'number_of_reviews', 'default_attribute', 'attributes', ]

    def get_rates_average(self, obj:Product):
        return obj.rates_average

    def get_number_of_reviews(self, obj):
        return obj.number_of_reviews
    
    def get_default_attribute(self, obj):
        default_attribute = obj.default_attribute()
        return ProductAttributeInProductDetailSerializer(default_attribute).data


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
    class Meta:
        model = ProductAttribute
        fields = ['title', 'final_price', ]

    def get_final_price(self, obj):
        if obj.discount_active:
            return obj.discounted_price
        return obj.price
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.variable.varaible_type == 'size':
            representation['size'] = instance.variable.title
        else:
            representation['color'] = instance.variable.title

        return {key: val for key, val in representation.items() if val is not None}


class ChangeCartItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField()
    class Meta:
        model = CartItem
        fields = ['quantity']

    def validate_quantity(self, value):
        cart_item = self.instance
        
        try:
            product = cart_item.product
        except ProductAttribute.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        
        if value > product.quantity:
            raise serializers.ValidationError(f"The maximum stock of this product is {product.quantity} pieces.")
        
        if value < 1:
            raise serializers.ValidationError("The minimum value must be 1")
        
        return value


class AddCartItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=ProductAttribute.objects.all())
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        product = data['product']
        requested_quantity = data['quantity']

        if requested_quantity > product.quantity:
            raise serializers.ValidationError({
                'quantity': f"Only {product.quantity} of this product are in stock."
            })

        return data

    def create(self, validated_data):
        cart_id = self.context['cart_pk']
        product = validated_data['product']
        quantity = validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product.id)
            total_quantity = cart_item.quantity + quantity
            if total_quantity > product.quantity:
                raise serializers.ValidationError({
                    'quantity': f"The total quantity of this product is more than the quantity in stock. ({product.quantity - cart_item.quantity}) more can be ordered."
                })
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart_id=cart_id, product_id=product.id, quantity=quantity)

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
    total_discount = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ['id', "items", "total_price", "total_discount", "total_items"]
        read_only_fields = ["id", ]

    def get_total_items(self, obj):
        count = 0
        for i in obj.items.all():
            count += 1

        return count

    def get_total_discount(self, obj):
        cart_total_dicount = []

        for item in obj.items.all():
            if item.product.discount_active:
                cart_total_dicount.append((item.product.price - item.product.discounted_price) * item.quantity)

        return sum(cart_total_dicount)

    def get_total_price(self, cart: Cart):
        return sum([item.quantity * item.product.discounted_price\
                    if item.product.discount_active\
                    else item.quantity * item.product.price\
                    for item in cart.items.all()])


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 
                  'receiver_name', 
                  'receiver_family', 
                  'receiver_phone_number', 
                  'receiver_city', 
                  'receiver_address', 
                  'receiver_postal_code', 
                  'receiver_latitude', 
                  'receiver_longitude', ]
        read_only_fields = ["id", ]

    def validate_receiver_phone_number(self, value):
        if not re.match(r'^09\d{9}$', value):
            raise serializers.ValidationError("put your number as following example: 09123456789")
        return value

    def create(self, validated_data):
        user_id = self.context['user_id']

        return Address.objects.create(user_id=user_id, **validated_data)


class OrderItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['id', 'title', ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.variable.varaible_type == 'size':
            representation['size'] = instance.variable.title
        else:
            representation['color'] = instance.variable.title

        return {key: val for key, val in representation.items() if val is not None}


class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderItemProductSerializer()
    item_total_price = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'item_total_price', ]

    def get_item_total_price(self, obj):
        return obj.get_item_total_price()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.discount_active:
            representation['discounted_price'] = instance.discounted_price
            representation['discount'] = instance.discount

        return {key: val for key, val in representation.items() if val is not None}


class ShippingMethodInOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ["id", "shipping_method", ]


class OrderSerializer(serializers.ModelSerializer):
    shipping_method = ShippingMethodInOrderSerializer()
    items = OrderItemSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = ['id',
                  'receiver_name',
                  'receiver_family',
                  'receiver_phone_number',
                  'receiver_city',
                  'receiver_address',
                  'receiver_postal_code',
                  'status',
                  'is_paid',
                  'tracking_code',
                  'shipping_method',
                  'shipping_price',
                  'total_price',
                  'total_discount_amount',
                  'items'
                  ]

    def get_status(self, obj):
        return obj.get_status_display()


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    class Meta:
        model = WishlistItem
        fields = ["id", "product", ]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True)
    class Meta:
        model = Wishlist
        fields = ["id", "items", ]


class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ["id", ]

    def create(self, validated_data):
        user_id = self.context["user_id"]

        try:
            wish_list = Wishlist.objects.get(user_id=user_id)
            raise serializers.ValidationError('You already have a wish list.')
        except Wishlist.DoesNotExist:
            wish_list = Wishlist.objects.create(user_id=user_id, **validated_data)

        self.instance = wish_list
        return wish_list


class AddWishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['id', 'product', ]

    def create(self, validated_data):
        wishlist_id = self.context["wishlist_pk"]
        product = validated_data.get('product')

        try:
            wishlist_item = WishlistItem.objects.get(wish_list_id=wishlist_id, product_id=product.id)
            raise serializers.ValidationError("This Product is in your wish list.")
        except WishlistItem.DoesNotExist:
            wishlist_item = WishlistItem.objects.create(wish_list_id=wishlist_id, **validated_data)

        self.instance = wishlist_item
        return wishlist_item


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username")
    
    class Meta:
        model = ProductReview
        fields = ["id", "user_name", "review_rating", ]


class AddProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ["id", "review_rating", ]

    def create(self, validated_data):
        user_id = self.context["user_id"]
        slug = self.context["slug"]
        user = CustomUser.objects.get(id=user_id)
        orders = Order.objects.filter(user=user).all()
        titles = []
        for order in orders:
            product_titles = OrderItem.objects\
                .select_related("product")\
                .filter(order=order)\
                .values_list('product__title', flat=True).distinct()
            for title in product_titles:
                titles.append(title)

        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise serializers.ValidationError("There is no product with this id.")

        if product.title not in list(set(titles)):
            raise serializers.ValidationError("You must first purchase this product")

        try:
            review = ProductReview.objects.get(product=product, user_id=user_id)
            raise serializers.ValidationError("You have already rated this product")
        except ProductReview.DoesNotExist:
            review = ProductReview.objects.create(product=product, user_id=user_id, **validated_data)

        self.instance = review
        return review
