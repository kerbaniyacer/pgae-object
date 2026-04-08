import json
import uuid
import re
import random
import hashlib
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q, Count, Min, Max, Sum
from django.core.paginator import Paginator
from django.utils.text import slugify
from .models import (
    Category, Product, ProductVariant, ProductAttribute, 
    Wishlist, Cart, CartItem, Order, OrderItem, Brand,
    ProductVideo, Brand, WishlistItem, SubscriptEmail, VariantImage
)
from .forms import ProductForm, ProductVariantForm



# Create your views here.
def home(request):
    categories = Category.objects.filter(is_active=True, parent=None)[:4]
    featured_products = Product.objects.filter(is_active=True, is_featured=True, variants__stock__gt=0).distinct()[:8]
    try:
        new_products = Product.objects.filter(is_active=True, variants__stock__gt=0).distinct().order_by('-sold_count')[:8]
    except Exception:
        new_products = None
        
    variants = []
    for product in featured_products:
        v = ProductVariant.objects.filter(product=product, is_main=True, stock__gt=0).first()
        if not v:
            v = ProductVariant.objects.filter(product=product, stock__gt=0).first()
        if not v:
            v = ProductVariant.objects.filter(product=product).first()
        variants.append(v)
        
        # ✅ إصلاح: لا تحفظ الـ Property في قاعدة البيانات
        # product.is_owner يُحسب لحظياً في الـ Template ولن نستخدم save()

    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    subscriptEmail = request.GET.get('subscriptEmail')
    if subscriptEmail:
        obj, created = SubscriptEmail.objects.get_or_create(
            email=subscriptEmail
        )
        if created :
            send_newsletter_welcome(to_email=subscriptEmail, username= request.user.username or 'صديقنا')
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'new_products': new_products,
        'variants': variants,
        'wishlist_product_ids': wishlist_product_ids,
    }
    return render(request, 'store/home.html', context)

