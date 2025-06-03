from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet, ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Prefetch
from django.http import Http404

from .filters import InStockOrderingFilter
from .filters import ProductsFilter
from .paginations import CustomPagination
from .permissions import IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly
from .models import Product,\
    ProductAttribute,\
    Category,\
    SubCategory,\
    Cart,\
    CartItem,\
    Comment,\
    ProductReview,\
    Address,\
    Order,\
    OrderItem,\
    Wishlist,\
    WishlistItem
from .serializers import\
    ProductSerializer,\
    ProductDetailSerializer,\
    CategorySerializer,\
    SubCategorySerializer,\
    CartSerializer,\
    CartItemSerializer,\
    AddCartItemSerializer,\
    ChangeCartItemSerializer,\
    CommentSerializer,\
    AddCommentSerializer,\
    ProductReviewSerializer,\
    AddProductReviewSerializer,\
    AddressSerializer,\
    OrderSerializer,\
    OrderItemSerializer,\
    WishlistSerializer,\
    WishlistCreateSerializer,\
    WishlistItemSerializer,\
    AddWishlistItemSerializer


# checked
class ProductViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = CustomPagination
    filter_backends  = [DjangoFilterBackend, InStockOrderingFilter, ] 
    filterset_class  = ProductsFilter
    ordering_fields  = ['price', 'title', 'datetime_created', 'total_sold', ]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Product.objects\
            .prefetch_related(Prefetch("attributes", queryset=ProductAttribute.objects.select_related("discount").all()))\
            .order_by("-datetime_created", "-in_stock")\
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

        return Response(data)

    def get_object_or_404(self, slug):
        try:
            return Product.objects.select_related("category", "subcategory", )\
                .prefetch_related(Prefetch("comments", queryset=Comment.objects.select_related("user")), 
                                  Prefetch("attributes", queryset=ProductAttribute.objects.select_related("variable")))\
                .get(slug=slug)
        except Product.DoesNotExist:
            raise Http404("Product not found.")


# checked
class CommentViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options", ]
    permission_classes = [IsAuthenticatedOrReadOnly, ]

    def get_queryset(self):
        queryset = Comment.objects.select_related("user").all()
        product_slug = self.kwargs["product_slug"]
        return queryset.filter(product__slug = product_slug, status=Comment.COMMENT_STATUS_APPROVED)

    def get_serializer_context(self):
        product_slug = self.kwargs["product_slug"]
        return {"slug": product_slug, "request": self.request}

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCommentSerializer
        
        return CommentSerializer


# checked
class CategoryViewSet(ReadOnlyModelViewSet):
    queryset = Category.objects.prefetch_related("products").all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'


# checked
class SubCategoryViewSet(ReadOnlyModelViewSet):
    serializer_class = SubCategorySerializer
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = SubCategory.objects.all()
        category_slug = self.kwargs.get('category__slug')

        if category_slug:
            return queryset.filter(category__slug=category_slug)

        return queryset


# checked
class AddressViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'options', 'head', ]
    permission_classes = [IsAuthenticated, ]
    serializer_class = AddressSerializer

    def get_queryset(self):
        queryset = Address.objects.all()
        user_id = self.request.user.id
        return queryset.filter(user_id=user_id)

    def get_serializer_context(self):
        user_id = self.request.user.id
        return {'user_id': user_id}


# checked
class CartViewSet(CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Cart.objects.prefetch_related(Prefetch(
        "items",
        queryset = CartItem.objects.select_related('product__variable', 'product__product').all()))\
        .all()
    serializer_class = CartSerializer

    def get_serializer_context(self):
        request = self.request
        return {'request': request}


# checked
class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'options', 'head', ]

    def get_queryset(self):
        queryset = CartItem.objects.select_related('product__variable', 'product__product').all()
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


# checked
class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'delete', 'options', 'head', ]
    permission_classes = [IsAuthenticated, ]
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.prefetch_related(Prefetch("items", OrderItem.objects.select_related("product__variable", "product__product").all())).all()
        user_id = self.request.user.id
        return queryset.filter(user_id=user_id)


# checked
class OrderItemViewSet(ModelViewSet):
    http_method_names = ['get', 'options', 'head', ]
    permission_classes = [IsAuthenticated, ]
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        order_pk = self.kwargs["order_pk"]
        user_id = self.request.user.id
        return OrderItem.objects.select_related("product__variable", "product__product").filter(order_id=order_pk, order__user_id=user_id).all()


# checked
class ProductReviewViewSet(ModelViewSet):
    http_method_names = ["get", "post", "delete", "head", "options", ]
    serializer_class = ProductReviewSerializer
    permission_classes = [IsOwnerOrReadOnly, ]

    def get_queryset(self):
        product_slug = self.kwargs["product_slug"]
        return ProductReview.objects.select_related("user").filter(product__slug = product_slug)
    
    def get_serializer_context(self):
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        product_slug = self.kwargs["product_slug"]
        context = {"slug": product_slug, "user_id": user_id}
        return context

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddProductReviewSerializer

        return ProductReviewSerializer


# checked
class WishlistViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'options', 'head', ]
    permission_classes = [IsAuthenticated, ]
    queryset = Wishlist.objects.prefetch_related(Prefetch("items", queryset=WishlistItem.objects.select_related("product").all())).all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WishlistCreateSerializer
        
        return WishlistSerializer

    def get_serializer_context(self):
        return {'user_id': self.request.user.id}


# checked
class WishlistItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'options', 'head', ]
    permission_classes = [IsAuthenticated, ]
    serializer_class = WishlistItemSerializer

    def get_serializer_context(self):
        wishlist_pk = self.kwargs['wishlist_pk']
        return {'wishlist_pk': wishlist_pk}

    def get_queryset(self):
        wishlist_pk = self.kwargs['wishlist_pk']
        return WishlistItem.objects.select_related('product').filter(wish_list_id=wishlist_pk).all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddWishlistItemSerializer

        return WishlistItemSerializer
