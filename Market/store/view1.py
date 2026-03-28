import time
import random
import json
import re
from urllib import request
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Sum
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import (
    Profile, Category, Product, ProductImage, Cart, CartItem,
    Order, OrderItem, Wishlist, Review, ProductVariant
)
from .forms import RegisterForm, LoginForm, ProfileForm, UserTypeForm, ProductForm


# ============================================
# HOME VIEWS
# ============================================

def home(request):
    """Home page with featured products and categories"""
    categories = Category.objects.filter(is_active=True)[:4]
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    new_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'new_products': new_products,
    }
    return render(request, 'store/home.html', context)


# ============================================
# PRODUCT VIEWS
# ============================================

def products(request):
    """Products listing page with filters"""
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)

    # Filter by category
    category_ids = request.GET.getlist('category')
    if category_ids:
        products = products.filter(category_id__in=category_ids)

    # Filter by price
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Filter by search
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # Filter by in stock
    in_stock = request.GET.get('in_stock')
    if in_stock:
        products = products.filter(stock__gt=0)

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'rating':
        products = products.order_by('-rating')
    elif sort == 'popular':
        products = products.order_by('-sold_count')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/products.html', context)


def product_detail(request, pk):
    """Product detail page"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=pk)[:5]
    reviews = product.reviews.all()[:5]

    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
    }
    return render(request, 'store/product_detail.html', context)


# ============================================
# CART VIEWS
# ============================================

def get_or_create_cart(request):
    """Helper function to get or create cart"""
    if request.user.is_authenticated:
        cart_obj, created = Cart.objects.get_or_create(user=request.user)
        # If user had a session cart, merge it
        session_key = request.session.session_key
        if session_key:
            try:
                session_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
                # Merge session cart items into user cart
                for item in session_cart.items.all():
                    cart_item, created = CartItem.objects.get_or_create(
                        cart=cart_obj,
                        variant=item.variant,
                        defaults={'quantity': item.quantity}
                    )
                    if not created:
                        cart_item.quantity += item.quantity
                        cart_item.save()
                # Delete the session cart
                session_cart.delete()
            except Cart.DoesNotExist:
                pass
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_obj, created = Cart.objects.get_or_create(
            session_key=session_key,
            user__isnull=True
        )
    return cart_obj, created


def get_default_variant(product):
    """Get or create default variant for a product"""
    variant = product.variants.first()
    if not variant:
        # Create default variant if none exists
        variant = ProductVariant.objects.create(
            product=product,
            name='افتراضي',
            price=product.price,
            stock=product.stock,
            sku=product.sku or f'{product.id}-default'
        )
    return variant


def cart(request):
    """Shopping cart page"""
    cart_obj, created = get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('variant__product').all()

    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart.html', context)


def cart_count(request):
    """Get cart items count (AJAX)"""
    try:
        cart_obj, _ = get_or_create_cart(request)
        count = cart_obj.items_count
        return JsonResponse({
            'success': True,
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'count': 0
        })


def add_to_cart(request):
    """Add product to cart (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity', 1))

            if quantity < 1:
                return JsonResponse({
                    'success': False,
                    'message': 'الكمية غير صالحة'
                })

            product = get_object_or_404(Product, pk=product_id, is_active=True)
            
            # Get variant (specific or default)
            if variant_id:
                variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
            else:
                variant = get_default_variant(product)
            
            # التحقق من المخزون
            if variant.stock < quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'الكمية المتوفرة: {variant.stock}'
                })

            cart_obj, created = get_or_create_cart(request)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart_obj,
                variant=variant,
                defaults={'quantity': quantity}
            )

            if not created:
                new_quantity = cart_item.quantity + quantity
                if new_quantity > variant.stock:
                    return JsonResponse({
                        'success': False,
                        'message': f'الكمية المتوفرة: {variant.stock}'
                    })
                cart_item.quantity = new_quantity
                cart_item.save()

            return JsonResponse({
                'success': True,
                'message': 'تمت إضافة المنتج للسلة',
                'cart_count': cart_obj.items_count
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'حدث خطأ: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'طلب غير صالح'})


def update_cart(request):
    """Update cart item quantity (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')  # للتوافق مع الكود القديم
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity', 1))

            cart_obj, _ = get_or_create_cart(request)

            # البحث بالـ variant_id أو product_id
            if variant_id:
                cart_item = CartItem.objects.get(cart=cart_obj, variant_id=variant_id)
            elif product_id:
                # البحث عن طريق المنتج (للتوافق مع الكود القديم)
                cart_item = CartItem.objects.filter(
                    cart=cart_obj, 
                    variant__product_id=product_id
                ).first()
                if not cart_item:
                    return JsonResponse({'success': False, 'message': 'العنصر غير موجود'})
            else:
                return JsonResponse({'success': False, 'message': 'معرف غير صالح'})
            
            if quantity > 0:
                # التحقق من المخزون
                if quantity > cart_item.variant.stock:
                    return JsonResponse({
                        'success': False,
                        'message': f'الكمية المتوفرة: {cart_item.variant.stock}'
                    })
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

            return JsonResponse({
                'success': True,
                'cart_count': cart_obj.items_count
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'العنصر غير موجود'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False})


def remove_from_cart(request):
    """Remove product from cart (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')  # للتوافق مع الكود القديم
            variant_id = data.get('variant_id')

            cart_obj, _ = get_or_create_cart(request)

            # البحث بالـ variant_id أو product_id
            if variant_id:
                cart_item = CartItem.objects.get(cart=cart_obj, variant_id=variant_id)
            elif product_id:
                # البحث عن طريق المنتج (للتوافق مع الكود القديم)
                cart_item = CartItem.objects.filter(
                    cart=cart_obj, 
                    variant__product_id=product_id
                ).first()
                if not cart_item:
                    return JsonResponse({'success': False, 'message': 'العنصر غير موجود'})
            else:
                return JsonResponse({'success': False, 'message': 'معرف غير صالح'})
            
            cart_item.delete()

            return JsonResponse({
                'success': True,
                'cart_count': cart_obj.items_count
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'العنصر غير موجود'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False})


# ============================================
# CHECKOUT VIEWS
# ============================================

@login_required
def checkout(request):
    """Checkout page"""
    cart_obj, _ = get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('variant__product').all()

    if not cart_items:
        messages.warning(request, 'سلة التسوق فارغة')
        return redirect('store:cart')

    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
    }
    return render(request, 'store/checkout.html', context)


@login_required
@require_POST
def place_order(request):
    """Place order"""
    cart_obj, _ = get_or_create_cart(request)
    cart_items = cart_obj.items.all()

    if not cart_items:
        return redirect('store:cart')

    # Calculate totals
    subtotal = sum(item.subtotal for item in cart_items)
    shipping = 0 if subtotal >= 200 else 25
    total = subtotal + shipping

    # Create order
    order = Order.objects.create(
        user=request.user,
        full_name=request.POST.get('full_name'),
        phone=request.POST.get('phone'),
        email=request.POST.get('email'),
        address=request.POST.get('address'),
        wilaya=request.POST.get('wilaya', ''),
        baladia=request.POST.get('baladia', ''),
        postal_code=request.POST.get('postal_code', ''),
        notes=request.POST.get('notes', ''),
        subtotal=subtotal,
        shipping_cost=shipping,
        total_amount=total,
        payment_method=request.POST.get('payment_method', 'cod'),
    )

    # Create order items
    for item in cart_items:
        product = item.variant.product
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_price=item.variant.price,
            quantity=item.quantity,
            subtotal=item.subtotal
        )
        # Update variant stock
        item.variant.stock -= item.quantity
        item.variant.save()
        
        # Update product sold count
        product.sold_count = getattr(product, 'sold_count', 0) + item.quantity
        product.save()

    # Clear cart
    cart_items.delete()

    messages.success(request, f'تم تأكيد طلبك بنجاح! رقم الطلب: {order.order_number}')
    return redirect('store:order_detail', pk=order.pk)


# ============================================
# ORDER VIEWS
# ============================================

@login_required
def orders(request):
    """User orders history"""
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': user_orders,
    }
    return render(request, 'store/orders.html', context)


