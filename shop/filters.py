from django_filters.rest_framework import FilterSet, CharFilter
from rest_framework.filters import OrderingFilter

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


class InStockOrderingFilter(OrderingFilter):
    def remove_in_stock_from_ordering(self, ordering):
        if ordering:
            ordering = [field for field in ordering if field not in ['in_stock', '-in_stock']]
        return ordering

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)

        if not ordering:
            return ['-in_stock']

        ordering = self.remove_in_stock_from_ordering(ordering)

        return ['-in_stock'] + ordering