def send_newsletter_welcome(to_email, username=None):
    """Send newsletter subscription welcome email"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings
    import threading

    subject = '📩 مرحباً بك في النشرة اليومية!'
    
    html_message = render_to_string('emails/newsletter.html', {
        'username': username or 'صديقنا',
    })
    
    plain_message = strip_tags(html_message)

    kwargs = {
        'subject': subject,
        'message': plain_message,
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'recipient_list': [to_email],
        'html_message': html_message,
    }
    
    threading.Thread(target=send_mail, kwargs=kwargs, daemon=True).start()
# ============================================
# PRODUCT VIEWS
# ============================================
def products(request):
    products = Product.objects.filter(is_active=True, variants__stock__gt=0).distinct()
    categories = Category.objects.filter(is_active=True, parent=None)

    category_ids = request.GET.getlist('category')
    if category_ids:
        selected_cats = Category.objects.filter(id__in=category_ids)
        all_cat_ids = []
        for cat in selected_cats:
            all_cat_ids.append(cat.id)
            all_cat_ids.extend(cat.children.values_list('id', flat=True))
        products = products.filter(category_id__in=all_cat_ids)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(variants__price__gte=min_price).distinct()
    if max_price:
        products = products.filter(variants__price__lte=max_price).distinct()

    search = request.GET.get('search')
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))

    in_stock = request.GET.get('in_stock')
    if in_stock:
        products = products.filter(variants__stock__gt=0).distinct()

    sort = request.GET.get('sort')
    if sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'price_low':
        products = products.annotate(min_price=Min('variants__price')).order_by('min_price')
    elif sort == 'price_high':
        products = products.annotate(max_price=Max('variants__price')).order_by('-max_price')
    elif sort == 'rating':
        products = products.order_by('-rating')
    elif sort == 'popular':
        products = products.order_by('-sold_count')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    variant = []
    for product in products:
        v = ProductVariant.objects.filter(product=product, is_main=True, stock__gt=0).first()
        if not v:
            v = ProductVariant.objects.filter(product=product, stock__gt=0).first()
        if not v:
            v = ProductVariant.objects.filter(product=product).first()
        variant.append(v)

    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )

    context = {
        'products': products,
        'user': request.user,
        'categories': categories,
        'variant': variant,
        'wishlist_product_ids': wishlist_product_ids,
    }
    return render(request, 'store/products.html', context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    return redirect(f"{reverse('store:products')}?category={category.id}")

def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    return redirect('store:products')

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = ProductVariant.objects.filter(product=product)

    is_main = variants.filter(is_main=True, stock__gt=0).first()
    if not is_main:
        is_main = variants.filter(stock__gt=0).first()
    if not is_main:
        is_main = variants.filter(is_main=True).first() or variants.first()

    attr_map = {}     
    variants_json = []
    variant_images = VariantImage.objects.filter(
        product=product
    ).prefetch_related('variants')

    # صور في gallery (كل الصور)
    all_images = [
        {
            'id': img.id,
            'url': img.image.url,
            'is_main': img.is_main,
            'variant_ids': list(img.variants.values_list('id', flat=True)),
        }
        for img in variant_images
    ]
    for v in variants:
        raw_attrs = v.attributes if isinstance(v.attributes, dict) else {}

        # صورة المتغير من الموديل الجديد
        main_img = v.images.filter(is_main=True).first() or v.images.first()
        v_image = main_img.image.url if main_img else None

        clean_attributes_for_json = {}
        for attr_name, attr_value in raw_attrs.items():
            if isinstance(attr_value, dict):
                clean_attributes_for_json[attr_name] = attr_value.get('value', str(attr_value))
            else:
                clean_attributes_for_json[attr_name] = str(attr_value)

        variants_json.append({
            'id': v.id,
            'name': v.name,
            'sku': v.sku,
            'price': str(v.price),
            'old_price': str(v.old_price) if v.old_price else None,
            'discount': v.discount or 0,
            'stock': v.stock,
            'image': v_image,
            'image_id': main_img.id if main_img else None,
            'is_main': v.is_main,
            'attributes': clean_attributes_for_json,
        })

        # ✅ تعبئة attr_map بالخيارات المتاحة لتعرض في القالب
        for attr_name, attr_value in clean_attributes_for_json.items():
            if attr_name not in attr_map:
                attr_map[attr_name] = {}
            
            if attr_value not in attr_map[attr_name]:
                attr_map[attr_name][attr_value] = {
                    'value': attr_value,
                    'image': main_img,  # سنستخدم أول صورة نجدها لهذه القيمة (مثل لون معين)
                }

    variant_attributes = {
        attr_name: list(values.values())
        for attr_name, values in attr_map.items()
    }

    prices = [v.price for v in variants]
    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None
    has_price_range = min_price != max_price

    
    videos = ProductVideo.objects.filter(product=product)
    reviews = product.reviews.all().order_by('-created_at')[:10]
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:5]
    
    product_attributes = ProductAttribute.objects.filter(product=product)
    
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    context = {
        'product': product,
        'is_main': is_main,
        'variants': variants,
        'variants_json': json.dumps(variants_json, ensure_ascii=False),
        'variant_attributes': variant_attributes,
        'has_price_range': has_price_range,
        'min_price': min_price,
        'max_price': max_price,
        'videos': videos,
        'reviews': reviews,
        'related_products': related_products,
        'product_attributes': product_attributes,
        'is_owner': request.user == product.seller if request.user.is_authenticated else False,
        'all_images': json.dumps(all_images, ensure_ascii=False),
        'variant_images': variant_images,
        'wishlist_product_ids': wishlist_product_ids,
    }
    
    return render(request, 'store/product_detail.html', context)



@login_required
def product_copy(request, pk):
    product = get_object_or_404(Product, pk=pk)
    old_name = product.name
    product.pk = None
    product.name = f"{old_name} نسخة"
    product.slug = slugify(product.name) + "-" + str(uuid.uuid4())[:6]
    product.save()
    messages.success(request, "تم نسخ المنتج بنجاح")
    return redirect('store:merchant_products')


# ============================================
# CART VIEWS
# ============================================

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart_obj, created = Cart.objects.get_or_create(user=request.user)
        session_key = request.session.session_key
        if session_key:
            try:
                session_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
                for item in session_cart.items.all():
                    cart_item, created = CartItem.objects.get_or_create(
                        cart=cart_obj,
                        variant=item.variant,
                        defaults={'quantity': item.quantity}
                    )
                    if not created:
                        cart_item.quantity += item.quantity
                        cart_item.save()
                session_cart.delete()
            except Cart.DoesNotExist:
                pass
    else:
        if not request.session.session_key:
            request.session.create()
        cart_obj, created = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user=None
        )
    return cart_obj, created


def get_default_variant(product):
    variant = product.variants.filter(is_main=True, stock__gt=0).first()
    if not variant:
        variant = product.variants.filter(stock__gt=0).first()
    if not variant:
        variant = product.variants.filter(is_main=True).first() or product.variants.first()
        
    if not variant:
        variant = ProductVariant.objects.create(
            product=product,
            name='افتراضي',
            price=0,
            stock=0,
            sku=product.sku or f'{product.id}-default'
        )
    return variant


def cart(request):
    cart_obj, created = get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('variant__product').all()

    for item in cart_items:
        variant = item.variant
        product = variant.product

        # جلب كل متغيرات نفس المنتج
        all_variants = ProductVariant.objects.filter(product=product)

        # === بناء attr_map بنفس طريقة product_detail بالضبط ===
        attr_map = {}
        main_img = variant.images.filter(is_main=True).first() or variant.images.first()
        item.variant_image = main_img.image.url if main_img else None
        for v in all_variants:
            raw_attrs = v.attributes if isinstance(v.attributes, dict) else {}

            for attr_name, attr_value in raw_attrs.items():
                if isinstance(attr_value, dict):
                    actual_value = attr_value.get('value', str(attr_value))
                else:
                    actual_value = str(attr_value)

                if attr_name not in attr_map:
                    attr_map[attr_name] = {}

                if actual_value not in attr_map[attr_name]:
                    attr_map[attr_name][actual_value] = {
                        'value': actual_value,
                        'variant_id': v.id,
                        'price': str(v.price),
                        'old_price': str(v.old_price) if v.old_price else None,
                        'discount': v.discount or 0,
                        'stock': v.stock,
                        'sku': v.sku,
                        'image': main_img.image.url if main_img else None,
                    }

        # === استخراج القيم الحالية للمتغير المختار ===
        current_raw = variant.attributes if isinstance(variant.attributes, dict) else {}
        clean_current = {}
        for attr_name, attr_value in current_raw.items():
            if isinstance(attr_value, dict):
                clean_current[attr_name] = attr_value.get('value', str(attr_value))
            else:
                clean_current[attr_name] = str(attr_value)

        # === بناء القائمة النهائية لكل خاصية ===
        variant_attributes = []
        for attr_name, values in attr_map.items():
            current_value = clean_current.get(attr_name, '')

            options = []
            for val_data in values.values():
                option = dict(val_data)
                option['current'] = (option['value'] == current_value)
                options.append(option)

            variant_attributes.append({
                'name': attr_name,
                'value': current_value,
                'options': options,
            })

        item.variant_attributes = variant_attributes

    return render(request, 'store/' \
    'cart.html', {'cart_items': cart_items})

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

@require_POST
@csrf_protect
def update_cart_variant(request):
    try:
        data = json.loads(request.body)
        current_variant_id = data.get('current_variant_id')
        new_variant_id = data.get('new_variant_id')

        if not current_variant_id or not new_variant_id:
            return JsonResponse({'error': 'بيانات ناقصة'}, status=400)

        if str(current_variant_id) == str(new_variant_id):
            return JsonResponse({'success': True})

        cart, created = get_or_create_cart(request)

        # عنصر السلة الحالي
        cart_item = CartItem.objects.get(
            cart=cart, variant_id=current_variant_id
        )

        # المتغير الجديد
        new_variant = ProductVariant.objects.select_related('product').get(
            id=new_variant_id
        )

        # التحقق من التوفر
        if new_variant.stock <= 0:
            return JsonResponse({'error': 'هذا المتغير غير متوفر في المخزن'})

        # التحقق أنه نفس المنتج
        if new_variant.product_id != cart_item.variant.product_id:
            return JsonResponse({'error': 'متغير غير صالح'})

        # هل المتغير الجديد موجود أصلاً في السلة؟
        existing_item = CartItem.objects.filter(
            cart=cart, variant_id=new_variant_id
        ).first()

        if existing_item:
            existing_item.quantity += cart_item.quantity
            existing_item.save(update_fields=['quantity'])
            cart_item.delete()
        else:
            cart_item.variant = new_variant
            cart_item.save(update_fields=['variant'])

        return JsonResponse({'success': True})

    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'العنصر غير موجود في السلة'}, status=404)
    except ProductVariant.DoesNotExist:
        return JsonResponse({'error': 'المتغير غير موجود'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def cart_count(request):
    try:
        cart_obj, _ = get_or_create_cart(request)
        return JsonResponse({'success': True, 'count': cart_obj.items_count})
    except Exception:
        return JsonResponse({'success': False, 'count': 0})


def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity', 1))

            if quantity < 1:
                return JsonResponse({'success': False, 'message': 'الكمية غير صالحة'})

            product = get_object_or_404(Product, pk=product_id, is_active=True)
            
            # منع صاحب المنتج من إضافة منتجه للسلة
            if request.user.is_authenticated and product.seller == request.user:
                return JsonResponse({'success': False, 'message': 'لا يمكنك إضافة منتجك الخاص إلى السلة'})
                
            variant = get_object_or_404(ProductVariant, pk=variant_id, product=product) if variant_id else get_default_variant(product)
            
            if variant.stock < quantity:
                return JsonResponse({'success': False, 'message': f'الكمية المتوفرة: {variant.stock}'})

            cart_obj, created = get_or_create_cart(request)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart_obj, variant=variant, defaults={'quantity': quantity}
            )

            if not created:
                new_quantity = cart_item.quantity + quantity
                if new_quantity > variant.stock:
                    return JsonResponse({'success': False, 'message': f'الكمية المتوفرة: {variant.stock}'})
                cart_item.quantity = new_quantity
                cart_item.save()

            return JsonResponse({'success': True, 'message': 'تمت إضافة المنتج للسلة', 'cart_count': cart_obj.items_count})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'حدث خطأ: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'طلب غير صالح'})


def update_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity', 1))
            cart_obj, _ = get_or_create_cart(request)

            if variant_id:
                cart_item = CartItem.objects.get(cart=cart_obj, variant_id=variant_id)
            else:
                return JsonResponse({'success': False, 'message': 'معرف غير صالح'})
            
            if quantity > 0:
                if quantity > cart_item.variant.stock:
                    return JsonResponse({'success': False, 'message': f'الكمية المتوفرة: {cart_item.variant.stock}'})
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

            return JsonResponse({'success': True, 'cart_count': cart_obj.items_count})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'العنصر غير موجود'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False})


def remove_from_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            variant_id = data.get('variant_id')
            cart_obj, _ = get_or_create_cart(request)

            if variant_id:
                cart_item = CartItem.objects.get(cart=cart_obj, variant_id=variant_id)
            else:
                return JsonResponse({'success': False, 'message': 'معرف غير صالح'})
            
            cart_item.delete()
            return JsonResponse({'success': True, 'cart_count': cart_obj.items_count})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False})


# ============================================
# CHECKOUT & ORDERS VIEWS
# ============================================

def checkout(request):
    cart_obj, _ = get_or_create_cart(request)
    cart_items = cart_obj.items.select_related('variant__product').all()
    if not cart_items:
        messages.warning(request, 'سلة التسوق فارغة')
        return redirect('store:cart')
    return render(request, 'store/checkout.html', {'cart': cart_obj, 'cart_items': cart_items})


@require_POST
def place_order(request):
    cart_obj, _ = get_or_create_cart(request)
    cart_items = cart_obj.items.all()
    if not cart_items:
        return redirect('store:cart')

    phone = request.POST.get('phone', '').strip()
    if phone and not re.match(r'^0[567][0-9]{8}$', phone):
        messages.error(request, 'رقم الهاتف غير صالح. يجب أن يتكون من 10 أرقام ويبدأ بـ 05، 06، أو 07')
        return redirect('store:checkout')

    subtotal = sum(item.subtotal for item in cart_items)
    shipping = 0 if subtotal >= 200 else 25
    total = subtotal + shipping

    payment_stat = 'paid' if request.POST.get('payment_method') in ['card', 'apple_pay'] else 'pending'
    
    user = request.user if request.user.is_authenticated else None
    username = request.user.username if request.user.is_authenticated else request.POST.get('full_name')

    order = Order.objects.create(
        user=user, username=username,
        full_name=request.POST.get('full_name'), phone=phone,
        email=request.POST.get('email'), address=request.POST.get('address'),
        wilaya=request.POST.get('wilaya', ''), baladia=request.POST.get('baladia', ''),
        postal_code=request.POST.get('postal_code', ''), notes=request.POST.get('notes', ''),
        subtotal=subtotal, shipping_cost=shipping, total_amount=total,
        status='pending', payment_method=request.POST.get('payment_method', 'cod'),
        payment_status=payment_stat,
    )

    from django.core.mail import send_mail
    merchants_emails = set()

    for item in cart_items:
        product = item.variant.product
        OrderItem.objects.create(
            order=order, product=product, variant=item.variant,
            product_name=product.name, product_price=item.variant.price,
            quantity=item.quantity, subtotal=item.subtotal
        )
        
        if product.seller and product.seller.email:
            merchants_emails.add(product.seller.email)

    cart_items.delete()
    
    if merchants_emails:
        from django.template.loader import render_to_string
        from django.utils.formats import date_format
        from django.conf import settings
        from django.urls import reverse
        
        merchant_email_html = render_to_string('emails/merchant_order_email.html', {
            'order_number': order.order_number,
            'order_date': date_format(order.created_at, "d/m/Y H:i"),
            'dashboard_url': request.build_absolute_uri(reverse('store:merchant_dashboard')),
        })
        
        send_mail(
            subject=f'سوق - طلب جديد #{order.order_number}',
            message=f'لقد تم طلب منتجات من متجرك في الطلب رقم {order.order_number}.',
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
            recipient_list=list(merchants_emails),
            fail_silently=True,
            html_message=merchant_email_html
        )

    request.session['recent_order_id'] = order.pk

    if order.email:
        from django.template.loader import render_to_string
        from django.utils.formats import date_format
        from django.conf import settings
        
        status_display = order.get_status_display()
        items_html = ""
        for item in order.items.all():
            items_html += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e8e2d9;">{item.product_name}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e8e2d9; text-align: center;">{item.quantity}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e8e2d9; text-align: right;">{item.product_price} د.ج</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e8e2d9; text-align: right;">{item.subtotal} د.ج</td>
                </tr>
            """
        
        invoice_html = f"""
        <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; background: #F8F6F2;">
            <div style="background: white; border-radius: 16px; padding: 30px; border: 1px solid #E8E2D9;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #5C8A6E; font-size: 28px; margin: 0;">سوق</h1>
                    <p style="color: #7A7169; margin: 5px 0 0 0;">تم استلام طلبك بنجاح</p>
                </div>
                
                <div style="background: #EAF2EE; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h2 style="color: #5C8A6E; margin: 0 0 15px 0; font-size: 18px;">المعلومات الأساسية</h2>
                    <p style="margin: 5px 0; color: #2D2D2D;"><strong>رقم الطلب:</strong> {order.order_number}</p>
                    <p style="margin: 5px 0; color: #2D2D2D;"><strong>الحالة:</strong> {status_display}</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #5C8A6E; margin: 0 0 10px 0;">معلومات الشحن</h3>
                    <p style="margin: 5px 0; color: #2D2D2D;"><strong>الاسم:</strong> {order.full_name}</p>
                    <p style="margin: 5px 0; color: #2D2D2D;"><strong>الهاتف:</strong> {order.phone}</p>
                    <p style="margin: 5px 0; color: #2D2D2D;"><strong>العنوان:</strong> {order.address}, {order.wilaya}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background: #5C8A6E; color: white;">
                            <th style="padding: 12px; text-align: right;">المنتج</th>
                            <th style="padding: 12px; text-align: center;">الكمية</th>
                            <th style="padding: 12px; text-align: right;">السعر</th>
                            <th style="padding: 12px; text-align: right;">المجموع</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                
                <div style="text-align: left; margin-bottom: 30px;">
                    <p style="font-size: 18px; margin: 5px 0; color: #2D2D2D;"><strong>المجموع الفرعي:</strong> <span style="color: #5C8A6E;">{order.subtotal} د.ج</span></p>
                    <p style="font-size: 18px; margin: 5px 0; color: #2D2D2D;"><strong>تكلفة الشحن:</strong> <span style="color: #5C8A6E;">{order.shipping_cost} د.ج</span></p>
                    <h3 style="font-size: 22px; margin: 10px 0 0 0; color: #2D2D2D;"><strong>الإجمالي:</strong> <span style="color: #5C8A6E;">{order.total_amount} د.ج</span></h3>
                </div>
            </div>
        </div>
        """
        send_mail(
            subject=f'سوق - تم تأكيد طلبك #{order.order_number}',
            message=f'تم استلام طلبك رقم {order.order_number}. يمكنك تتبع طلبك عبر الموقع.',
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
            recipient_list=[order.email],
            fail_silently=True,
            html_message=invoice_html
        )

    messages.success(request, f'تم تأكيد طلبك بنجاح! رقم الطلب: {order.order_number}')
    return redirect('store:order_detail', pk=order.pk)


