import time
import random
import json
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
    Order, OrderItem, Wishlist, Review
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
    products_list = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)

    # Filter by category
    category_ids = request.GET.getlist('category')
    if category_ids:
        products_list = products_list.filter(category_id__in=category_ids)

    # Filter by price
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products_list = products_list.filter(price__gte=min_price)
    if max_price:
        products_list = products_list.filter(price__lte=max_price)

    # Filter by search
    search = request.GET.get('search')
    if search:
        products_list = products_list.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # Filter by in stock
    in_stock = request.GET.get('in_stock')
    if in_stock:
        products_list = products_list.filter(stock__gt=0)

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    sort_options = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'rating': '-rating',
        'popular': '-sold_count',
    }
    products_list = products_list.order_by(sort_options.get(sort, '-created_at'))

    # Pagination
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,
        'categories': categories,
        'selected_categories': category_ids,
        'current_sort': sort,
    }
    return render(request, 'store/products.html', context)


def product_detail(request, pk):
    """Product detail page"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=pk)[:4]
    reviews = product.reviews.all()[:5]

    # Check if in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'store/product_detail.html', context)


# ============================================
# CART VIEWS
# ============================================

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


def cart(request):
    """Shopping cart page"""
    cart_obj, created = get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('product').all()

    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart.html', context)


@require_POST
def add_to_cart(request):
    """Add product to cart (AJAX)"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        if quantity < 1:
            return JsonResponse({'success': False, 'message': 'الكمية غير صالحة'})

        product = get_object_or_404(Product, pk=product_id, is_active=True)
        
        if product.stock < quantity:
            return JsonResponse({
                'success': False, 
                'message': f'الكمية المتوفرة: {product.stock}'
            })

        cart_obj, created = get_or_create_cart(request)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart_obj,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return JsonResponse({
                    'success': False, 
                    'message': f'الكمية المتوفرة: {product.stock}'
                })
            cart_item.quantity = new_quantity
            cart_item.save()

        return JsonResponse({
            'success': True,
            'message': 'تمت إضافة المنتج للسلة',
            'cart_count': cart_obj.total_items
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'حدث خطأ'})


@require_POST
def update_cart(request):
    """Update cart item quantity (AJAX)"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        if quantity < 0:
            return JsonResponse({'success': False, 'message': 'الكمية غير صالحة'})

        cart_obj, _ = get_or_create_cart(request)

        try:
            cart_item = CartItem.objects.get(cart=cart_obj, product_id=product_id)
            
            if quantity == 0:
                cart_item.delete()
            elif quantity > cart_item.product.stock:
                return JsonResponse({
                    'success': False, 
                    'message': f'الكمية المتوفرة: {cart_item.product.stock}'
                })
            else:
                cart_item.quantity = quantity
                cart_item.save()
                
            return JsonResponse({
                'success': True,
                'cart_count': cart_obj.total_items,
                'cart_total': float(cart_obj.total_price)
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'المنتج غير موجود في السلة'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'حدث خطأ'})


@require_POST
def remove_from_cart(request):
    """Remove product from cart (AJAX)"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        cart_obj, _ = get_or_create_cart(request)

        try:
            cart_item = CartItem.objects.get(cart=cart_obj, product_id=product_id)
            cart_item.delete()
            return JsonResponse({
                'success': True,
                'cart_count': cart_obj.total_items,
                'cart_total': float(cart_obj.total_price)
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'المنتج غير موجود في السلة'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'حدث خطأ'})


# ============================================
# CHECKOUT VIEWS
# ============================================

@login_required
def checkout(request):
    """Checkout page"""
    cart_obj, _ = get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('product').all()

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
    cart_items = cart_obj.items.select_related('product').all()

    if not cart_items:
        messages.error(request, 'سلة التسوق فارغة')
        return redirect('store:cart')

    # Check stock availability
    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(request, f'الكمية المتوفرة من {item.product.name}: {item.product.stock}')
            return redirect('store:cart')

    # Calculate totals
    subtotal = sum(item.subtotal for item in cart_items)
    shipping = 0 if subtotal >= 200 else 25
    total = subtotal + shipping

    # Create order
    order = Order.objects.create(
        user=request.user,
        full_name=request.POST.get('full_name', request.user.get_full_name()),
        phone=request.POST.get('phone', request.user.profile.phone if hasattr(request.user, 'profile') else ''),
        email=request.POST.get('email', request.user.email),
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

    messages.success(request, f'تم تأكيد طلبك بنجاح! رقم الطلب: #{order.id}')
    return redirect('store:order_detail', pk=order.pk)


# ============================================
# ORDER VIEWS
# ============================================

@login_required
def orders(request):
    """User orders history"""
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Filter by status
    status = request.GET.get('status')
    if status:
        user_orders = user_orders.filter(current_status=status)

    context = {
        'orders': user_orders,
        'current_status': status,
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
    """
    Login view with OTP verification:
    Step 1: Show username/email and password fields
    Step 2: After clicking login, send OTP and show verification code field
    Step 3: Verify OTP and complete login
    """
    
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        # Check if this is step 1 (login) or step 2 (OTP verification)
        otp_sent = request.POST.get('otp_sent') == 'true'
        
        if otp_sent:
            # Step 2: Verify OTP
            user_id = request.session.get('login_user_id')
            code_verification = request.POST.get('code_verification', '').strip()
            
            if not user_id:
                messages.error(request, 'انتهت صلاحية الجلسة، يرجى المحاولة مرة أخرى')
                return redirect('store:login')
            
            if not code_verification:
                messages.error(request, 'يرجى إدخال رمز التحقق')
                masked_email = request.session.get('login_user_email', '')
                return render(request, 'accounts/login.html', {
                    'form': form, 
                    'otp_sent': True,
                    'user_email': masked_email
                })
            
            try:
                User = get_user_model()
                user = User.objects.get(id=user_id)
                
                # Verify the OTP code
                if verify_otp_code(user.email, code_verification):
                    # Clear session data
                    request.session.pop('login_user_id', None)
                    request.session.pop('login_user_email', None)
                    request.session.pop('login_timestamp', None)
                    
                    # Login the user
                    login(request, user)
                    messages.success(request, 'تم تسجيل الدخول بنجاح')
                    
                    # Redirect based on user type
                    if hasattr(user, 'profile') and user.profile.is_seller:
                        return redirect('store:merchant_dashboard')
                    return redirect('store:home')
                else:
                    messages.error(request, 'رمز التحقق غير صحيح أو منتهي الصلاحية')
                    masked_email = mask_email(user.email)
                    return render(request, 'accounts/login.html', {
                        'form': form, 
                        'otp_sent': True,
                        'user_email': masked_email
                    })
                    
            except User.DoesNotExist:
                messages.error(request, 'حدث خطأ، يرجى المحاولة مرة أخرى')
                return redirect('store:login')
        
        else:
            # Step 1: Validate credentials and send OTP
            user_input = request.POST.get('user', '').strip()
            password = request.POST.get('password', '')
            
            if not user_input or not password:
                messages.error(request, 'يرجى ملء جميع الحقول')
                return render(request, 'accounts/login.html', {'form': form})
            
            # Allow login with either username or email
            user = authenticate(request, username=user_input, password=password)
            
            if user is None:
                # Try with email
                try:
                    User = get_user_model()
                    user_obj = User.objects.get(email__iexact=user_input)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None:
                # Check if user is active
                if not user.is_active:
                    messages.error(request, 'حسابك غير مفعل، يرجى التواصل مع الدعم')
                    return render(request, 'accounts/login.html', {'form': form})
                
                # Check rate limiting for OTP
                cache_key = f'otp_rate_limit_{user.email}'
                if cache.get(cache_key):
                    messages.warning(request, 'يرجى الانتظار 60 ثانية قبل طلب رمز جديد')
                    masked_email = mask_email(user.email)
                    return render(request, 'accounts/login.html', {
                        'form': form,
                        'otp_sent': True,
                        'user_email': masked_email
                    })
                
                # Send OTP email
                send_otp_email(to_email=user.email, username=user.username)
                
                # Set rate limit
                cache.set(cache_key, True, 60)
                
                # Store user info in session
                request.session['login_user_id'] = user.id
                request.session['login_user_email'] = mask_email(user.email)
                request.session['login_timestamp'] = int(time.time())
                
                messages.info(request, 'تم إرسال رمز التحقق إلى بريدك الإلكتروني')
                
                return render(request, 'accounts/login.html', {
                    'form': form,
                    'otp_sent': True,
                    'user_email': mask_email(user.email)
                })
            else:
                messages.error(request, 'بيانات الدخول غير صحيحة')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح')
    return redirect('store:home')


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
            form = RegisterForm(request.POST, request.FILES)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, 'تم إنشاء الحساب وتسجيل الدخول بنجاح')
                
                # Send welcome email
                send_registration_confirmation(to_email=user.email, username=user.username)
                
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
            
            # Send notification email
            password_change_notification(to_email=request.user.email, username=request.user.username)
            
            return redirect('store:profile')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


# ============================================
# PASSWORD RESET VIEWS
# ============================================

def forgot_password(request):
    """
    Forgot password view - Step 1:
    User enters email, send password reset link
    """
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'يرجى إدخال البريد الإلكتروني')
            return render(request, 'accounts/forgot_password.html')
        
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
            
            # Check rate limiting
            cache_key = f'password_reset_rate_limit_{email}'
            if cache.get(cache_key):
                messages.warning(request, 'يرجى الانتظار 60 ثانية قبل طلب رابط جديد')
                return render(request, 'accounts/forgot_password.html')
            
            # Generate password reset token
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Store token in cache for additional validation
            cache.set(f'password_reset_token_{user.pk}', token, 3600)  # 1 hour
            
            # Build reset URL
            reset_url = request.build_absolute_uri(
                reverse('store:reset_password', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send password reset email
            send_password_reset_email(
                to_email=user.email,
                username=user.username,
                reset_url=reset_url
            )
            
            # Set rate limit
            cache.set(cache_key, True, 60)
            
            messages.success(request, 'تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني')
            return render(request, 'accounts/password_reset_sent.html', {'email': mask_email(user.email)})
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            messages.success(request, 'إذا كان البريد مسجل لدينا، ستصلك رسالة بإعادة تعيين كلمة المرور')
            return render(request, 'accounts/password_reset_sent.html')
    
    return render(request, 'accounts/forgot_password.html')


def reset_password(request, uidb64, token):
    """
    Reset password view - Step 2:
    User sets new password using the link from email
    """
    if request.user.is_authenticated:
        return redirect('store:home')
    
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.hashers import make_password
    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None
    
    # Validate token
    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'رابط إعادة تعيين كلمة المرور غير صالح أو منتهي الصلاحية')
        return redirect('store:forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validate passwords
        if not new_password or not confirm_password:
            messages.error(request, 'يرجى ملء جميع الحقول')
            return render(request, 'accounts/reset_password.html', {
                'uidb64': uidb64,
                'token': token
            })
        
        if new_password != confirm_password:
            messages.error(request, 'كلمات المرور غير متطابقة')
            return render(request, 'accounts/reset_password.html', {
                'uidb64': uidb64,
                'token': token
            })
        
        # Validate password strength
        if len(new_password) < 8:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
            return render(request, 'accounts/reset_password.html', {
                'uidb64': uidb64,
                'token': token
            })
        
        # Set new password
        user.password = make_password(new_password)
        user.save()
        
        # Clear any cached tokens
        cache.delete(f'password_reset_token_{user.pk}')
        
        # Send confirmation email
        password_reset_success_email(to_email=user.email, username=user.username)
        
        messages.success(request, 'تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول')
        return render(request, 'accounts/password_reset_complete.html')
    
    return render(request, 'accounts/reset_password.html', {
        'uidb64': uidb64,
        'token': token
    })


def send_password_reset_email(to_email, username, reset_url):
    """Send password reset email"""
    send_mail(
        subject="🔑 إعادة تعيين كلمة المرور - متجرنا",
        message=f"لإعادة تعيين كلمة المرور، يرجى زيارة: {reset_url}",
        from_email=None,
        recipient_list=[to_email],
        html_message=f"""
        <div dir="rtl" style="font-family:Arial; max-width:600px; margin:auto; padding:20px; border:1px solid #e0e0e0; border-radius:10px;">
            <h2 style="color:#5C8A6E; text-align:center;">متجرنا</h2>
            <hr>
            <p>مرحباً <strong>{username}</strong> 👋</p>
            <p>لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بك.</p>
            <p>اضغط على الزر أدناه لإعادة تعيين كلمة المرور:</p>
            <div style="text-align:center; margin:25px 0;">
                <a href="{reset_url}" style="background:#5C8A6E; color:white; padding:12px 30px; text-decoration:none; border-radius:8px; font-weight:bold;">
                    إعادة تعيين كلمة المرور
                </a>
            </div>
            <p style="color:#888; font-size:13px;">⏳ الرابط صالح لمدة <strong>ساعة واحدة</strong> فقط.</p>
            <p style="color:#888; font-size:13px;">⚠️ إذا لم تطلب هذا التغيير، يمكنك تجاهل هذه الرسالة بأمان.</p>
            <hr>
            <p style="color:#aaa; font-size:12px; text-align:center;">© 2026 متجرنا - جميع الحقوق محفوظة</p>
        </div>
        """,
        fail_silently=False,
    )


def password_reset_success_email(to_email, username):
    """Send password reset success notification"""
    send_mail(
        subject="✅ تم تغيير كلمة المرور - متجرنا",
        message=f"مرحباً {username}، تم تغيير كلمة المرور الخاصة بك بنجاح.",
        from_email=None,
        recipient_list=[to_email],
        html_message=f"""
        <div dir="rtl" style="font-family:Arial; max-width:600px; margin:auto; padding:20px; border:1px solid #e0e0e0; border-radius:10px;">
            <h2 style="color:#5C8A6E; text-align:center;">متجرنا</h2>
            <hr>
            <p>مرحباً <strong>{username}</strong> 👋</p>
            <p>تم تغيير كلمة المرور الخاصة بك بنجاح ✅</p>
            <p>يمكنك الآن تسجيل الدخول باستخدام كلمة المرور الجديدة.</p>
            <div style="background:#FEF3E2; padding:15px; border-radius:8px; margin:20px 0;">
                <p style="margin:0; color:#C9897A; font-size:14px;">
                    ⚠️ إذا لم تقم بهذا التغيير، يرجى التواصل معنا فوراً.
                </p>
            </div>
            <hr>
            <p style="color:#aaa; font-size:12px; text-align:center;">© 2026 متجرنا - جميع الحقوق محفوظة</p>
        </div>
        """,
        fail_silently=False,
    )


@require_POST
def resend_otp(request):
    """Resend OTP code via AJAX"""
    try:
        data = json.loads(request.body) if request.body else {}
        email = data.get('email', '')
        
        # If email provided (from resend_otp page)
        if email:
            User = get_user_model()
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'البريد الإلكتروني غير مسجل لدينا'
                })
        else:
            # Get from session (from login page)
            user_id = request.session.get('login_user_id')
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'message': 'انتهت صلاحية الجلسة، يرجى المحاولة مرة أخرى'
                })
            
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'حدث خطأ، يرجى المحاولة مرة أخرى'
                })
        
        # Check rate limiting
        cache_key = f'otp_rate_limit_{user.email}'
        if cache.get(cache_key):
            return JsonResponse({
                'success': False,
                'message': 'يرجى الانتظار 60 ثانية قبل إعادة الإرسال'
            })
        
        # Send new OTP
        send_otp_email(to_email=user.email, username=user.username)
        
        # Set rate limit
        cache.set(cache_key, True, 60)
        
        # Update session
        request.session['login_user_id'] = user.id
        request.session['login_user_email'] = mask_email(user.email)
        
        return JsonResponse({
            'success': True,
            'message': 'تم إرسال رمز التحقق بنجاح'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ، يرجى المحاولة مرة أخرى'
        })


