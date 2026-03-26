from django.urls import path, re_path, include
from . import views

handler404 = 'templates.error_handlers.custom_404'
handler500 = 'templates.error_handlers.custom_500'
handler403 = 'templates.error_handlers.custom_403'
handler400 = 'templates.error_handlers.custom_400'


app_name = 'store'

urlpatterns = [
    # ============================================
    # HOME
    # ============================================
    path('', views.home, name='home'),

    # ============================================
    # PRODUCTS
    # ============================================
    path('products/', views.products, name='products'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # ============================================
    # CART
    # ============================================
    path('cart/', views.cart, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),

    # ============================================
    # CHECKOUT
    # ============================================
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/place-order/', views.place_order, name='place_order'),

    # ============================================
    # ORDERS
    # ============================================
    path('orders/', views.orders, name='orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),

    # ============================================
    # WISHLIST
    # ============================================
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),

    # ============================================
    # MERCHANT
    # ============================================
    path('merchant/dashboard/', views.merchant_dashboard, name='merchant_dashboard'),
    path('merchant/products/', views.merchant_products, name='merchant_products'),
    path('merchant/products/add/', views.product_create, name='product_create'),
    path('merchant/products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('merchant/products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('merchant/orders/', views.merchant_orders, name='merchant_orders'),

    # ============================================
    # AUTH (Accounts)
    # ============================================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),

]

urlpatterns += [
    path('error/<int:error_code>/', views.error_view, name='error_page'),
    re_path(r'^.*$', views.handler404_view),  # ← يلتقط أي URL غير موجود
]