@login_required
def orders(request):
    current_status = request.GET.get('status', None)
    user_orders = Order.objects.filter(user=request.user)
    if current_status:
        user_orders = user_orders.filter(status=current_status)
    user_orders = user_orders.order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': user_orders, 'current_status': current_status})


def order_detail(request, pk):
    order = get_object_or_404(Order, id=pk)
    
    has_access = False
    if request.user.is_authenticated and order.user == request.user:
        has_access = True
    elif request.session.get('recent_order_id') == order.pk:
        has_access = True
    elif request.session.get('tracked_order_id') == order.pk:
        has_access = True
        
    if not has_access:
        messages.error(request, 'عذراً، لا تملك صلاحية الوصول إلى هذه الصفحة.')
        return redirect('store:home')
        
    my_num = 1
    if order.user and request.user.is_authenticated:
        my_num = Order.objects.filter(user=request.user, created_at__gt=order.created_at).count() + 1
        
    return render(request, 'store/order_detail.html', {'order': order, 'my_num': my_num})

def track_order(request):
    if request.method == 'POST':
        order_number = request.POST.get('order_number', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        if not order_number or not phone:
            messages.error(request, 'يرجى إدخال رقم الطلب والبحث المدخل بشكل صحيح.')
        else:
            try:
                order = Order.objects.get(order_number=order_number, phone=phone)
                request.session['tracked_order_id'] = order.pk
                messages.success(request, 'تم التحقق بنجاح من بيانات الطلب.')
                return redirect('store:order_detail', pk=order.pk)
            except Order.DoesNotExist:
                messages.error(request, 'عذراً، لم يتم العثور على طلب مطابق. تأكد من إدخال البيانات بشكل صحيح.')
    return render(request, 'store/track_order.html')


@login_required
def cancel_order(request, pk):
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, id=pk, user=request.user)
            if order.status != 'pending':
                return JsonResponse({'success': False, 'message': 'لا يمكن إلغاء هذا الطلب في حالته الحالية'})
            order.status = 'cancelled'
            order.payment_status = 'refunded' if order.payment_status == 'paid' else 'cancelled'
            
            # إرجاع المخزن إذا تم خصمه مسبقاً
            if order.stock_deducted:
                for item in order.items.all():
                    if item.variant:
                        item.variant.stock += item.quantity
                        item.variant.save()
                    if item.product:
                        item.product.sold_count = max(0, item.product.sold_count - item.quantity)
                        item.product.save()
                order.stock_deducted = False
                
            order.save()
            return JsonResponse({'success': True, 'message': 'تم إلغاء الطلب بنجاح'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'حدث خطأ: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'})


