from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet, ModelViewSet
from rest_framework.mixins   import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin

from django.db.models import Q, Prefetch

from .models import Product, ProductAttribute, Category, SubCategory, Cart, CartItem
from .serializers import\
    ProductSerializer,\
    ProductAttributeSerializer,\
    ProductDetailSerializer,\
    CategorySerializer,\
    SubCategorySerializer,\
    CartSerializer,\
    CartItemSerializer,\
    AddCartItemSerializer,\
    ChangeCartItemSerializer


class ProductViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Product.objects.prefetch_related(Prefetch("attributes", queryset=ProductAttribute.objects.select_related("discount").all())).order_by("-datetime_created").all()
        category_slug = self.kwargs.get('category__slug')
        subcategory_slug = self.kwargs.get('subcategory__slug')

        if category_slug and subcategory_slug:
            return queryset.filter(category__slug=category_slug, subcategory__slug=subcategory_slug)
        if category_slug or subcategory_slug:
            return queryset.filter(Q(category__slug=category_slug) | Q(subcategory__slug=subcategory_slug))

        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            slug = kwargs.get("slug")
            product = Product.objects.select_related("category", "subcategory").get(slug=slug)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        data = ProductDetailSerializer(product).data

        variables = product.variables()
        default_variable = product.default_variable()
        related_products = Product.objects.filter(subcategory=product.subcategory)\
            .prefetch_related(Prefetch("attributes", queryset=ProductAttribute.objects.select_related("discount").all()))\
            .order_by("-datetime_created")\
            .all()\
            .exclude(slug=product.slug)

        data.update({
            "variables": list(variables),
            "default_variable": variables.first(),
            "default_product_attr": ProductAttributeSerializer(default_variable).data,
        })

        get_variable = request.query_params.get('variable')
        if get_variable:
            try:
                selected_product = ProductAttribute.objects.select_related("variable", "product", "discount")\
                .get(variable__title=get_variable, product=product)
            except ProductAttribute.DoesNotExist:
                return Response({"error": "Product not found"}, status=404)
            
            data.pop("default_variable", None)
            data["selected_variable"] = get_variable
            data.pop("default_product_attr", None)
            data["product_attr"] = ProductAttributeSerializer(selected_product).data

        related_products = [ProductSerializer(p).data for p in related_products]
        data["related_products"] = related_products

        return Response(data)


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