@login_required
def order_detail(request, pk):
    """Order detail page"""
    order = get_object_or_404(Order, pk=pk, user=request.user)

    context = {
        'order': order,
    }
    return render(request, 'store/order_detail.html', context)


# ============================================
# WISHLIST VIEWS
# ============================================

@login_required
def wishlist(request):
    """User wishlist page"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')

    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'store/wishlist.html', context)


@login_required
@require_POST
def toggle_wishlist(request):
    """Add/Remove from wishlist (AJAX)"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        product = get_object_or_404(Product, pk=product_id, is_active=True)

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': 'تم إزالة المنتج من المفضلة',
                'wishlist_count': Wishlist.objects.filter(user=request.user).count()
            })

        return JsonResponse({
            'success': True,
            'action': 'added',
            'message': 'تمت إضافة المنتج للمفضلة',
            'wishlist_count': Wishlist.objects.filter(user=request.user).count()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'حدث خطأ'})


# ============================================
# ACCOUNT VIEWS
# ============================================

def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'تم تسجيل الدخول بنجاح')

                # Redirect based on user type
                if hasattr(user, 'profile') and user.profile.is_seller:
                    return redirect('store:merchant_dashboard')
                return redirect('store:home')

            messages.error(request, 'بيانات الدخول غير صحيحة')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح')
    return redirect('store:home')