# ============================================
# MERCHANT VIEWS
# ============================================

@login_required
def merchant_dashboard(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
        return redirect('store:home')
    
    products_count = Product.objects.filter(seller=request.user).count()
    orders_items = OrderItem.objects.filter(product__seller=request.user)
    total_sales = orders_items.aggregate(total=Sum('subtotal'))['total'] or 0
    total_orders = orders_items.values('order').distinct().count()
    recent_orders = Order.objects.filter(items__product__seller=request.user).distinct().order_by('-created_at')[:5]
    
    return render(request, 'store/merchant_dashboard.html', {
        'products_count': products_count, 'total_sales': total_sales,
        'total_orders': total_orders, 'recent_orders': recent_orders,
    })


@login_required
def merchant_products(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
        return redirect('store:home')
    products = Product.objects.filter(seller=request.user).prefetch_related('variants')
    return render(request, 'store/merchant_products.html', {'products': products})




@login_required
def merchant_order_detail(request, pk):
    """تفاصيل طلب التاجر (يعرض منتجات التاجر فقط من هذا الطلب)"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'ليس لديك صلاحية الوصول')
        return redirect('store:home')
    
    # جلب الطلب بشرط أن يحتوي على منتج من هذا التاجر
    order = get_object_or_404(
        Order, 
        id=pk, 
        items__product__seller=request.user
    )
    
    # جلب منتجات التاجر فقط من هذا الطلب
    merchant_items = order.items.filter(product__seller=request.user)
    
    # حساب إجمالي أرباح التاجر من هذا الطلب
    merchant_subtotal = sum(item.subtotal for item in merchant_items)
    
    # حساب رقم الطلب في قائمة التاجر
    newer_orders_count = Order.objects.filter(
        items__product__seller=request.user,
        created_at__gt=order.created_at
    ).distinct().count()
    my_num = newer_orders_count + 1
    
    context = {
        'order': order,
        'merchant_items': merchant_items,
        'merchant_subtotal': merchant_subtotal,
        'my_num': my_num,
        'is_merchant_view': True,  # تفعيل وضع التاجر
    }
    return render(request, 'store/order_detail.html', context)

@login_required
def merchant_update_order_status(request, pk):
    """Update order status (Merchant AJAX)"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        return JsonResponse({'success': False, 'message': 'غير مصرح'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            tracking_number = data.get('tracking_number')
            
            valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned']
            if new_status not in valid_statuses:
                return JsonResponse({'success': False, 'message': 'حالة غير صالحة'})
            
            order = get_object_or_404(Order, id=pk, items__product__seller=request.user)
            order.status = new_status
            
            # حفظ رقم التتبع إذا تم إرساله
            if tracking_number:
                order.tracking_number = tracking_number
            
            # --- منطق خصم وإرجاع المخزن ---
            active_statuses = ['confirmed', 'processing', 'shipped', 'delivered']
            inactive_statuses = ['cancelled', 'returned']

            if new_status in active_statuses and not order.stock_deducted:
                # خصم الكمية من المخزن وزيادة عدد المبيعات
                for item in order.items.all():
                    if item.variant:
                        item.variant.stock = max(0, item.variant.stock - item.quantity)
                        item.variant.save()
                    if item.product:
                        item.product.sold_count += item.quantity
                        item.product.save()
                order.stock_deducted = True
            
            elif new_status in inactive_statuses and order.stock_deducted:
                # إرجاع الكمية للمخزن وإنقاص عدد المبيعات
                for item in order.items.all():
                    if item.variant:
                        item.variant.stock += item.quantity
                        item.variant.save()
                    if item.product:
                        item.product.sold_count = max(0, item.product.sold_count - item.quantity)
                        item.product.save()
                order.stock_deducted = False

            order.save()
            
            if order.email:
                status_dict = {
                    'pending': 'قيد الانتظار', 'confirmed': 'مؤكد', 'processing': 'قيد التجهيز',
                    'shipped': 'تم الشحن', 'delivered': 'تم التوصيل', 'cancelled': 'ملغي', 'returned': 'معاد'
                }
                ar_status = status_dict.get(new_status, new_status)
                from django.core.mail import send_mail
                send_mail(
                    subject=f'تحديث حالة الطلب: {order.order_number}',
                    message=f'مرحباً،\nتم تحديث حالة طلبك إلى: {ar_status}\nرقم التتبع: {order.tracking_number if order.tracking_number else "غير متوفر"}',
                    from_email=None,
                    recipient_list=[order.email],
                    fail_silently=True,
                )
            
            status_names = {
                'pending': 'قيد الانتظار', 'confirmed': 'مؤكد', 'processing': 'قيد التجهيز',
                'shipped': 'تم الشحن', 'delivered': 'تم التوصيل', 'cancelled': 'ملغي', 'returned': 'معاد'
            }
            
            return JsonResponse({
                'success': True,
                'message': f'تم تحديث حالة الطلب إلى: {status_names.get(new_status, new_status)}'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'})



@login_required
def merchant_orders(request):
    """صفحة طلبات التاجر"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'ليس لديك صلاحية الوصول')
        return redirect('store:home')
        
    current_status = request.GET.get('status')
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    sort = request.GET.get('sort', '-created_at')
    
    # جلب الطلبات الخاصة بالتاجر فقط
    merchant_orders = Order.objects.filter(
        items__product__seller=request.user
    ).distinct()
    
    # تطبيق الفلاتر
    if current_status:
        merchant_orders = merchant_orders.filter(status=current_status)
    if search:
        merchant_orders = merchant_orders.filter(
            Q(order_number__icontains=search) | 
            Q(full_name__icontains=search) | 
            Q(user__username__icontains=search)
        )
    if date_from:
        merchant_orders = merchant_orders.filter(created_at__date__gte=date_from)
    if date_to:
        merchant_orders = merchant_orders.filter(created_at__date__lte=date_to)
        
    merchant_orders = merchant_orders.order_by(sort)
    
    # Pagination (10 طلبات في كل صفحة)
    paginator = Paginator(merchant_orders, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # حساب الإحصائيات بدقة بناءً على الحالات في models.py
    stats_raw = Order.objects.filter(
        items__product__seller=request.user
    ).values('status').annotate(count=Count('id'))
    
    stats = {
        'total': sum(item['count'] for item in stats_raw),
        'pending': next((item['count'] for item in stats_raw if item['status'] == 'pending'), 0),
        'confirmed': next((item['count'] for item in stats_raw if item['status'] == 'confirmed'), 0),
        'processing': next((item['count'] for item in stats_raw if item['status'] == 'processing'), 0),
        'shipped': next((item['count'] for item in stats_raw if item['status'] == 'shipped'), 0),
        'delivered': next((item['count'] for item in stats_raw if item['status'] == 'delivered'), 0),
        'cancelled': next((item['count'] for item in stats_raw if item['status'] == 'cancelled'), 0),
    }
    
    context = {
        'orders': orders,
        'current_status': current_status,
        'stats': stats,
    }
    return render(request, 'store/merchant_orders.html', context)




@login_required
def product_create(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'ليس لديك صلاحية الوصول')
        return redirect('store:home')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            
            # ✅ معالجة brand
            brand_id = request.POST.get('brand')
            other_brand = request.POST.get('other_brand')
            
            if brand_id and brand_id != '' and brand_id != 'other':
                try:
                    product.brand_id = int(brand_id)
                except (ValueError, TypeError):
                    product.brand_id = None
            elif other_brand:
                obj, _ = Brand.objects.get_or_create(name=other_brand)
                product.brand = obj
            else:
                default_brand, _ = Brand.objects.get_or_create(
                    name='غير محدد', defaults={'name': 'غير محدد'}
                )
                product.brand = default_brand
            
            product.save()
            form.save_m2m()
            
            if request.FILES.get('video'):
                ProductVideo.objects.create(product=product, video=request.FILES['video'])

            specs_data = json.loads(request.POST.get('specs_data', '[]'))
            for spec in specs_data:
                ProductAttribute.objects.create(
                    product=product, 
                    name=spec.get('name'), 
                    value=spec.get('value')
                )

            # ✅ إنشاء المتغيرات مع صور مشتركة
            import random
            variant_keys = [
                key.replace('_combination', '') 
                for key in request.POST.keys() 
                if key.endswith('_combination')
            ]

            # الخطوة 1: إنشاء المتغيرات بدون صور
            created_variants = []
            for idx, key in enumerate(variant_keys):
                i = str(random.randint(10, 20))
                j = str(random.randint(1, 10))
                combination = json.loads(request.POST.get(f'{key}_combination', '{}'))
                price = float(request.POST.get(f'{key}_price', 0))
                old_price = float(request.POST.get(f'{key}_old_price', 0)) or None
                stock = int(request.POST.get(f'{key}_stock', 0))
                sku = request.POST.get(f'{key}_sku', f'{product.sku}-{i},{j}')
                image_file = request.FILES.get(f'{key}_image')
                is_main = request.POST.get('is_main') == key
                
                variant = ProductVariant.objects.create(
                    product=product,
                    name=' / '.join(combination.values()),
                    sku=sku or f'{product.id}-V{idx+1}',
                    price=price,
                    old_price=old_price,
                    stock=stock,
                    is_main=is_main,
                    attributes=combination
                )
                if old_price and old_price > price:
                    variant.discount = int(((old_price - price) / old_price) * 100)
                    variant.save(update_fields=['discount'])
                
                created_variants.append({
                    'variant': variant,
                    'combination': combination,
                    'image_file': image_file,
                    'is_main': is_main,
                })

            # الخطوة 2: تجميع الصور حسب المحتوى (Deduplication by Hash) لضمان عدم تكرار الملفات
            hash_to_vi = {}
            first_image_created = False

            for item in created_variants:
                variant = item['variant']
                image_file = item['image_file']

                if image_file:
                    # حساب الهاش للملف للتأكد من عدم تكراره وتقليل مساحة التخزين
                    hasher = hashlib.md5()
                    for chunk in image_file.chunks():
                        hasher.update(chunk)
                    f_hash = hasher.hexdigest()

                    if f_hash in hash_to_vi:
                        variant_image = hash_to_vi[f_hash]
                    else:
                        variant_image = VariantImage.objects.create(
                            product=product,
                            image=image_file,
                            is_main=(not first_image_created),
                        )
                        hash_to_vi[f_hash] = variant_image
                        first_image_created = True

                    # ربط المتغير بالصورة
                    variant_image.variants.add(variant)

            messages.success(request, 'تم إنشاء المنتج بنجاح')
            return redirect('store:merchant_products')
    else:
        form = ProductForm()
    
    return render(request, 'store/product_form.html', {
        'form': form,
        'categories': Category.objects.filter(is_active=True),
        'brands': Brand.objects.all(),
    })


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()

            # ✅ التعامل مع العلامة التجارية
            brand_val = request.POST.get('brand')
            other_brand = request.POST.get('other_brand')
            
            if brand_val and brand_val != '' and brand_val != 'other':
                if brand_val.isdigit():
                    product.brand_id = int(brand_val)
                else:
                    brand_obj, _ = Brand.objects.get_or_create(
                        name=brand_val,
                        defaults={'slug': slugify(brand_val)}
                    )
                    product.brand = brand_obj
            elif other_brand:
                obj, _ = Brand.objects.get_or_create(name=other_brand)
                product.brand = obj
            else:
                product.brand = None
            product.save(update_fields=['brand'])

            specs_data = json.loads(request.POST.get('specs_data', '[]'))
            if specs_data:
                ProductAttribute.objects.filter(product=product).delete()
                for spec in specs_data:
                    ProductAttribute.objects.create(
                        product=product,
                        name=spec.get('name'),
                        value=spec.get('value')
                    )

            # ✅ تحديث المتغيرات مع الحفاظ على الصور القديمة
            variant_keys = [
                key.replace('_combination', '') 
                for key in request.POST.keys() 
                if key.endswith('_combination')
            ]

            if variant_keys:
                # حفظ خريطة الصور القديمة قبل الحذف
                # first_attr_value -> VariantImage
                old_image_map = {}
                for v in product.variants.all():
                    attrs = v.attributes if isinstance(v.attributes, dict) else {}
                    first_attr = list(attrs.values())[0] if attrs else None
                    if first_attr and first_attr not in old_image_map:
                        try:
                            old_img = (
                                v.images.filter(is_main=True).first() 
                                or v.images.first()
                            )
                        except:
                            old_img = None
                        if old_img:
                            old_image_map[first_attr] = old_img

                # حذف المتغيرات القديمة (الربط M2M يزول تلقائياً)
                product.variants.all().delete()

                # إنشاء المتغيرات الجديدة
                import random
                created_variants = []
                for idx, key in enumerate(variant_keys):
                    combination = json.loads(request.POST.get(f'{key}_combination', '{}'))
                    price = float(request.POST.get(f'{key}_price', 0))
                    old_price = float(request.POST.get(f'{key}_old_price', 0)) or None
                    stock = int(request.POST.get(f'{key}_stock', 0))
                    sku = request.POST.get(f'{key}_sku', '')
                    image_file = request.FILES.get(f'{key}_image')
                    is_main = request.POST.get('is_main') == key

                    variant = ProductVariant.objects.create(
                        product=product,
                        name=' / '.join(combination.values()),
                        sku=sku or f'{product.id}-V{idx+1}',
                        price=price,
                        old_price=old_price,
                        stock=stock,
                        is_main=is_main,
                        attributes=combination
                    )
                    if old_price and old_price > price:
                        variant.discount = int(((old_price - price) / old_price) * 100)
                        variant.save(update_fields=['discount'])

                    created_variants.append({
                        'variant': variant,
                        'combination': combination,
                        'image_file': image_file,
                        'is_main': is_main,
                        'key': key,  # إضافة المفتاح لاسترجاع البيانات الإضافية من POST
                    })

                # ربط الصور: الجديدة أولاً (بالاعتماد على الهاش) ثم القديمة كبديل
                hash_to_vi = {}
                first_image_created = VariantImage.objects.filter(product=product, is_main=True).exists()

                for item in created_variants:
                    variant = item['variant']
                    combination = item['combination']
                    image_file = item['image_file']
                    key = item['key']
                    
                    # محاولة جلب معرف الصورة القديم من الطلب
                    existing_img_id = request.POST.get(f'{key}_image_id')

                    if image_file:
                        # جلب هاش الصورة الجديدة لمنع التكرار
                        hasher = hashlib.md5()
                        for chunk in image_file.chunks():
                            hasher.update(chunk)
                        f_hash = hasher.hexdigest()

                        if f_hash in hash_to_vi:
                            variant_image = hash_to_vi[f_hash]
                        else:
                            variant_image = VariantImage.objects.create(
                                product=product,
                                image=image_file,
                                is_main=(not first_image_created),
                            )
                            hash_to_vi[f_hash] = variant_image
                            first_image_created = True
                        
                        variant_image.variants.add(variant)
                    
                    elif existing_img_id and str(existing_img_id).isdigit():
                        # استخدام الصورة القديمة بناءً على المعرف الصريح (الأكثر دقة)
                        try:
                            old_img = VariantImage.objects.get(id=existing_img_id, product=product)
                            old_img.variants.add(variant)
                        except VariantImage.DoesNotExist:
                            pass
                    
                    else:
                        # محاولة أخيرة بناءً على الخاصية الأولى (للخلف)
                        first_attr_value = (
                            list(combination.values())[0]
                            if combination else None
                        )
                        if first_attr_value and first_attr_value in old_image_map:
                            old_img = old_image_map[first_attr_value]
                            old_img.variants.add(variant)

                # حذف الصور اليتيمة (غير مربوطة بأي متغير)
                from django.db.models import Count
                VariantImage.objects.filter(
                    product=product
                ).annotate(
                    v_count=Count('variants')
                ).filter(v_count=0).delete()

            messages.success(request, 'تم تحديث المنتج بنجاح')
            return redirect('store:merchant_products')

    else:
        form = ProductForm(instance=product)

    # ✅ تجهيز بيانات الخيارات القديمة
    existing_options = {}
    for variant in product.variants.all():
        attrs = variant.attributes if isinstance(variant.attributes, dict) else {}
        for key, val in attrs.items():
            if key not in existing_options:
                existing_options[key] = set()
            existing_options[key].add(val)

    options_json = json.dumps(
        [{"name": k, "values": list(v)} for k, v in existing_options.items()],
        ensure_ascii=False
    )
    # ✅ تجهيز بيانات المتغيرات القديمة
    existing_variants = []
    for idx, v in enumerate(product.variants.all()):
        # جلب أول صورة مرتبطة بهذا المتغير
        img_obj = v.images.first()
        img_id = img_obj.id if img_obj else None
        img_url = img_obj.image.url if img_obj else 'https://placehold.co/600x600/F0EBE3/5C8A6E?text=No+Image'

        existing_variants.append({
            "key": f"v_{idx}",
            "sku": v.sku or "",
            "price": str(v.price),
            "old_price": str(v.old_price) if v.old_price else "",
            "stock": v.stock,
            "is_main": v.is_main,
            "image_id": img_id,
            "image_url": img_url,
        })

    # ✅ تجهيز المواصفات القديمة
    specs_list = list(
        ProductAttribute.objects.filter(product=product).values('name', 'value')
    )
    
    return render(request, 'store/product_form.html', {
        'form': form,
        'product': product,
        'categories': Category.objects.filter(is_active=True),
        'brands': Brand.objects.all(),
        'video': ProductVideo.objects.filter(product=product).first(),
        'variants': product.variants.all(),
        'specs_json': json.dumps(specs_list, ensure_ascii=False),
        'options_json': options_json,
        'existing_variants_json': json.dumps(existing_variants, ensure_ascii=False),
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        product.delete() # ستحذف المتغيرات والصور تلقائياً لو وضعت on_delete=CASCADE في الموديلز
        messages.success(request, 'تم حذف المنتج بنجاح')
        return redirect('store:merchant_products')
    return render(request, 'store/product_confirm_delete.html', {'product': product})

# ============================================
# WISHLIST VIEWS - النسخة المصححة نهائياً ومتوافقة مع الموديلز
# ============================================

def get_or_create_wishlist(request):
    """الحصول على أو إنشاء قائمة المفضلة للمستخدم"""
    if not request.user.is_authenticated:
        return None
    
    # ✅ استخدام filter و first بدلاً من get_or_create لتجنب خطأ التكرار
    # سنأخذ أحدث سجل (بناءً على الـ ID) إذا وُجد أكثر من واحد
    wishlist_obj = Wishlist.objects.filter(user=request.user).order_by('-id').first()
    
    if not wishlist_obj:
        wishlist_obj = Wishlist.objects.create(user=request.user)
        
    return wishlist_obj


# ============================================
# WISHLIST VIEWS - متوافق تماماً مع هيكل الموديلز
# ============================================

def wishlist(request):
    """صفحة المفضلة"""
    if request.user.is_authenticated:
        # ✅ جلب العناصر عبر الـ user مباشرة (بدون إنشاء مفضلة فارغة)
        wishlist_items = WishlistItem.objects.filter(
            wishlist__user=request.user
        ).select_related('variant__product', 'wishlist__product')
        
        for item in wishlist_items:
            variant = item.variant
            if not variant:
                continue
            product = variant.product
            
            # جلب كل متغيرات نفس المنتج
            all_variants = ProductVariant.objects.filter(product=product)

            # === بناء attr_map بنفس طريقة السلة ===
            attr_map = {}
            # صورة المتغير الحالي
            main_img = variant.images.filter(is_main=True).first() or variant.images.first()
            item.variant_image = main_img.image.url if main_img else (product.image.url if product.image else None)
            
            for v in all_variants:
                raw_attrs = v.attributes if isinstance(v.attributes, dict) else {}

                for attr_name, attr_value in raw_attrs.items():
                    if isinstance(attr_value, dict):
                        actual_value = attr_value.get('value', str(attr_value))
                    else:
                        actual_value = str(attr_value)

                    if attr_name not in attr_map:
                        attr_map[attr_name] = {}

                    if actual_value not in attr_map[attr_name]:
                        v_img = v.images.filter(is_main=True).first() or v.images.first()
                        attr_map[attr_name][actual_value] = {
                            'value': actual_value,
                            'variant_id': v.id,
                            'price': str(v.price),
                            'old_price': str(v.old_price) if v.old_price else None,
                            'discount': v.discount or 0,
                            'stock': v.stock,
                            'sku': v.sku,
                            'image': v_img.image.url if v_img else (product.image.url if product.image else None),
                        }

            # === استخراج القيم الحالية للمتغير المختار ===
            current_raw = variant.attributes if isinstance(variant.attributes, dict) else {}
            clean_current = {}
            for attr_name, attr_value in current_raw.items():
                if isinstance(attr_value, dict):
                    clean_current[attr_name] = attr_value.get('value', str(attr_value))
                else:
                    clean_current[attr_name] = str(attr_value)

            # === بناء القائمة النهائية لكل خاصية ===
            variant_attributes = []
            for attr_name, values in attr_map.items():
                current_value = clean_current.get(attr_name, '')

                options = []
                for val_data in values.values():
                    option = dict(val_data)
                    option['current'] = (option['value'] == current_value)
                    options.append(option)

                variant_attributes.append({
                    'name': attr_name,
                    'value': current_value,
                    'options': options,
                })

            item.variant_attributes = variant_attributes

        context = {
            'wishlist_items': wishlist_items,
        }
        return render(request, 'store/wishlist.html', context)
    else:
        messages.info(request, 'يرجى تسجيل الدخول لعرض قائمة المنتجات المفضلة')
        return redirect('accounts:login')


def wishlist_count(request):
    """عدد عناصر المفضلة (AJAX)"""
    try:
        if request.user.is_authenticated:
            count = WishlistItem.objects.filter(wishlist__user=request.user).count()
        else:
            count = 0
        return JsonResponse({'success': True, 'count': count})
    except Exception:
        return JsonResponse({'success': False, 'count': 0})


@require_POST
def toggle_wishlist(request):
    """إضافة/حذف من المفضلة (AJAX) - مصحح لتوافق الـ Property"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'يرجى تسجيل الدخول',
                'redirect': '/login/'
            })

        product = get_object_or_404(Product, pk=product_id, is_active=True)
        
        # ✅ منع صاحب المنتج من إضافة منتجه للمفضلة
        if product.seller == request.user:
            return JsonResponse({
                'success': False,
                'message': 'لا يمكنك إضافة منتجك الخاص إلى المفضلة'
            })
        
        if variant_id:
            variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
        else:
            variant = get_default_variant(product)

        wishlist_item = WishlistItem.objects.filter(
            wishlist__user=request.user, 
            variant=variant
        ).first()

        if wishlist_item:
            # ✅ موجود -> حذفه وحذف الأب أيضاً لمنع خطأ التكرار لاحقاً
            parent_wishlist = wishlist_item.wishlist
            wishlist_item.delete()
            if parent_wishlist and not parent_wishlist.items.exists():
                parent_wishlist.delete()
                
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': 'تم إزالة المنتج من المفضلة',
                'wishlist_count': WishlistItem.objects.filter(wishlist__user=request.user).count()
            })
        else:
            # ✅ غير موجود -> إنشاء الأب باستخدام get_or_create لمنع التكرار
            wishlist_obj, _ = Wishlist.objects.get_or_create(
                user=request.user, 
                product=product
            )
            
            # ✅ عدم إرسال product= هنا لأنه يتعارض مع @property في الموديل
            WishlistItem.objects.create(
                wishlist=wishlist_obj,
                variant=variant,
                quantity=1
            )
            return JsonResponse({
                'success': True,
                'action': 'added',
                'message': 'تمت إضافة المنتج للمفضلة',
                'wishlist_count': WishlistItem.objects.filter(wishlist__user=request.user).count()
            })

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'المنتج غير موجود'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'حدث خطأ: {str(e)}'})


