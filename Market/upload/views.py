from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from .models import (
    Profile, Category, Product, ProductImage, Cart, CartItem,
    Order, OrderItem, Wishlist, Review
)
from .forms import RegisterForm, LoginForm, ProfileForm, UserTypeForm, ProductForm


# ============================================
# HOME VIEWS
# ============================================

def home(request):
    """Home page with featured products and categories"""
    categories = Category.objects.filter(is_active=True)[:4]
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:4]
    new_products = Product.objects.filter(is_active=True).order_by('-created_at')[:6]

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

def cart(request):
    """Shopping cart page"""
    cart_obj, created = get_or_create_cart(request)
    cart_items = cart_obj.items.all()

    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart.html', context)


def get_or_create_cart(request):
    """Helper function to get or create cart"""
    if request.user.is_authenticated:
        cart_obj, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_obj, created = Cart.objects.get_or_create(session_key=session_key)
    return cart_obj, created


def add_to_cart(request):
    """Add product to cart (AJAX)"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        product = get_object_or_404(Product, pk=product_id)
        cart_obj, created = get_or_create_cart(request)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart_obj,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return JsonResponse({
            'success': True,
            'message': 'تمت إضافة المنتج للسلة',
            'cart_count': cart_obj.items_count
        })

    return JsonResponse({'success': False})


def update_cart(request):
    """Update cart item quantity (AJAX)"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        cart_obj, _ = get_or_create_cart(request)

        try:
            cart_item = CartItem.objects.get(cart=cart_obj, product_id=product_id)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
            return JsonResponse({
                'success': True,
                'cart_count': cart_obj.items_count
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False})

    return JsonResponse({'success': False})


def remove_from_cart(request):
    """Remove product from cart (AJAX)"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        product_id = data.get('product_id')

        cart_obj, _ = get_or_create_cart(request)

        try:
            cart_item = CartItem.objects.get(cart=cart_obj, product_id=product_id)
            cart_item.delete()
            return JsonResponse({
                'success': True,
                'cart_count': cart_obj.items_count
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False})

    return JsonResponse({'success': False})


# ============================================
# CHECKOUT VIEWS
# ============================================

@login_required
def checkout(request):
    """Checkout page"""
    cart_obj, _ = get_or_create_cart(request)
    cart_items = cart_obj.items.all()

    if not cart_items:
        return redirect('store:cart')

    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
    }
    return render(request, 'store/checkout.html', context)


@login_required
def place_order(request):
    """Place order"""
    if request.method == 'POST':
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
            city=request.POST.get('city'),
            postal_code=request.POST.get('postal_code', ''),
            notes=request.POST.get('notes', ''),
            subtotal=subtotal,
            shipping_cost=shipping,
            total_amount=total,
            payment_method=request.POST.get('payment_method', 'cod'),
        )

        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )
            # Update product stock
            item.product.stock -= item.quantity
            item.product.sold_count += item.quantity
            item.product.save()

        # Clear cart
        cart_items.delete()

        messages.success(request, f'تم تأكيد طلبك بنجاح! رقم الطلب: {order.order_number}')
        return redirect('store:order_detail', pk=order.pk)

    return redirect('store:checkout')


# ============================================
# ORDER VIEWS
# ============================================

@login_required
def orders(request):
    """User orders history"""
    user_orders = Order.objects.filter(user=request.user)

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
    return render(request, 'store/order_detail.html', {'order': order})


# ============================================
# WISHLIST VIEWS
# ============================================

@login_required
def wishlist(request):
    """User wishlist page"""
    wishlist_items = Wishlist.objects.filter(user=request.user)

    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'store/wishlist.html', context)


@login_required
def toggle_wishlist(request):
    """Add/Remove from wishlist (AJAX)"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        product_id = data.get('product_id')

        product = get_object_or_404(Product, pk=product_id)

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': 'تم إزالة المنتج من المفضلة'
            })

        return JsonResponse({
            'success': True,
            'action': 'added',
            'message': 'تمت إضافة المنتج للمفضلة'
        })

    return JsonResponse({'success': False})


# ============================================
# ACCOUNT VIEWS
# ============================================

def login_view(request):
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
                if user.profile.is_seller:
                    return redirect('store:merchant_dashboard')
                return redirect('store:home')

            messages.error(request, 'بيانات الدخول غير صحيحة')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'تم تسجيل الخروج')
    return redirect('store:home')


def register(request):
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
            form = RegisterForm(request.POST, request.FILES)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, 'تم إنشاء الحساب وتسجيل الدخول')
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
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الملف الشخصي')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'accounts/profile.html', {'form': form})


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
