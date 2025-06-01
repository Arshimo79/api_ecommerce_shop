from django.urls import path, include

from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('subcategories', views.SubCategoryViewSet, basename='subcategory')
router.register('carts', views.CartViewSet, basename="cart")
router.register('orders', views.OrderViewSet, basename='order')
router.register('addresses', views.AddressViewSet, basename='address')

product_router = routers.NestedDefaultRouter(router, "products", lookup="product")
product_router.register("comments", views.CommentViewSet, basename="product-comments")
product_router.register("reviews", views.ProductReviewViewSet, basename="product-reviews")

category_router = routers.NestedDefaultRouter(router, 'categories', lookup="category")
category_router.register('products', views.ProductViewSet, basename='category-products')
category_router.register('subcategories', views.SubCategoryViewSet, basename='category-subcategories')

subcategory_products_router = routers.NestedDefaultRouter(category_router, 'subcategories', lookup='subcategory')
subcategory_products_router.register('products', views.ProductViewSet, basename='subcategory-products')

subcategory_router = routers.NestedDefaultRouter(router, 'subcategories', lookup="subcategory")
subcategory_router.register('products', views.ProductViewSet, basename='subcategory-products')

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup="cart")
cart_router.register('items', views.CartItemViewSet, basename='cart-items')

order_router = routers.NestedDefaultRouter(router, 'orders', lookup="order")
order_router.register('items', views.OrderItemViewSet, basename='order-items')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(product_router.urls)),
    path('', include(category_router.urls)),
    path('', include(subcategory_router.urls)),
    path('', include(subcategory_products_router.urls)),
    path('', include(cart_router.urls)),
    path('', include(order_router.urls))
]