def remove_from_wishlist(request):
    """حذف من المفضلة (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            variant_id = data.get('variant_id')
            
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'message': 'يرجى تسجيل الدخول'})

            if not variant_id:
                return JsonResponse({'success': False, 'message': 'معرف غير صالح'})

            wishlist_item = WishlistItem.objects.filter(
                wishlist__user=request.user, 
                variant_id=variant_id
            ).first()

            if wishlist_item:
                # ✅ حذف العنصر وحذف الأب أيضاً
                parent_wishlist = wishlist_item.wishlist
                wishlist_item.delete()
                if parent_wishlist and not parent_wishlist.items.exists():
                    parent_wishlist.delete()
                    
                return JsonResponse({
                    'success': True,
                    'action': 'removed',
                    'message': 'تم إزالة المنتج من المفضلة',
                    'wishlist_count': WishlistItem.objects.filter(wishlist__user=request.user).count()
                })
            else:
                return JsonResponse({'success': False, 'message': 'المنتج غير موجود في المفضلة'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'حدث خطأ: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'طلب غير صالح'})


def update_wishlist(request):
    """تحديث كمية المنتج في المفضلة (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity', 1))
            
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'message': 'يرجى تسجيل الدخول'})
            
            if not variant_id:
                return JsonResponse({'success': False, 'message': 'معرف غير صالح'})

            wishlist_item = WishlistItem.objects.filter(
                wishlist__user=request.user, 
                variant_id=variant_id
            ).first()
            
            if not wishlist_item:
                return JsonResponse({'success': False, 'message': 'العنصر غير موجود'})
            
            if quantity > 0:
                if quantity > wishlist_item.variant.stock:
                    return JsonResponse({'success': False, 'message': f'الكمية المتوفرة: {wishlist_item.variant.stock}'})
                wishlist_item.quantity = quantity
                wishlist_item.save()
            else:
                # ✅ إذا كانت الكمية 0، نحذف العنصر والأب
                parent_wishlist = wishlist_item.wishlist
                wishlist_item.delete()
                if parent_wishlist and not parent_wishlist.items.exists():
                    parent_wishlist.delete()
                
            return JsonResponse({
                'success': True,
                'message': 'تم التحديث',
                'wishlist_count': WishlistItem.objects.filter(wishlist__user=request.user).count()
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'طلب غير صالح'})


