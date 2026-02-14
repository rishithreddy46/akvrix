from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_page, name='cart'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('account/', views.account_page, name='account'),
    # API
    path('api/cart/add/', views.add_to_cart, name='add_to_cart'),
    path('api/cart/update/', views.update_cart, name='update_cart'),
    path('api/wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('api/order/place/', views.place_order, name='place_order'),
]
