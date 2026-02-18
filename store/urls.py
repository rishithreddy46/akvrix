from django.urls import path
from . import views, admin_views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    # Auth pages
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('logout/', views.logout_view, name='logout'),
    # Protected pages (login required)
    path('cart/', views.cart_page, name='cart'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('wishlist/', views.wishlist_page, name='wishlist'),
    path('account/', views.account_page, name='account'),
    path('my-orders/', views.my_orders_page, name='my_orders'),
    path('order/<str:order_number>/', views.order_detail_page, name='order_detail_page'),
    # Profile & Password APIs
    path('api/profile/update/', views.update_profile, name='update_profile'),
    path('api/password/change/', views.change_password, name='change_password'),
    # Cart & Wishlist APIs
    path('api/cart/add/', views.add_to_cart, name='add_to_cart'),
    path('api/cart/update/', views.update_cart, name='update_cart'),
    path('api/wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('api/order/place/', views.place_order, name='place_order'),
    # Admin Dashboard
    path('dashboard/login/', admin_views.admin_login, name='admin_login'),
    path('dashboard/logout/', admin_views.admin_logout, name='admin_logout'),
    path('dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/products/', admin_views.admin_products, name='admin_products'),
    path('dashboard/products/add/', admin_views.admin_product_edit, name='admin_product_add'),
    path('dashboard/products/<int:product_id>/edit/', admin_views.admin_product_edit, name='admin_product_edit'),
    path('dashboard/products/<int:product_id>/delete/', admin_views.admin_product_delete, name='admin_product_delete'),
    path('dashboard/orders/', admin_views.admin_orders, name='admin_orders'),
    path('dashboard/orders/<int:order_id>/', admin_views.admin_order_detail, name='admin_order_detail'),
    path('dashboard/reviews/', admin_views.admin_reviews, name='admin_reviews'),
    path('dashboard/reviews/<int:review_id>/edit/', admin_views.admin_review_edit, name='admin_review_edit'),
    path('dashboard/reviews/<int:review_id>/delete/', admin_views.admin_review_delete, name='admin_review_delete'),
    path('dashboard/customers/', admin_views.admin_customers, name='admin_customers'),
    # Review API
    path('api/review/<slug:slug>/', views.submit_review, name='submit_review'),
    # Address APIs
    path('api/addresses/', views.address_list, name='address_list'),
    path('api/address/save/', views.address_save, name='address_save'),
    path('api/address/<int:address_id>/delete/', views.address_delete, name='address_delete'),
    path('api/address/<int:address_id>/default/', views.address_set_default, name='address_set_default'),
]
