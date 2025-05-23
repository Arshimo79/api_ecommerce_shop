from rest_framework.filters import OrderingFilter
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet, ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Prefetch
from django.http import Http404

from .filters import ProductsFilter
from .paginations import CustomPagination
from .permissions import IsAuthenticatedOrReadOnly
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
    ProductReview
from .serializers import\
    ProductSerializer,\
    ProductAttributeSerializer,\
    ProductDetailSerializer,\
    CategorySerializer,\
    SubCategorySerializer,\
    CartSerializer,\
    CartItemSerializer,\
    AddCartItemSerializer,\
    ChangeCartItemSerializer,\
    OrderSerializer,\
    OrderCreateSerializer,\
    OrderUpdateSerializer,\
    WishlistSerializer,\
    WishlistItemSerializer,\
    AddWishlistItemSerializer,\
    WishlistCreateSerializer,\
    CommentSerializer,\
    AddCommentSerializer,\
    ProductReviewSerializer


class ProductViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = CustomPagination
    filter_backends  = [DjangoFilterBackend, OrderingFilter] 
    filterset_class  = ProductsFilter
    ordering_fields  = ['price', 'title', 'datetime_created', ]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Product.objects\
            .prefetch_related(Prefetch("attributes", queryset=ProductAttribute.objects.select_related("discount").all()))\
            .order_by("-datetime_created")\
            .filter(in_stock=True)\
            .custom_query()\
            .all()\

        category_slug = self.kwargs.get('category__slug')
        subcategory_slug = self.kwargs.get('subcategory__slug')

        if category_slug and subcategory_slug:
            return queryset.filter(category__slug=category_slug, subcategory__slug=subcategory_slug)
        if category_slug or subcategory_slug:
            return queryset.filter(Q(category__slug=category_slug) | Q(subcategory__slug=subcategory_slug))

        return queryset

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object_or_404(kwargs.get("slug"))
        
        data = ProductDetailSerializer(product).data

        data.update(self.get_variable_data(request, product))

        return Response(data)

    def get_object_or_404(self, slug):
        try:
            return Product.objects.select_related("category", "subcategory")\
                .prefetch_related(Prefetch("comments", queryset=Comment.objects.select_related("user")))\
                .custom_query()\
                .get(slug=slug)
        except Product.DoesNotExist:
            raise Http404("Product not found.")

    def get_variable_data(self, request, product):
        variables = product.variables()
        default_variable = product.default_variable()
        data = {
            "variables": list(variables),
            "default_variable": default_variable.variable.title,
            "default_product_attr": ProductAttributeSerializer(default_variable).data,
        }

        selected = request.query_params.get("variable")
        if selected:
            try:
                attr = ProductAttribute.objects.select_related("variable", "product", "discount")\
                        .get(variable__title=selected, product=product)
                data.update({
                    "selected_variable": selected,
                    "product_attr": ProductAttributeSerializer(attr).data,
                })
                data.pop("default_variable", None)
                data.pop("default_product_attr", None)
            except ProductAttribute.DoesNotExist:
                raise Http404("Product not found")
        return data


class CommentViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options", "delete"]
    permission_classes = [IsAuthenticatedOrReadOnly, ]

    def get_queryset(self):
        queryset = Comment.objects.select_related("user").all()
        product_slug = self.kwargs["product_slug"]
        return queryset.filter(product__slug = product_slug)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCommentSerializer
        
        return CommentSerializer
    
    def get_serializer_context(self):
        user_id = self.request.user.id
        product_slug = self.kwargs["product_slug"]
        context = {"slug": product_slug, "user_id": user_id}
        return context


class CategoryViewSet(ReadOnlyModelViewSet):
    queryset = Category.objects.prefetch_related("products").all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'


class SubCategoryViewSet(ReadOnlyModelViewSet):
    serializer_class = SubCategorySerializer
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = SubCategory.objects.all()
        category_slug = self.kwargs.get('category__slug')

        if category_slug:
            return queryset.filter(category__slug=category_slug)

        return queryset


class CartViewSet(CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Cart.objects.prefetch_related(Prefetch(
        "items",
        queryset = CartItem.objects.select_related('product__variable').all(),
        )).all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        queryset = CartItem.objects.select_related('product__variable').all()
        cart_pk = self.kwargs['cart_pk']
        return queryset.filter(cart_id=cart_pk)

    def get_serializer_context(self):
        cart_pk = self.kwargs['cart_pk']
        return {'cart_pk': cart_pk}

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        if self.request.method == "PATCH":
            return ChangeCartItemSerializer
        return CartItemSerializer


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'options', 'head']

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Order.objects.select_related("user").prefetch_related(Prefetch(
        "items",
        OrderItem.objects.select_related("product__variable").all(),
        )).all()
    
        user = self.request.user

        if user.is_staff:
            return queryset

        return queryset.filter(user_id=user.id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        if self.request.method == "PATCH":
            return OrderUpdateSerializer

        return OrderSerializer
    
    def get_serializer_context(self):
        return {'user_id': self.request.user.id}

    def create(self, request, *args, **kwargs):
        create_order_serializer = OrderCreateSerializer(
            data = request.data,
            context = {'user_id': self.request.user.id},
            )
        create_order_serializer.is_valid(raise_exception=True)
        created_order = create_order_serializer.save()

        serializer = OrderSerializer(created_order)
        return Response(serializer.data)


class WishlistViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'options', 'head']
    permission_classes = [IsAuthenticated, ]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WishlistCreateSerializer
        
        return WishlistSerializer

    def get_serializer_context(self):
        return {'user_id': self.request.user.id}

    def get_queryset(self):
        queryset = Wishlist.objects.select_related("user").prefetch_related(Prefetch(
        "items",
        WishlistItem.objects.select_related("product").prefetch_related('product__attributes').all(),
        )).all()
    
        user = self.request.user

        if user.is_staff:
            return queryset

        return queryset.filter(user_id=user.id)


class WishlistItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'options', 'head']
    permission_classes = [IsAuthenticated, ]
    serializer_class = WishlistItemSerializer

    def get_serializer_context(self):
        wishlist_pk = self.kwargs['wishlist_pk']
        return {'wishlist_pk': wishlist_pk}

    def get_queryset(self):
        queryset = WishlistItem.objects.select_related("product").prefetch_related('product__attributes').all()
        wishlist_pk = self.kwargs['wishlist_pk']
        return queryset.filter(wish_list_id=wishlist_pk)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddWishlistItemSerializer

        return WishlistItemSerializer


class ProductReviewViewSet(ModelViewSet):
    http_method_names = ["post", "head", "options", "delete"]
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    serializer_class = ProductReviewSerializer

    def get_queryset(self):
        queryset = ProductReview.objects.all()
        product_slug = self.kwargs["product_slug"]
        return queryset.filter(product__slug = product_slug)
    
    def get_serializer_context(self):
        user_id = self.request.user.id
        product_slug = self.kwargs["product_slug"]
        context = {"slug": product_slug, "user_id": user_id}
        return context