@require_POST
def update_wishlist_variant(request):
    """تحديث متغير المنتج في المفضلة (AJAX)"""
    try:
        data = json.loads(request.body)
        current_variant_id = data.get('current_variant_id')
        new_variant_id = data.get('new_variant_id')

        if not current_variant_id or not new_variant_id:
            return JsonResponse({'error': 'بيانات ناقصة'}, status=400)

        if str(current_variant_id) == str(new_variant_id):
            return JsonResponse({'success': True})

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'يرجى تسجيل الدخول'}, status=401)

        # عنصر المفضلة الحالي
        wishlist_item = WishlistItem.objects.filter(
            wishlist__user=request.user, 
            variant_id=current_variant_id
        ).first()

        if not wishlist_item:
            return JsonResponse({'error': 'العنصر غير موجود في المفضلة'}, status=404)

        # المتغير الجديد
        new_variant = ProductVariant.objects.select_related('product').get(
            id=new_variant_id
        )

        # التحقق أنه نفس المنتج
        if new_variant.product_id != wishlist_item.variant.product_id:
            return JsonResponse({'error': 'متغير غير صالح'})

        # هل المتغير الجديد موجود أصلاً في المفضلة؟
        existing_item = WishlistItem.objects.filter(
            wishlist__user=request.user, 
            variant_id=new_variant_id
        ).first()

        if existing_item:
            # إذا كان موجوداً، نحذف الحالي لأننا لا نريد تكرار نفس المتغير في المفضلة
            wishlist_item.delete()
        else:
            wishlist_item.variant = new_variant
            wishlist_item.save(update_fields=['variant'])

        return JsonResponse({'success': True})

    except WishlistItem.DoesNotExist:
        return JsonResponse({'error': 'العنصر غير موجود'}, status=404)
    except ProductVariant.DoesNotExist:
        return JsonResponse({'error': 'المتغير غير موجود'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def upload_video(request):
    if request.method == 'POST' and request.FILES.get('video'):
        video = request.FILES['video']

        obj = ProductVideo.objects.create(video=video)

        return JsonResponse({
            'success': True,
            'video_id': obj.id,
            'url': obj.video.url
        })

    return JsonResponse({'success': False})


@csrf_exempt
def delete_product_video(request, pk):
    try:
        video = ProductVideo.objects.get(pk=pk)
        video.delete()
        return JsonResponse({'success': True})
    except ProductVideo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'الفيديو غير موجود'})

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




