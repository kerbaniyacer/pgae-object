from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *
import re
from django.core.exceptions import ValidationError

class ProductForm(forms.ModelForm):
    """نموذج إضافة/تعديل المنتج"""
    
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'brand', 'sku', 'is_active', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
                'placeholder': 'اسم المنتج'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all resize-none',
                'placeholder': 'وصف المنتج'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
            }),
            # ✅ تم التصحيح: تغيير TextInput إلى Select لأنه ForeignKey
            'brand': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
            }),
            'sku': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
                'placeholder': 'رمز المنتج (SKU)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].required = False
        self.fields['brand'].required = False
        self.fields['brand'].queryset = Brand.objects.all() # ✅ إضافة قائمة العلامات التجارية
        self.fields['sku'].required = False
        self.fields['is_active'].initial = True


class ProductVariantForm(forms.ModelForm):
    """نموذج إضافة/تعديل متغير المنتج"""
    
    class Meta:
        model = ProductVariant
        fields = ['name', 'sku', 'price', 'old_price', 'stock', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
                'placeholder': 'اسم المتغير (مثل: أحمر - Large)'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
                'placeholder': 'رمز المتغير'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
                'placeholder': 'السعر',
                'step': '0.01'
            }),
            'old_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
                'placeholder': 'السعر القديم (اختياري)',
                'step': '0.01'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all',
                'placeholder': 'الكمية المتوفرة'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_price'].required = False
        self.fields['image'].required = False


class CategoryForm(forms.ModelForm):
    """نموذج الفئة"""
    
    class Meta:
        model = Category
        fields = ['name', 'parent', 'logo', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'
            }),
            'parent': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-page-bg border border-border-sand rounded-xl focus:border-sage focus:ring-2 focus:ring-sage/10 outline-none transition-all'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Category.objects.filter(is_active=True, parent=None)
        self.fields['parent'].required = False


class ReviewForm(forms.ModelForm):
    """نموذج التقييم"""
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }