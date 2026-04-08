from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models import Avg
from django.core.exceptions import ValidationError
import random
import string


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='اسم الفئة')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )    
    slug = models.SlugField(unique=True, blank=True, verbose_name='الرابط')
    logo = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='الصورة')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'الفئة'
        verbose_name_plural = 'الفئات'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    @property
    def products_count(self):
        return self.products.filter(is_active=True).count()

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('store:category_detail', args=[self.slug])

    def get_products_count(self):
        return self.products.count()

    def get_active_products_count(self):
        return self.products.filter(is_active=True).count()

    def get_children(self):
        return Category.objects.filter(parent=self)

    def has_children(self):
        return self.get_children().exists()

    def get_all_products(self):
        if self.has_children():
            products = []
            for child in self.get_children():
                products.extend(child.get_all_products())
            return products
        else:
            return self.products.all()

    def get_active_products(self):
        if self.has_children():
            products = []
            for child in self.get_children():
                products.extend(child.get_active_products())
            return products
        else:
            return self.products.filter(is_active=True)

    def get_average_rating(self):
        return self.products.aggregate(Avg('average_rating'))['average_rating'] or 0    


class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Brand Name"))
    slug = models.SlugField(unique=True, blank=True, verbose_name=_("Slug"))
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, verbose_name=_("Brand Logo"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='brands', verbose_name='الفئة')
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    website = models.URLField(blank=True, null=True, verbose_name=_("Website"))
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Country"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:brand_detail', args=[self.slug])

    def get_products_count(self):
        return self.products.count()

    def get_active_products_count(self):
        return self.products.filter(is_active=True).count()

    def get_products(self):
        return self.products.all()

    def get_active_products(self):
        return self.products.filter(is_active=True)

    def get_average_rating(self):
        return self.products.aggregate(Avg('average_rating'))['average_rating'] or 0


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='الفئة')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', verbose_name='البائع')
    name = models.CharField(max_length=255, verbose_name='اسم المنتج')
    slug = models.SlugField(unique=True, blank=True, verbose_name='الرابط')
    description = models.TextField(verbose_name='الوصف')
    sku = models.CharField(max_length=50, blank=True, verbose_name='رمز المنتج')
    brand = models.ForeignKey(Brand,null=True,blank=True, on_delete=models.CASCADE, related_name='products', verbose_name='العلامة التجارية')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    is_featured = models.BooleanField(default=False, verbose_name='مميز')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='التقييم')
    reviews_count = models.PositiveIntegerField(default=0, verbose_name='عدد التقييمات')
    sold_count = models.PositiveIntegerField(default=0, verbose_name='عدد المبيعات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    is_owner = models.BooleanField(default=False, verbose_name='هل هذا المنتج يخص المستخدم الحالي')

    def generate_unique_slug(self):
        slug = slugify(self.name)
        unique_slug = slug
        counter = 1

        while Product.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{counter}"
            counter += 1

        return unique_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()


        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        # التحقق من المخزون عبر المتغيرات أو المخزون المباشر
        if self.variants.exists():
            return self.variants.filter(stock__gt=0).exists()
        return False

    @property
    def total_stock(self):
        if self.variants.exists():
            return self.variants.aggregate(total=models.Sum('stock'))['total'] or 0
        return 0

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    @property
    def image(self):
        """جلب الصورة الرئيسية للمنتج من متغيراته - لإرجاع كائن صورة متوافق مع القوالب القديمة"""
        v = self.variants.filter(is_main=True).first()
        if not v:
            v = self.variants.filter(stock__gt=0).first()
        if not v:
            v = self.variants.first()
        
        if v:
            # نحاول جلب الصورة الرئيسية للمتغير
            img = v.images.filter(is_main=True).first()
            if not img:
                img = v.images.first()
            return img.image if img else None
        return None

class ProductAttribute(models.Model): #Specification    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}: {self.value}"
        
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='المنتج')
    name = models.CharField(max_length=100, verbose_name='اسم المتغير', blank=True, default='')
    sku = models.CharField(max_length=100, verbose_name='رمز المتغير')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='السعر')
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='السعر القديم')
    discount = models.PositiveIntegerField(default=0, verbose_name='نسبة الخصم')
    stock = models.PositiveIntegerField(default=0, verbose_name='المخزون')
    
    # ✅ تم إزالة حقل image القديم نهائياً
    
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    attributes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    is_main = models.BooleanField(default=False, verbose_name='المتغير الرئيسي')

    class Meta:
        unique_together = ['product', 'sku']
        verbose_name = 'متغير المنتج'
        verbose_name_plural = 'متغيرات المنتجات'

    def save(self, *args, **kwargs):
        # 1. إذا كان هذا المتغير هو الرئيسي، نقوم بإلغاء "الرئيسي" عن باقي المتغيرات
        if self.is_main:
            ProductVariant.objects.filter(product=self.product, is_main=True).exclude(pk=self.pk).update(is_main=False)
        else:
            # 2. إذا لم يكن رئيسياً، نتحقق إذا كان هناك أي متغير رئيسي آخر للمنتج
            # إذا لم يوجد، نجعل هذا المتغير هو الرئيسي تلقائياً
            if not ProductVariant.objects.filter(product=self.product, is_main=True).exclude(pk=self.pk).exists():
                self.is_main = True
                
        super().save(*args, **kwargs)

    def __str__(self):
        if self.name:
            return f"{self.product.name} - {self.name}"
        return f"{self.product.name} - {self.sku}"

    @property
    def is_in_stock(self):
        return self.stock > 0
    
    @property
    def get_image(self):
        """أول صورة مرتبطة بهذا المتغير من جدول VariantImage"""
        img = self.images.filter(is_main=True).first()
        if not img:
            img = self.images.first()
        return img.image.url if img else None

    @property
    def get_main_image_obj(self):
        """كائن الصورة الرئيسية"""
        img = self.images.filter(is_main=True).first()
        if not img:
            img = self.images.first()
        return img

class VariantImage(models.Model):
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        related_name='variant_images',
        verbose_name='المنتج'
    )
    image = models.ImageField(
        upload_to='variants/%Y/%m/', 
        verbose_name='الصورة'
    )
    alt_text = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='النص البديل'
    )
    variants = models.ManyToManyField(
        'ProductVariant', 
        blank=True, 
        related_name='images',
        verbose_name='المتغيرات المرتبطة'
    )
    is_main = models.BooleanField(
        default=False, 
        verbose_name='صورة رئيسية'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'صورة متغير'
        verbose_name_plural = 'صور المتغيرات'
        ordering = ['-is_main', 'id']

    def __str__(self):
        variant_names = ', '.join(
            self.variants.values_list('name', flat=True)[:3]
        )
        return f"{self.product.name} → {variant_names or 'بدون متغيرات'}"

    def save(self, *args, **kwargs):
        # لو فعّلناها كرئيسية، نلغي الرئيسية الأخرى لنفس المنتج
        if self.is_main:
            VariantImage.objects.filter(
                product=self.product
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

class ProductVideo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='products/videos/')
    
    class Meta:
        verbose_name = 'فيديو المنتج'

    def __str__(self):
        return f"فيديو لـ {self.product.name}"

class AttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', verbose_name='المستخدم', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name='مفتاح الجلسة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'سلة المشتريات'
        verbose_name_plural = 'سلال المشتريات'
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_cart'
            ),
            models.UniqueConstraint(
                fields=['session_key'],
                condition=models.Q(user__isnull=True),
                name='unique_session_cart'
            ),
        ]

    def __str__(self):
        if self.user:
            return f"سلة {self.user.username}"
        return f"سلة زائر ({self.session_key})"

    def clear(self):
        self.items.all().delete()

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def unique_items_count(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='السلة')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, verbose_name='المتغير', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, verbose_name='الكمية')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'عنصر السلة'
        verbose_name_plural = 'عناصر السلة'
        unique_together = ['cart', 'variant']

    def __str__(self):
        return f"{self.quantity}x {self.variant.product.name}"

    @property
    def get_product(self):
        """للتوافق مع القوالب القديمة"""
        return self.variant.product if self.variant else None

    @property
    def subtotal(self):
        return self.variant.price * self.quantity if self.variant else 0

    def clean(self):
        if self.quantity < 1:
            raise ValidationError('الكمية يجب أن تكون 1 على الأقل')
        if self.quantity > self.variant.stock:
            raise ValidationError(f'الكمية المتوفرة هي {self.variant.stock} فقط')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('processing', 'قيد التجهيز'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التوصيل'),
        ('cancelled', 'ملغي'),
        ('returned', 'معاد'),
    ]

    PAYMENT_STATUS_CHOICES = [
    ('pending', 'في إنتظار الدفع'),
    ('paid', 'مدفوع'),
    ('failed', 'فشل الدفع'),
    ('refunded', 'مسترد'),
    ('cancelled', 'تم إلغاء الطلب'),
    ]

    PAYMENT_CHOICES = [
        ('cod', 'الدفع عند الاستلام'),
        ('card', 'بطاقة ائتمان'),
        ('apple_pay', 'Apple Pay'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='المستخدم', null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True, verbose_name='رقم الطلب')
    username = models.CharField(max_length=150, verbose_name='اسم المستخدم', null=True, blank=True)  # حقل جديد لحفظ اسم المستخدم في الطلب

    # Shipping Info
    full_name = models.CharField(max_length=255, verbose_name='الاسم الكامل')
    phone = models.CharField(max_length=20, verbose_name='رقم الهاتف')
    email = models.EmailField(verbose_name='البريد الإلكتروني')
    address = models.TextField(verbose_name='العنوان')
    wilaya = models.CharField(max_length=100, verbose_name='الولاية', default='اختر الولاية')
    baladia = models.CharField(max_length=100, verbose_name='البلدية', default='اختر البلدية')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='الرمز البريدي')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    # Order Info
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المجموع الفرعي')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='تكلفة الشحن')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='الخصم')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المبلغ الكلي')
    tracking_number = models.CharField(max_length=50, blank=True, verbose_name='رقم التتبع', null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod', verbose_name='طريقة الدفع')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='حالة الدفع')
    stock_deducted = models.BooleanField(default=False, verbose_name='تم خصم المخزن')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب #{self.order_number}"

    def save(self, *args, **kwargs):
        import random
        import string
        if not self.order_number:
            new_number = 'ORD' + ''.join(random.choices(string.digits, k=8))
            while Order.objects.filter(order_number=new_number).exists():
                new_number = 'ORD' + ''.join(random.choices(string.digits, k=8))
            self.order_number = new_number
            
        if not self.tracking_number:
            new_trk = 'TRK' + ''.join(random.choices(string.digits, k=8))
            while Order.objects.filter(tracking_number=new_trk).exists():
                new_trk = 'TRK' + ''.join(random.choices(string.digits, k=8))
            self.tracking_number = new_trk
            
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='الطلب')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='المنتج')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, verbose_name='المتغير')
    product_name = models.CharField(max_length=255, verbose_name='اسم المنتج')
    product_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='سعر المنتج')
    quantity = models.PositiveIntegerField(verbose_name='الكمية')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المجموع')

    class Meta:
        verbose_name = 'عنصر الطلب'
        verbose_name_plural = 'عناصر الطلب'

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist', verbose_name='المستخدم')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='المنتج')
    created_at = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name='مفتاح الجلسة')
    class Meta:
        verbose_name = 'المفضلة'
        verbose_name_plural = 'المفضلات'
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items', verbose_name='المفضلة')
    quantity = models.PositiveIntegerField(default=1, verbose_name='الكمية')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, verbose_name='المتغير', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'عنصر المفضلة'
        verbose_name_plural = 'عناصر المفضلة'
        unique_together = ['wishlist', 'variant']

    def __str__(self):
        return f"{self.quantity}x {self.variant.product.name}"

    @property
    def get_product(self):
        """للتوافق مع القوالب القديمة"""
        return self.variant.product

    @property
    def subtotal(self):
        return self.variant.price * self.quantity

    def clean(self):
        if self.quantity < 1:
            raise ValidationError('الكمية يجب أن تكون 1 على الأقل')
        if self.quantity > self.variant.stock:
            raise ValidationError(f'الكمية المتوفرة هي {self.variant.stock} فقط')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='المنتج')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='المستخدم')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='التقييم')
    comment = models.TextField(verbose_name='التعليق')
    verified = models.BooleanField(default=False, verbose_name='مشتري موثق')
    helpful_count = models.PositiveIntegerField(default=0, verbose_name='عدد المفيد')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التقييم')

    class Meta:
        verbose_name = 'التقييم'
        verbose_name_plural = 'التقييمات'
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"تقييم {self.user.username} لـ {self.product.name}"


class SubscriptEmail(models.Model):
    email = models.EmailField(unique=True, verbose_name='البريد الإلكتروني')
    def __str__(self):
        return {self.email}

