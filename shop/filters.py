from django_filters.rest_framework import FilterSet, CharFilter

from .models import Product


class ProductsFilter(FilterSet):
    title = CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label=''
    )

    class Meta:
        model = Product
        fields = ['title', ]