# تم حذف دوال variant_create, variant_update, variant_update, get_category_attributes 
# لأنها غير متوافقة مع نظام الـ JSONField وتم استبدال منطقها داخل product_create و product_update

def handler404_view(request, exception=None):
    return error_view(request, 404)


def handler500_view(request):
    return error_view(request, 500)


def handler403_view(request, exception=None):
    return error_view(request, 403)


def handler400_view(request, exception=None):
    return error_view(request, 400)

from django.db.models import Sum, Count, Q

# ============================================
# ADMIN PANEL VIEWS
# ============================================

@login_required
def admin_dashboard(request):
    """لوحة تحكم الأدمن الشاملة"""
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
        return redirect('store:home')
    
    # جلب المستخدمين المسجلين مع بيانات الملف الشخصي
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    
    # جلب الزوار (طلبات بدون مستخدم مسجل)
    guest_orders = Order.objects.filter(user__isnull=True).values('email', 'full_name').annotate(
        orders_count=Count('id')
    ).order_by('-orders_count')

    # إحصائيات عامة
    total_sellers = users.filter(profile__is_seller=True).count()
    total_buyers = users.filter(profile__is_seller=False).count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # آخر الطلبات في النظام
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    context = {
        'users': users,
        'guest_orders': guest_orders,
        'total_sellers': total_sellers,
        'total_buyers': total_buyers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    return render(request, 'store/admin_dashboard.html', context)


@login_required
def admin_user_detail(request, user_id):
    """صفحة تفاصيل المستخدم (تاجر أو مشتري) للأدمن"""
    if not request.user.is_superuser:
        return redirect('store:home')
        
    target_user = get_object_or_404(User.objects.select_related('profile'), pk=user_id)
    profile = target_user.profile
    
    context = {
        'target_user': target_user,
        'profile': profile,
    }
    
    if profile.is_seller:
        # بيانات التاجر
        products = Product.objects.filter(seller=target_user)
        merchant_orders_items = OrderItem.objects.filter(product__seller=target_user)
        seller_revenue = merchant_orders_items.aggregate(Sum('subtotal'))['subtotal__sum'] or 0
        seller_products_count = products.count()
        
        context.update({
            'products': products,
            'merchant_orders_items': merchant_orders_items[:20],
            'seller_revenue': seller_revenue,
            'seller_products_count': seller_products_count,
        })
    else:
        # بيانات المشتري
        buyer_orders = Order.objects.filter(user=target_user).order_by('-created_at')
        total_spent = buyer_orders.filter(payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        context.update({
            'buyer_orders': buyer_orders,
            'total_spent': total_spent,
        })
        
    return render(request, 'store/admin_user_detail.html', context)


@login_required
@require_POST
def admin_delete_user(request, user_id):
    """حذف مستخدم (تاجر/مشتري) من قبل الأدمن"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'غير مصرح'})
    try:
        user = get_object_or_404(User, pk=user_id)
        if user == request.user:
            return JsonResponse({'success': False, 'message': 'لا يمكنك حذف حسابك الخاص'})
        user.delete()
        return JsonResponse({'success': True, 'message': 'تم حذف المستخدم وجميع بياناته بنجاح'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def admin_delete_product(request, product_id):
    """حذف منتج معين من قبل الأدمن"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'غير مصرح'})
    try:
        product = get_object_or_404(Product, pk=product_id)
        product.delete()
        return JsonResponse({'success': True, 'message': 'تم حذف المنتج بنجاح'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
    

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.shortcuts import redirect

def send_help(request):
    if request.method == "POST":
        issue_type = request.POST.get('issue_type')
        description = request.POST.get('description')
        page_url = request.POST.get('page_url')

        # بيانات المرسل (إذا كان مسجل دخول)
        user = request.user if request.user.is_authenticated else None
        username = user.username if user else "زائر"
        email = user.email if user else "غير متوفر"
        issue_map = {
            "bug": "خطأ تقني",
            "payment": "مشكلة في الدفع",
            "order": "مشكلة في الطلب",
            "account": "مشكلة في الحساب",
            "other": "أخرى",
        }

        issue_type = issue_map.get(issue_type, issue_type)
        # توليد HTML
        html_message = render_to_string('emails/support_email.html', {
            'username': username,
            'email': email,
            'issue_type': issue_type,
            'description': description,
            'page_url': page_url,
        })

        plain_message = strip_tags(html_message)

        send_mail(
            subject="🛠️ طلب مساعدة جديد",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['souqsupport@gmail.com'],
            html_message=html_message,
        )

    return redirect(request.META.get('HTTP_REFERER', '/'))