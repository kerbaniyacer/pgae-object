import time
import random
import json
import re
import uuid
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from allauth.socialaccount.models import SocialLogin
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.core.files.base import ContentFile
from .models import Profile
from store.models import Category
from .forms import LoginForm, CompleteProfileForm, UserTypeForm, RegisterForm, ProfileForm
import requests

WILAYAS = [
    ("01", "أدرار"),
    ("02", "الشلف"),
    ("03", "الأغواط"),
    ("04", "أم البواقي"),
    ("05", "باتنة"),
    ("06", "بجاية"),
    ("07", "بسكرة"),
    ("08", "بشار"),
    ("09", "البليدة"),
    ("10", "البويرة"),
    ("11", "تمنراست"),
    ("12", "تبسة"),
    ("13", "تلمسان"),
    ("14", "تيارت"),
    ("15", "تيزي وزو"),
    ("16", "الجزائر"),
    ("17", "الجلفة"),
    ("18", "جيجل"),
    ("19", "سطيف"),
    ("20", "سعيدة"),
    ("21", "سكيكدة"),
    ("22", "سيدي بلعباس"),
    ("23", "عنابة"),
    ("24", "قالمة"),
    ("25", "قسنطينة"),
    ("26", "المدية"),
    ("27", "مستغانم"),
    ("28", "المسيلة"),
    ("29", "معسكر"),
    ("30", "ورقلة"),
    ("31", "وهران"),
    ("32", "البيض"),
    ("33", "إليزي"),
    ("34", "برج بوعريريج"),
    ("35", "بومرداس"),
    ("36", "الطارف"),
    ("37", "تندوف"),
    ("38", "تيسمسيلت"),
    ("39", "الوادي"),
    ("40", "خنشلة"),
    ("41", "سوق أهراس"),
    ("42", "تيبازة"),
    ("43", "ميلة"),
    ("44", "عين الدفلى"),
    ("45", "النعامة"),
    ("46", "عين تموشنت"),
    ("47", "غرداية"),
    ("48", "غليزان"),
    ("49", "تيميمون"),
    ("50", "برج باجي مختار"),
    ("51", "أولاد جلال"),
    ("52", "بني عباس"),
    ("53", "عين صالح"),
    ("54", "عين قزام"),
    ("55", "تقرت"),
    ("56", "جانت"),
    ("57", "المغير"),
    ("58", "المنيعة"),
]
# Create your views here.
# ============================================
# ACCOUNT VIEWS
# ============================================
from allauth.socialaccount.models import SocialAccount

def is_google_user(user):
    return SocialAccount.objects.filter(user=user, provider='google').exists()

def login_view(request):
    """
    Login view with OTP verification:
    Step 1: Show username/email and password fields
    Step 2: After clicking login, send OTP and show verification code field
    Step 3: Verify OTP and complete login
    """
    request.session.pop('sociallogin', None)  # Clear any previous social login data from session
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
                return redirect('accounts:login')
            
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
                    if not is_google_user(user):
                        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    else:
                        login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
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
                return redirect('accounts:login')
        
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


User = get_user_model()
def register(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('store:home')
    user_type = request.GET.get('type')
    # Step 1: Choose account type
    if request.method == 'POST' and 'choose_type' in request.POST :
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
                

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'تم إنشاء الحساب وتسجيل الدخول بنجاح')
                # Send welcome email
                send_registration_confirmation(to_email=user.email, username=user.username)
                
                return redirect('store:home')
            else:
                # التحقق الإضافي من الأخطاء في الفورم
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
        else:
            form = RegisterForm(initial={'user_type': user_type})

        return render(request, 'accounts/register.html', {
            'form': form,
            'user_type': user_type,
            'store_categories': Category.objects.filter(is_active=True, parent=None), # عرض بعض الفئات في الخلفية 
            'wilayas': WILAYAS,  
        })
    # Display type selection
    type_form = UserTypeForm()
    return render(request, 'accounts/register.html', {
        'type_form': type_form,
        'store_categories': Category.objects.filter(is_active=True, parent=None),
        'wilayas': WILAYAS,
    })

