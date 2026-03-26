from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Product, Category, Review


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
        fields = ['username', 'email', 'full_name', 'phone', 'city', 'password1', 'password2',
                  'user_type', 'store_name', 'store_description', 'store_category',
                  'store_logo', 'commercial_register']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make merchant fields required if user_type is seller
        user_type = kwargs.get('initial', {}).get('user_type')
        if user_type == 'seller':
            self.fields['store_name'].required = True
            self.fields['store_description'].required = True
            self.fields['store_category'].required = True
            self.fields['store_logo'].required = True

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
                city=self.cleaned_data.get('city', ''),
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
        fields = ['phone', 'address', 'city', 'bio', 'photo',
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
