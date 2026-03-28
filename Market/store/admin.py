from django.contrib import admin
from .models import (
    AttributeValue, ProductVariant, Profile, Category, Product, ProductImage,
    Cart, CartItem, Order, OrderItem,
    Wishlist, Review, Attribute
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_seller', 'phone', 'wilaya', 'baladia', 'store_name')
    list_filter = ('is_seller', 'wilaya', 'baladia')
    search_fields = ('user__username', 'phone', 'store_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'products_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller']
    list_display = ('name', 'category', 'seller', 'price', 'old_price', 'discount', 'stock', 'is_active', 'is_featured')
    list_filter = ('category', 'is_active', 'is_featured', 'brand')
    search_fields = ('name', 'description', 'sku')
    readonly_fields = ('rating', 'reviews_count', 'sold_count', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.profile.is_seller:
            return qs.filter(seller=request.user)
        return qs
    def save_model(self, request, obj, form, change):
        if not obj.seller:
            obj.seller = request.user.profile  # 🔥 هنا الحل
        super().save_model(request, obj, form, change) 



@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'is_main')
    search_fields = ('product__name',)

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'price', 'stock')
    search_fields = ('product__name', 'sku')

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value')
    search_fields = ('attribute__name', 'value')



class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'items_count', 'total', 'created_at', 'updated_at')
    search_fields = ('user__username', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'subtotal')
    search_fields = ('cart__user__username', 'product__name')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_price', 'quantity', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'full_name', 'total_amount', 'status', 'payment_method', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__username', 'full_name', 'phone', 'email')
    readonly_fields = ('order_number', 'subtotal', 'shipping_cost', 'discount', 'total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'product_price', 'subtotal')
    search_fields = ('order__order_number', 'product_name')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'verified', 'helpful_count', 'created_at')
    list_filter = ('rating', 'verified', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)