def complete_profile(request):
    """Complete user profile after registration"""
    if request.user.is_authenticated and not request.session.get('sociallogin'):
        return redirect('store:home')
    user_type = request.GET.get('type')
    sociallogin_data =  request.session.get('sociallogin') or None
    if request.method == 'POST' and 'choose_type' in request.POST and not user_type:
        type_form = UserTypeForm(request.POST)
        if type_form.is_valid():
            selected = type_form.cleaned_data['user_type']
            return redirect(f"{request.path}?type={selected}")
        return render(request, 'accounts/register.html', {'type_form': type_form})
    # Debugging line to check if sociallogin data is present
    if user_type in ['customer', 'seller']: 

        if request.method == 'POST' and sociallogin_data:
    
            form = CompleteProfileForm(request.POST, request.FILES, user_type=user_type)
            if form.is_valid():
                sociallogin = SocialLogin.deserialize(sociallogin_data)
                account = sociallogin_data.get('account', {})
                extra = account.get('extra_data', {})
                email = extra.get('email')
                name = extra.get('name')
                picture = extra.get('picture')
                user_data = sociallogin_data.get('user', {})
                first_name = user_data.get('first_name')
                last_name = user_data.get('last_name')
                
                base_username = email.split('@')[0]
                username = base_username

                from django.utils.crypto import get_random_string

                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{get_random_string(4)}"


                # إنشاء المستخدم
                name_parts = name.split(' ', 1) if name else ['', '']
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name or (name_parts[0] if name_parts else ''),
                    last_name=last_name or (name_parts[1] if len(name_parts) > 1 else ''),
                )
                user.set_unusable_password()
                user.save()
                profile = Profile.objects.create(
                    user=user,
                    is_seller=(user_type == 'seller'),
                    phone=form.cleaned_data.get('phone', ''),
                    wilaya=form.cleaned_data.get('wilaya', ''),
                    baladia=form.cleaned_data.get('baladia', ''),
                )

                # فقط للبائع
                if user_type == 'seller':
                    profile.store_name = form.cleaned_data.get('store_name', '')
                    profile.store_description = form.cleaned_data.get('store_description', '')
                    profile.store_category = form.cleaned_data.get('store_category')
                    profile.store_logo = form.cleaned_data.get('store_logo')
                    profile.commercial_register = form.cleaned_data.get('commercial_register', '')
                    profile.save()
                image_url = picture
                try:
                    if image_url:
                        response = requests.get(image_url, timeout=5)
                        response.raise_for_status()
                        file_name = f"profile_{get_random_string(8)}.jpg"
                        profile.photo = ContentFile(response.content, name=file_name)
                        profile.save()

                except requests.exceptions.RequestException:
                    pass
                # ✅ بيانات من Google

                # ✅ إنشاء Profile مرة واحدة فقط
                
                # ✅ ربط حساب Google
                sociallogin.connect(request, user)
                request.session.pop('sociallogin', None)
                login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
                send_registration_confirmation(to_email=user.email, username=user.username)
                messages.success(request, 'تم إنشاء الحساب وتسجيل الدخول بنجاح')
                return redirect('store:home')
            else:
                # التحقق الإضافي من الأخطاء في الفورم
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
        else:
            form = CompleteProfileForm(initial={'user_type': user_type})
        return render(request, 'accounts/complete_profile.html', {
            'form': form,
            'user_type': user_type,
            'store_categories': Category.objects.filter(is_active=True),  # عرض بعض الفئات في الخلفية 
            'wilayas': WILAYAS,  
        })
    type_form = UserTypeForm()
    return render(request, 'accounts/complete_profile.html', {
        'type_form': type_form,
        'store_categories': Category.objects.filter(is_active=True),
        'wilayas': WILAYAS,
    })



