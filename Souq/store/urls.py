from django.urls import path, re_path, include
from . import views
from accounts.views import send_invoice
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
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('brand/<slug:slug>/', views.brand_detail, name='brand_detail'),
    path('product/copy/<int:pk>/', views.product_copy, name='product_copy'),
    path('upload-video/', views.upload_video, name='upload_video'),
    path('delete-product-image/<int:pk>/', views.delete_product_image, name='delete_product_image'),
    path('delete-product-video/<int:pk>/', views.delete_product_video, name='delete_product_video'),
    # ============================================
    # ATTRIBUTES API (للمواصفات)
    # ============================================

    # ============================================
    # CART
    # ============================================
    path('cart/', views.cart, name='cart'),
    path('cart/count/', views.cart_count, name='cart_count'),
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
    path('track-order/', views.track_order, name='track_order'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/send-invoice/', send_invoice, name='send_invoice'),
    path('orders/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),

    # ============================================
    # WISHLIST
    # ============================================
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/count/', views.wishlist_count, name='wishlist_count'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/update/', views.update_wishlist, name='update_wishlist'),
    path('wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # ============================================
    # MERCHANT
    # ============================================
    path('merchant/dashboard/', views.merchant_dashboard, name='merchant_dashboard'),
    path('merchant/products/', views.merchant_products, name='merchant_products'),
    path('merchant/products/add/', views.product_create, name='product_create'),
    path('merchant/products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('merchant/products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('merchant/orders/', views.merchant_orders, name='merchant_orders'),
    # في urls.py داخل مسارات التاجر
    path('merchant/orders/<int:pk>/', views.merchant_order_detail, name='merchant_order_detail'),
    path('merchant/orders/<int:pk>/update-status/', views.merchant_update_order_status, name='merchant_update_order_status'),

    # مسارات لوحة تحكم الأدمن
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin-panel/user/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/product/<int:product_id>/delete/', views.admin_delete_product, name='admin_delete_product'),

]  
urlpatterns += [
    path('error/<int:error_code>/', views.error_view, name='error_page'),
]   