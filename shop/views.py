from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from django.db.models import Q

from .models import Product, ProductAttribute, Category, SubCategory
from .serializers import \
    ProductSerializer,\
    ProductAttributeSerializer, \
    ProductDetailSerializer, \
    CategorySerializer, \
    SubCategorySerializer


class ProductViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Product.objects.prefetch_related("attributes").order_by("-datetime_created").all()
        category_slug = self.kwargs.get('category__slug')
        subcategory_slug = self.kwargs.get('subcategory__slug')

        if category_slug and subcategory_slug:
            return queryset.filter(category__slug=category_slug, subcategory__slug=subcategory_slug)
        if category_slug or subcategory_slug:
            return queryset.filter(Q(category__slug=category_slug) | Q(subcategory__slug=subcategory_slug))

        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            product = self.get_object()
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        data = ProductDetailSerializer(product).data

        variables = product.variables()
        default_variable = product.default_variable()
        related_products = Product.objects.filter(subcategory=product.subcategory).exclude(slug=product.slug)

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