User = get_user_model()

def register(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('store:home')

    user_type = request.GET.get('type')

    # Step 1: Choose account type
    if request.method == 'POST' and 'choose_type' in request.POST:
        type_form = UserTypeForm(request.POST)
        if type_form.is_valid():
            selected = type_form.cleaned_data['user_type']
            return redirect(f"{request.path}?type={selected}")
        return render(request, 'accounts/register.html', {'type_form': type_form})

    # Step 2: Registration details
    if user_type in ['customer', 'seller']:
        if request.method == 'POST' and 'username' in request.POST:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip().lower()
            
            # التحقق من اسم المستخدم - لا رموز
            if not re.match(r'^[a-zA-Z0-9_\u0600-\u06FF]+$', username):
                messages.error(request, 'اسم المستخدم يجب أن يحتوي على أحرف وأرقام فقط بدون رموز')
                form = RegisterForm(request.POST, request.FILES)
                return render(request, 'accounts/register.html', {
                    'form': form,
                    'user_type': user_type,
                })
            
            # التحقق من طول اسم المستخدم
            if len(username) < 3:
                messages.error(request, 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل')
                form = RegisterForm(request.POST, request.FILES)
                return render(request, 'accounts/register.html', {
                    'form': form,
                    'user_type': user_type,
                })
            
            if len(username) > 30:
                messages.error(request, 'اسم المستخدم يجب ألا يتجاوز 30 حرف')
                form = RegisterForm(request.POST, request.FILES)
                return render(request, 'accounts/register.html', {
                    'form': form,
                    'user_type': user_type,
                })
            
            # التحقق من عدم وجود اسم المستخدم مسبقاً
            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, 'اسم المستخدم مستخدم بالفعل، اختر اسماً آخر')
                form = RegisterForm(request.POST, request.FILES)
                return render(request, 'accounts/register.html', {
                    'form': form,
                    'user_type': user_type,
                })
            
            # التحقق من عدم وجود البريد الإلكتروني مسبقاً
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, 'البريد الإلكتروني مستخدم بالفعل، سجل الدخول أو استخدم بريداً آخر')
                form = RegisterForm(request.POST, request.FILES)
                return render(request, 'accounts/register.html', {
                    'form': form,
                    'user_type': user_type,
                })
            
            form = RegisterForm(request.POST, request.FILES)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, 'تم إنشاء الحساب وتسجيل الدخول بنجاح')
                return redirect('store:home')
        else:
            form = RegisterForm(initial={'user_type': user_type})

        return render(request, 'accounts/register.html', {
            'form': form,
            'user_type': user_type,
        })

    # Display type selection
    type_form = UserTypeForm()
    return render(request, 'accounts/register.html', {'type_form': type_form})


