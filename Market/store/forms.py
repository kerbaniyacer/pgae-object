from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Product, Category, Review
import re
from django.core.exceptions import ValidationError

class UserTypeForm(forms.Form):
    USER_TYPE_CHOICES = [
        ('customer', 'مشتري'),
        ('seller', 'تاجر'),
    ]
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect, label='نوع الحساب')


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='البريد الإلكتروني')
    full_name = forms.CharField(max_length=255, required=False, label='الاسم الكامل')
    phone = forms.CharField(max_length=20, required=False, label='رقم الهاتف')
    city = forms.CharField(max_length=100, required=False, label='المدينة')
    user_type = forms.CharField(widget=forms.HiddenInput(), required=False)

    # Merchant fields
    store_name = forms.CharField(max_length=255, required=False, label='اسم المتجر')
    store_description = forms.CharField(widget=forms.Textarea, required=False, label='وصف المتجر')
    store_category = forms.CharField(max_length=100, required=False, label='فئة المتجر')
    store_logo = forms.ImageField(required=False, label='شعار المتجر')
    commercial_register = forms.CharField(max_length=50, required=False, label='السجل التجاري')

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone', 'password1', 'password2',
                  'user_type', 'store_name', 'store_description', 'store_category',
                  'store_logo', 'commercial_register']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['wilaya'] = forms.CharField(max_length=100, required=False, label='الولاية')
        self.fields['baladia'] = forms.CharField(max_length=100, required=False, label='البلدية')
        # Make merchant fields required if user_type is seller
        user_type = kwargs.get('initial', {}).get('user_type')
        if user_type == 'seller':
            self.fields['store_name'].required = True
            self.fields['store_description'].required = True
            self.fields['store_category'].required = True
            self.fields['store_logo'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        
        # التحقق من أن اسم المستخدم لا يحتوي على رموز (فقط أحرف وأرقام و _)
        if not re.match(r'^[a-zA-Z0-9_\u0600-\u06FF]+$', username):
            raise ValidationError('اسم المستخدم يجب أن يحتوي على أحرف وأرقام فقط بدون رموز')
        
        # التحقق من الطول
        if len(username) < 3:
            raise ValidationError('اسم المستخدم يجب أن يكون 3 أحرف على الأقل')
        
        if len(username) > 30:
            raise ValidationError('اسم المستخدم يجب ألا يتجاوز 30 حرف')
        
        # التحقق من عدم تكرار اسم المستخدم
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('اسم المستخدم مستخدم بالفعل، اختر اسماً آخر')
        
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        # التحقق من عدم تكرار البريد الإلكتروني
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('البريد الإلكتروني مستخدم بالفعل، سجل الدخول أو استخدم بريداً آخر')
        
        return email

    def clean_store_description(self):
        description = self.cleaned_data.get('store_description', '')
        if self.cleaned_data.get('user_type') == 'seller' and len(description) < 20:
            raise forms.ValidationError('يجب أن يكون وصف المتجر 20 حرف على الأقل')
        return description

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        # Set full name
        full_name = self.cleaned_data.get('full_name', '')
        if full_name:
            parts = full_name.split()
            if len(parts) >= 2:
                user.first_name = parts[0]
                user.last_name = ' '.join(parts[1:])
            else:
                user.first_name = full_name

        if commit:
            user.save()
            user_type = self.cleaned_data.get('user_type', 'customer')
            is_seller = user_type == 'seller'

            # Create profile
            Profile.objects.create(
                user=user,
                is_seller=is_seller,
                phone=self.cleaned_data.get('phone', ''),
                wilaya=self.cleaned_data.get('wilaya', ''),
                baladia=self.cleaned_data.get('baladia', ''),
                store_name=self.cleaned_data.get('store_name', '') if is_seller else '',
                store_description=self.cleaned_data.get('store_description', '') if is_seller else '',
                store_category=self.cleaned_data.get('store_category', '') if is_seller else '',
                store_logo=self.cleaned_data.get('store_logo') if is_seller else None,
                commercial_register=self.cleaned_data.get('commercial_register', '') if is_seller else '',
            )
        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label='اسم المستخدم')
    password = forms.CharField(widget=forms.PasswordInput, label='كلمة المرور')


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=255, required=False, label='الاسم الكامل')

    class Meta:
        model = Profile
        fields = ['phone', 'address', 'wilaya', 'baladia', 'bio', 'photo',
                  'store_name', 'store_description', 'store_category', 'store_logo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            user = self.instance.user
            self.fields['full_name'].initial = f"{user.first_name} {user.last_name}".strip()

        # Only show merchant fields for sellers
        if not self.instance.is_seller:
            del self.fields['store_name']
            del self.fields['store_description']
            del self.fields['store_category']
            del self.fields['store_logo']

    def save(self, commit=True):
        profile = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '')
        if full_name:
            parts = full_name.split()
            if len(parts) >= 2:
                profile.user.first_name = parts[0]
                profile.user.last_name = ' '.join(parts[1:])
            else:
                profile.user.first_name = full_name
            profile.user.save()
        if commit:
            profile.save()
        return profile


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'brand', 'price', 'old_price',
                  'discount', 'stock', 'sku', 'image', 'is_active', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all resize-none'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'}),
            'brand': forms.TextInput(attrs={'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'}),
            'old_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'}),
            'discount': forms.NumberInput(attrs={'min': '0', 'max': '100', 'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'}),
            'stock': forms.NumberInput(attrs={'min': '0', 'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'}),
            'sku': forms.TextInput(attrs={'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].required = False
        self.fields['brand'].required = False
        self.fields['old_price'].required = False
        self.fields['discount'].required = False
        self.fields['sku'].required = False


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image', 'is_active']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }
