from django.urls import path
from . import views

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
]