def resend_otp_page(request):
    """Standalone page for resending OTP"""
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'يرجى إدخال البريد الإلكتروني')
            return render(request, 'accounts/resend_otp.html')
        
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
            
            # Check rate limiting
            cache_key = f'otp_rate_limit_{email}'
            if cache.get(cache_key):
                messages.warning(request, 'يرجى الانتظار 60 ثانية قبل إعادة الإرسال')
                return render(request, 'accounts/resend_otp.html')
            
            # Send new OTP
            send_otp_email(to_email=user.email, username=user.username)
            
            # Set rate limit
            cache.set(cache_key, True, 60)
            
            # Store in session
            request.session['login_user_id'] = user.id
            request.session['login_user_email'] = mask_email(user.email)
            
            messages.success(request, 'تم إرسال رمز التحقق إلى بريدك الإلكتروني')
            return redirect('store:login')
            
        except User.DoesNotExist:
            messages.error(request, 'البريد الإلكتروني غير مسجل لدينا')
    
    return render(request, 'accounts/resend_otp.html')


# ============================================
# MERCHANT VIEWS
# ============================================

@login_required
def merchant_dashboard(request):
    """Merchant dashboard"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'هذه الصفحة متاحة للتاجر فقط')
        return redirect('store:home')

    products = Product.objects.filter(seller=request.user)
    
    # Get orders containing merchant's products
    order_items = OrderItem.objects.filter(product__seller=request.user)
    order_ids = order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids)

    # Calculate stats
    total_sales = order_items.aggregate(total=Sum('subtotal'))['total'] or 0
    total_orders = orders.count()
    total_products = products.count()
    low_stock_count = products.filter(stock__lt=5).count()
    avg_rating = products.aggregate(avg=Avg('rating'))['avg'] or 0
    total_reviews = sum(p.reviews_count for p in products if p.reviews_count)

    context = {
        'stats': {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'total_products': total_products,
            'low_stock': low_stock_count,
            'avg_rating': round(avg_rating, 1),
            'total_reviews': total_reviews,
        },
        'recent_orders': orders.order_by('-created_at')[:5],
        'low_stock_products': products.filter(stock__lt=5)[:5],
    }
    return render(request, 'store/merchant_dashboard.html', context)


@login_required
def merchant_products(request):
    """Merchant products list"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'هذه الصفحة متاحة للتاجر فقط')
        return redirect('store:home')

    products_list = Product.objects.filter(seller=request.user)
    
    # Search
    search = request.GET.get('search')
    if search:
        products_list = products_list.filter(
            Q(name__icontains=search) | Q(sku__icontains=search)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products_list = products_list.filter(category_id=category_id)
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        products_list = products_list.filter(is_active=True)
    elif status == 'inactive':
        products_list = products_list.filter(is_active=False)
    elif status == 'low_stock':
        products_list = products_list.filter(stock__lt=5)
    
    # Sort
    sort = request.GET.get('sort', '-created_at')
    products_list = products_list.order_by(sort)
    
    # Pagination
    paginator = Paginator(products_list, 10)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,
        'categories': Category.objects.filter(is_active=True),
        'stats': {
            'total': Product.objects.filter(seller=request.user).count(),
            'active': Product.objects.filter(seller=request.user, is_active=True).count(),
            'inactive': Product.objects.filter(seller=request.user, is_active=False).count(),
            'low_stock': Product.objects.filter(seller=request.user, stock__lt=5).count(),
        },
    }
    return render(request, 'store/merchant_products.html', context)


