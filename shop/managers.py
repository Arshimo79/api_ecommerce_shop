from django.db import models
from django.db.models import (
    OuterRef, Subquery, Count, Avg, Value, Case, When,
    IntegerField, FloatField, BooleanField
)
from django.db.models.functions import Coalesce, Cast


class ProductQuerySet(models.QuerySet):
    def custom_query(self):
        from .models import ProductAttribute

        discounted_attrs = ProductAttribute.objects.filter(
            product=OuterRef('pk'),
            quantity__gt=0,
            discount_active=True,
            discounted_price__isnull=False
        ).order_by('discounted_price')

        normal_attrs = ProductAttribute.objects.filter(
            product=OuterRef('pk'),
            quantity__gt=0,
            discount_active=False
        ).order_by('price')

        return self.annotate(
            annotated_number_of_reviews=Count('reviews'),

            annotated_rates_average=Avg(
                Cast('reviews__review_rating', FloatField())
            ),

            annotated_price=Coalesce(
                Subquery(discounted_attrs.values('price')[:1]),
                Subquery(normal_attrs.values('price')[:1])
            ),

            annotated_discounted_price=Subquery(
                discounted_attrs.values('discounted_price')[:1]
            ),

            annotated_discount_amount=Coalesce(
                Subquery(discounted_attrs.values('discount_amount')[:1]),
                Value(0.00),
                output_field=IntegerField()
            ),

            annotated_has_discount=Case(
                When(annotated_discounted_price__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def custom_query(self):
        return self.get_queryset().custom_query()