@login_required
def profile(request):
    """User profile page"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'accounts/profile.html', {'form': form , 'wilayas': WILAYAS})


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        # Check if this is step 1 (change_password) or step 2 (OTP verification)
        otp_sent = request.POST.get('otp_sent') == 'true'
        
        if otp_sent:
            # Step 2: Verify OTP
            code_verification = request.POST.get('code_verification', '').strip()
            if not code_verification:
                messages.error(request, 'يرجى إدخال رمز التحقق')
                masked_email = request.session.get('login_user_email', '')
                return render(request, 'accounts/change_password.html', {
                    'form': form, 
                    'otp_sent': True,
                    'user_email': masked_email
                })
            try: 
                if verify_otp_code(request.user.email, code_verification):
                    # OTP is valid, proceed with password change
                    if form.is_valid():
                        user = form.save()
                        update_session_auth_hash(request, user)
                        messages.success(request, 'تم تغيير كلمة المرور بنجاح')
                        
                        # Send notification email
                        password_change_notification(to_email=request.user.email, username=request.user.username)
                        logout(request)
                        return redirect('accounts:login')
                    else:
                        messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
                else:
                    messages.error(request, 'رمز التحقق غير صحيح أو منتهي الصلاحية')
                    masked_email = mask_email(request.user.email)
                    return render(request, 'accounts/change_password.html', {
                        'form': form, 
                        'otp_sent': True,
                        'user_email': masked_email
                    })
            except Exception as e:
                messages.error(request, 'حدث خطأ، يرجى المحاولة مرة أخرى')
                return redirect('accounts:change_password')
        else:
            # Step 1: Send OTP for password change verification
            cache_key = f'otp_rate_limit_{request.user.email}'
            if cache.get(cache_key):
                messages.warning(request, 'يرجى الانتظار 60 ثانية قبل طلب رمز جديد')
                masked_email = mask_email(request.user.email)
                return render(request, 'accounts/change_password.html', {
                    'form': form,
                    'otp_sent': True,
                    'user_email': masked_email
                })
            
            # Validate form first before sending OTP
            if form.is_valid():
                send_otp_email(to_email=request.user.email, username=request.user.username)
                cache.set(cache_key, True, 60)
                request.session['login_user_email'] = mask_email(request.user.email)
                messages.info(request, 'تم إرسال رمز التحيق إلى بريدك الإلكتروني')
                return render(request, 'accounts/change_password.html', {
                    'form': form,
                    'otp_sent': True,
                    'user_email': mask_email(request.user.email)
                })
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
                reverse('accounts:reset_password', kwargs={'uidb64': uid, 'token': token})
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
        return redirect('accounts:forgot_password')
    
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
                'message': 'يرجى الانتظار 60 ثانية قبل طلب رمز جديد'
            })
        
        # Send OTP
        send_otp_email(to_email=user.email, username=user.username)
        
        # Set rate limit
        cache.set(cache_key, True, 60)
        
        # Update session timestamp
        request.session['login_timestamp'] = int(time.time())
        
        return JsonResponse({
            'success': True,
            'message': 'تم إرسال رمز التحقق إلى بريدك الإلكتروني',
            'user_email': mask_email(user.email)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ، يرجى المحاولة مرة أخرى'
        })


# ============================================
# HELPER FUNCTIONS
# ============================================

def mask_email(email):
    """Mask email for display"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '***' + local[-1]
    
    return f"{masked_local}@{domain}"


def generate_otp_code():
    """Generate 6-digit OTP code"""
    import random
    return str(random.randint(100000, 999999))


def send_otp_email(to_email, username):
    """Send OTP verification email"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    otp_code = generate_otp_code()
    
    # Store OTP in cache with 10 minutes expiry
    cache.set(f'otp_code_{to_email}', otp_code, 600)
    
    subject = 'رمز التحقق - سوق'
    html_message = render_to_string('emails/otp_email.html', {
        'username': username,
        'otp_code': otp_code,
    })
    plain_message = strip_tags(html_message)
    
    kwargs = {
        'subject': subject,
        'message': plain_message,
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'recipient_list': [to_email],
        'html_message': html_message,
    }
    import threading
    threading.Thread(target=send_mail, kwargs=kwargs, daemon=True).start()


def verify_otp_code(email, code):
    """Verify OTP code"""
    cached_code = cache.get(f'otp_code_{email}')
    if cached_code and cached_code == code:
        cache.delete(f'otp_code_{email}')
        return True
    return False


def send_registration_confirmation(to_email, username):
    """Send registration confirmation email"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    subject = 'مرحباً بك في سوق!'
    html_message = render_to_string('emails/welcome_email.html', {
        'username': username,
    })
    plain_message = strip_tags(html_message)
    
    kwargs = {
        'subject': subject,
        'message': plain_message,
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'recipient_list': [to_email],
        'html_message': html_message,
    }
    import threading
    threading.Thread(target=send_mail, kwargs=kwargs, daemon=True).start()


