from django.urls import path, include

from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('subcategories', views.SubCategoryViewSet, basename='subcategory')
router.register('carts', views.CartViewSet, basename="cart")
router.register('orders', views.OrderViewSet, basename='order')
router.register('wishlists', views.WishlistViewSet, basename='wishlist')

category_router = routers.NestedDefaultRouter(router, 'categories', lookup="category")
category_router.register('products', views.ProductViewSet, basename='category-products')
category_router.register('subcategories', views.SubCategoryViewSet, basename='category-subcategories')

subcategory_products_router = routers.NestedDefaultRouter(category_router, 'subcategories', lookup='subcategory')
subcategory_products_router.register('products', views.ProductViewSet, basename='subcategory-products')

subcategory_router = routers.NestedDefaultRouter(router, 'subcategories', lookup="subcategory")
subcategory_router.register('products', views.ProductViewSet, basename='subcategory-products')

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup="cart")
cart_router.register('items', views.CartItemViewSet, basename='cart-items')

wishlist_router = routers.NestedDefaultRouter(router, 'wishlists', lookup="wishlist")
wishlist_router.register("items", views.WishlistItemViewSet, basename="wishlist-items")

urlpatterns = [
    path('', include(router.urls)),
    path('', include(category_router.urls)),
    path('', include(subcategory_router.urls)),
    path('', include(subcategory_products_router.urls)),
    path('', include(cart_router.urls)),
    path('', include(wishlist_router.urls)),
]
