from django.urls import path, include

from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('subcategories', views.SubCategoryViewSet, basename='subcategory')

category_router = routers.NestedDefaultRouter(router, 'categories', lookup="category")
category_router.register('products', views.ProductViewSet, basename='category-products')
category_router.register('subcategories', views.SubCategoryViewSet, basename='category-subcategories')

subcategory_products_router = routers.NestedDefaultRouter(category_router, 'subcategories', lookup='subcategory')
subcategory_products_router.register('products', views.ProductViewSet, basename='subcategory-products')

subcategory_router = routers.NestedDefaultRouter(router, 'subcategories', lookup="subcategory")
subcategory_router.register('products', views.ProductViewSet, basename='subcategory-products')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(category_router.urls)),
    path('', include(subcategory_router.urls)),
    path('', include(subcategory_products_router.urls)),
]