@login_required
def product_create(request):
    """Create new product"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
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
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'هذه الصفحة متاحة للتاجر فقط')
        return redirect('store:home')

    # Get order items for this merchant's products
    order_items = OrderItem.objects.filter(
        product__seller=request.user
    ).select_related('order', 'product')
    
    # Get unique orders
    order_ids = order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(current_status=status)
    
    # Search by order ID
    search = request.GET.get('search')
    if search:
        orders = orders.filter(id__icontains=search)
    
    # Date filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)

    context = {
        'orders': orders_page,
        'stats': {
            'total': orders.count(),
            'to_pay': orders.filter(current_status='to_pay').count(),
            'to_ship': orders.filter(current_status='to_ship').count(),
            'shipped': orders.filter(current_status='shipped').count(),
            'delivered': orders.filter(current_status='delivered').count(),
        },
    }
    return render(request, 'store/merchant_orders.html', context)


# ============================================
# ERROR VIEWS
# ============================================

def error_view(request, error_code):
    """Generic error view"""
    error_info = {
        '400': {'title': 'طلب غير صالح', 'message': 'عذراً، الطلب الذي أرسلته غير صالح.'},
        '401': {'title': 'غير مصرح', 'message': 'عذراً، يجب تسجيل الدخول للوصول إلى هذه الصفحة.'},
        '403': {'title': 'الوصول محظور', 'message': 'عذراً، ليس لديك صلاحية للوصول إلى هذه الصفحة.'},
        '404': {'title': 'الصفحة غير موجودة', 'message': 'عذراً، الصفحة التي تبحث عنها غير موجودة.'},
        '429': {'title': 'طلبات كثيرة جداً', 'message': 'عذراً، قمت بإرسال طلبات كثيرة جداً.'},
        '500': {'title': 'خطأ في الخادم', 'message': 'عذراً، حدث خطأ غير متوقع في الخادم.'},
        '502': {'title': 'بوابة غير صالحة', 'message': 'عذراً، حدث خطأ في الاتصال بالخادم.'},
        '503': {'title': 'الخدمة غير متاحة', 'message': 'عذراً، الخدمة غير متاحة حالياً.'},
        '504': {'title': 'انتهت مهلة البوابة', 'message': 'عذراً، انتهت مهلة الاتصال بالخادم.'},
    }
    
    code = str(error_code)
    info = error_info.get(code, {'title': 'حدث خطأ', 'message': 'عذراً، حدث خطأ غير متوقع.'})
    
    return render(request, 'error.html', {
        'error_code': code,
        'error_title': info['title'],
        'error_message': info['message'],
    }, status=int(code) if code in error_info else 500)


def handler404_view(request, exception=None):
    return error_view(request, 404)


def handler500_view(request):
    return error_view(request, 500)


def handler403_view(request, exception=None):
    return error_view(request, 403)


def handler400_view(request, exception=None):
    return error_view(request, 400)


# ============================================
# HELPER FUNCTIONS
# ============================================

def send_otp_email(to_email, username):
    """Send OTP code to user's email"""
    otp_code = str(random.randint(100000, 999999))
    cache.set(f'otp_{to_email}', otp_code, 3600)  # 1 hour validity
    
    send_mail(
        subject="🔐 رمز التحقق الخاص بك - سوق",
        message=f"رمز التحقق: {otp_code}",
        from_email=None,
        recipient_list=[to_email],
        html_message=f"""
        <div dir="rtl" style="font-family:Arial; max-width:600px; margin:auto; padding:20px; border:1px solid #e0e0e0; border-radius:10px;">
            <h2 style="color:#5C8A6E; text-align:center;">سوق</h2>
            <hr>
            <p>مرحباً <strong>{username}</strong> 👋</p>
            <p>رمز التحقق الخاص بك:</p>
            <div style="text-align:center; margin:25px 0;">
                <span style="font-size:36px; font-weight:bold; letter-spacing:10px;
                             color:#5C8A6E; background:#EAF2EE; padding:15px 30px; border-radius:10px;">
                    {otp_code}
                </span>
            </div>
            <p style="color:#888; font-size:13px;">⏳ صالح لمدة <strong>5 دقائق</strong> فقط.</p>
            <p style="color:#888; font-size:13px;">⚠️ إذا لم تطلب هذا الرمز، تجاهل هذه الرسالة.</p>
            <hr>
            <p style="color:#aaa; font-size:12px; text-align:center;">© 2026 سوق - جميع الحقوق محفوظة</p>
        </div>
        """,
        fail_silently=False,
    )
    
    return otp_code