@login_required
def profile(request):
    """User profile page"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
            return redirect('store:profile')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('store:profile')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


# ============================================
# MERCHANT VIEWS
# ============================================

@login_required
def merchant_dashboard(request):
    """Merchant dashboard"""
    if not request.user.profile.is_seller:
        messages.error(request, 'هذه الصفحة متاحة للتاجر فقط')
        return redirect('store:home')

    products = Product.objects.filter(seller=request.user)
    orders = Order.objects.filter(items__product__seller=request.user).distinct()

    context = {
        'stats': {
            'total_sales': sum(order.total_amount for order in orders),
            'total_orders': orders.count(),
            'total_products': products.count(),
            'low_stock': products.filter(stock__lt=5).count(),
            'avg_rating': products.aggregate(Avg('rating'))['rating__avg'] or 0,
            'total_reviews': sum(p.reviews_count for p in products),
        },
        'recent_orders': orders[:5],
        'low_stock_products': products.filter(stock__lt=5)[:5],
    }
    return render(request, 'store/merchant_dashboard.html', context)


@login_required
def merchant_products(request):
    """Merchant products list"""
    if not request.user.profile.is_seller:
        messages.error(request, 'هذه الصفحة متاحة للتاجر فقط')
        return redirect('store:home')

    products = Product.objects.filter(seller=request.user)

    context = {
        'products': products,
    }
    return render(request, 'store/merchant_products.html', context)


@login_required
def product_create(request):
    """Create new product"""
    if not request.user.profile.is_seller:
        messages.error(request, 'هذه الصفحة متاحة للتاجر فقط')
        return redirect('store:home')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            
            # إنشاء متغير افتراضي للمنتج الجديد
            ProductVariant.objects.create(
                product=product,
                name='افتراضي',
                price=product.price,
                stock=product.stock,
                sku=product.sku or f'{product.id}-default'
            )
            
            messages.success(request, 'تم إضافة المنتج بنجاح')
            return redirect('store:merchant_products')
    else:
        form = ProductForm()

    context = {
        'form': form,
        'categories': Category.objects.filter(is_active=True),
    }
    return render(request, 'store/product_form.html', context)


@login_required
def product_update(request, pk):
    """Update product"""
    product = get_object_or_404(Product, pk=pk, seller=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث المنتج بنجاح')
            return redirect('store:merchant_products')
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'product': product,
        'categories': Category.objects.filter(is_active=True),
    }
    return render(request, 'store/product_form.html', context)


@login_required
def product_delete(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk, seller=request.user)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'تم حذف المنتج بنجاح')
        return redirect('store:merchant_products')

    return render(request, 'store/product_confirm_delete.html', {'product': product})


@login_required
def merchant_orders(request):
    """Merchant orders list"""
    if not request.user.profile.is_seller:
        messages.error(request, 'هذه الصفحة متاحة للتاجر فقط')
        return redirect('store:home')

    # Get orders that contain products from this merchant
    orders = Order.objects.filter(items__product__seller=request.user).distinct()

    context = {
        'orders': orders,
    }
    return render(request, 'store/merchant_orders.html', context)


# ============================================
# ERROR HANDLERS
# ============================================

def error_view(request, error_code):
    """Error page view"""
    return render(request, 'error.html', {'error_code': error_code}, status=error_code)


def handler404_view(request, exception=None):
    """404 handler"""
    return render(request, 'errors/404.html', status=404)


def handler500_view(request):
    """500 handler"""
    return render(request, 'errors/500.html', status=500)


def handler403_view(request, exception=None):
    """403 handler"""
    return render(request, 'errors/403.html', status=403)


def handler400_view(request, exception=None):
    """400 handler"""
    return render(request, 'errors/400.html', status=400)


# ============================================
# PASSWORD RESET VIEWS
# ============================================

def forgot_password(request):
    """Forgot password view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate and send OTP
            # ... OTP logic here
            messages.success(request, 'تم إرسال رمز التحقق إلى بريدك الإلكتروني')
            return redirect('store:reset_password', uidb64='', token='')
        except User.DoesNotExist:
            messages.error(request, 'البريد الإلكتروني غير مسجل')
    
    return render(request, 'accounts/forgot_password.html')


def reset_password(request, uidb64, token):
    """Reset password view"""
    # ... password reset logic
    return render(request, 'accounts/reset_password.html')


def resend_otp(request):
    """Resend OTP"""
    # ... resend OTP logic
    return JsonResponse({'success': True})


def send_invoice(request, pk):
    """Send invoice to email"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    # ... send invoice logic
    messages.success(request, 'تم إرسال الفاتورة إلى بريدك الإلكتروني')
    return redirect('store:order_detail', pk=pk)