def send_password_reset_email(to_email, username, reset_url):
    """Send password reset email"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    subject = 'إعادة تعيين كلمة المرور - سوق'
    html_message = render_to_string('emails/password_reset_email.html', {
        'username': username,
        'reset_url': reset_url,
    })
    plain_message = strip_tags(html_message)
    
    kwargs = {
        'subject': subject,
        'message': plain_message,
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'recipient_list': [to_email],
        'html_message': html_message,
    }
    import threading
    threading.Thread(target=send_mail, kwargs=kwargs, daemon=True).start()


def password_reset_success_email(to_email, username):
    """Send password reset success notification"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    subject = 'تم تغيير كلمة المرور - سوق'
    html_message = render_to_string('emails/password_reset_success.html', {
        'username': username,
    })
    plain_message = strip_tags(html_message)
    
    kwargs = {
        'subject': subject,
        'message': plain_message,
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'recipient_list': [to_email],
        'html_message': html_message,
    }
    import threading
    threading.Thread(target=send_mail, kwargs=kwargs, daemon=True).start()


def password_change_notification(to_email, username):
    """Send password change notification"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    subject = 'تم تغيير كلمة المرور - سوق'
    html_message = render_to_string('emails/password_changed.html', {
        'username': username,
    })
    plain_message = strip_tags(html_message)
    
    kwargs = {
        'subject': subject,
        'message': plain_message,
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'recipient_list': [to_email],
        'html_message': html_message,
    }
    import threading
    threading.Thread(target=send_mail, kwargs=kwargs, daemon=True).start()

import threading
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateformat import format as date_format
from django.core.mail import send_mail
from django.conf import settings
from store.models import Order

@login_required
def send_invoice(request, pk):
    """Send order invoice to user's email (AJAX)"""
    try:
        order = get_object_or_404(Order, pk=pk, user=request.user)
        
        # Build invoice HTML
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
        
        # تنسيق حالة الطلب بشكل صحيح
        status_display = order.get_status_display()
        
        invoice_html = f"""
        <div dir="rtl" style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; background: #F8F6F2;">
            <div style="background: white; border-radius: 16px; padding: 30px; border: 1px solid #E8E2D9;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #5C8A6E; font-size: 28px; margin: 0;">سوق</h1>
                    <p style="color: #7A7169; margin: 5px 0 0 0;">فاتورة طلب</p>
                </div>
                
                <div style="background: #EAF2EE; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h2 style="color: #5C8A6E; margin: 0 0 15px 0; font-size: 18px;">تفاصيل الطلب #{order.order_number}</h2>
                    <p style="margin: 5px 0; color: #2D2D2D;"><strong>التاريخ:</strong> {date_format(order.created_at, "d/m/Y H:i")}</p>
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
                            <th style="padding: 12px; text-align: right;">الإجمالي</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                
                <div style="border-top: 2px solid #E8E2D9; padding-top: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #7A7169;">المجموع الفرعي:</span>
                        <span style="color: #2D2D2D;">{order.subtotal} د.ج</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #7A7169;">الشحن:</span>
                        <span style="color: #2D2D2D;">{"مجاناً" if order.shipping_cost == 0 else f"{order.shipping_cost} د.ج"}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 20px; font-weight: bold; padding-top: 10px; border-top: 1px solid #E8E2D9;">
                        <span style="color: #5C8A6E;">الإجمالي:</span>
                        <span style="color: #5C8A6E;">{order.total_amount} د.ج</span>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #E8E2D9;">
                    <p style="color: #7A7169; font-size: 12px;">شكراً لتسوقكم معنا!</p>
                    <p style="color: #B5AFA8; font-size: 11px;">© 2024 سوق - جميع الحقوق محفوظة</p>
                </div>
            </div>
        </div>
        """
        
        # دالة الإرسال في الخلفية لعدم تعطيل الصفحة
        def send_emailInBackground():
            try:
                send_mail(
                    subject=f"فاتورة الطلب #{order.order_number} - سوق",
                    message="فاتورة طلبك",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.email],
                    html_message=invoice_html,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending invoice email: {e}")

        # تشغيل الإيميل في ثريد خلفي (Background Thread)
        email_thread = threading.Thread(target=send_emailInBackground)
        email_thread.daemon = True  # يغلق مع إغلاق السيرفر
        email_thread.start()

        # إرجاع رد فوري للمستخدم بدون انتظار الإيميل
        return JsonResponse({
            'success': True,
            'message': 'جاري إرسال الفاتورة إلى بريدك الإلكتروني...'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        })
  

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