def verify_otp_code(email, code):
    """Verify OTP code"""
    stored_code = cache.get(f'otp_{email}')
    
    if stored_code and stored_code == code:
        cache.delete(f'otp_{email}')
        return True
    return False


def mask_email(email):
    """Mask email for display"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@')
    masked_local = local[:3] + '***' if len(local) > 3 else local[0] + '***'
    
    return f'{masked_local}@{domain}'


def send_registration_confirmation(to_email, username):
    """Send registration confirmation email"""
    send_mail(
        subject="🎉 تم إنشاء حسابك بنجاح - سوق",
        message=f"مرحباً {username}، تم إنشاء حسابك بنجاح في سوق!",
        from_email=None,
        recipient_list=[to_email],
        html_message=f"""
        <div dir="rtl" style="font-family:Arial; max-width:600px; margin:auto; padding:20px; border:1px solid #e0e0e0; border-radius:10px;">
            <h2 style="color:#5C8A6E; text-align:center;">سوق</h2>
            <hr>
            <p>مرحباً <strong>{username}</strong> 👋</p>
            <p>شكراً لانضمامك إلى سوق! 🎉</p>
            <p>يمكنك الآن استكشاف آلاف المنتجات والتسوق بكل سهولة.</p>
            <hr>
            <p style="color:#aaa; font-size:12px; text-align:center;">© 2026 سوق - جميع الحقوق محفوظة</p>
        </div>
        """,
        fail_silently=False,
    )


def password_change_notification(to_email, username):
    """Send password change notification"""
    send_mail(
        subject="🔒 تم تغيير كلمة المرور - سوق",
        message=f"مرحباً {username}، تم تغيير كلمة المرور الخاصة بك بنجاح.",
        from_email=None,
        recipient_list=[to_email],
        html_message=f"""
        <div dir="rtl" style="font-family:Arial; max-width:600px; margin:auto; padding:20px; border:1px solid #e0e0e0; border-radius:10px;">
            <h2 style="color:#5C8A6E; text-align:center;">سوق</h2>
            <hr>
            <p>مرحباً <strong>{username}</strong> 👋</p>
            <p>تم تغيير كلمة المرور الخاصة بك بنجاح.</p>
            <p style="color:#C9897A;">إذا لم تقم بهذا التغيير، يرجى التواصل مع الدعم فوراً.</p>
            <hr>
            <p style="color:#aaa; font-size:12px; text-align:center;">© 2026 سوق - جميع الحقوق محفوظة</p>
        </div>
        """,
        fail_silently=False,
    )
