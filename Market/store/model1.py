from unicodedata import name
from django.utils.text import slugify

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from ckeditor_uploader.fields import RichTextUploadingField


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='المستخدم')
    is_seller = models.BooleanField(default=False, verbose_name='تاجر')
    phone = models.CharField(max_length=20, blank=True, verbose_name='رقم الهاتف')
    address = models.CharField(max_length=255, blank=True, verbose_name='العنوان')
    wilaya = models.CharField(max_length=100, blank=True, verbose_name='الولاية')
    baladia = models.CharField(max_length=100, blank=True, verbose_name='البلدية')
    bio = models.TextField(blank=True, verbose_name='نبذة')
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name='الصورة الشخصية')

    # Merchant-specific fields
    store_name = models.CharField(max_length=255, blank=True, verbose_name='اسم المتجر')
    store_description = models.TextField(blank=True, verbose_name='وصف المتجر')
    store_category = models.CharField(max_length=100, blank=True, verbose_name='فئة المتجر')
    store_logo = models.ImageField(upload_to='stores/', blank=True, null=True, verbose_name='شعار المتجر')
    commercial_register = models.CharField(max_length=50, blank=True, verbose_name='السجل التجاري')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'الملف الشخصي'
        verbose_name_plural = 'الملفات الشخصية'

    def __str__(self):
        return f"{self.user.username} - الملف الشخصي"


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
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='الصورة')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        unique_together = ['name', 'parent']
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


class Attribute(models.Model):
    name = models.CharField(max_length=255)  # مثال: RAM, Color
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='attributes')

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ['attribute', 'value']

    def __str__(self):
        return self.value


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='الفئة')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', verbose_name='البائع')
    name = models.CharField(max_length=255, verbose_name='اسم المنتج')
    slug = models.SlugField(unique=True, blank=True, verbose_name='الرابط')
    Specifications = RichTextUploadingField(verbose_name='المواصفات')
    description = models.TextField(verbose_name='الوصف')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='السعر')
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='السعر القديم')
    discount = models.PositiveIntegerField(default=0, verbose_name='نسبة الخصم')
    image = models.ImageField(upload_to='products/', verbose_name='الصورة الرئيسية')
    stock = models.PositiveIntegerField(default=0, verbose_name='المخزون')
    sku = models.CharField(max_length=50, blank=True, verbose_name='رمز المنتج')
    brand = models.CharField(max_length=100, blank=True, verbose_name='العلامة التجارية')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    is_featured = models.BooleanField(default=False, verbose_name='مميز')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='التقييم')
    reviews_count = models.PositiveIntegerField(default=0, verbose_name='عدد التقييمات')
    sold_count = models.PositiveIntegerField(default=0, verbose_name='عدد المبيعات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

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

        if self.old_price and self.old_price > self.price:
            self.discount = int((self.old_price - self.price) / self.old_price * 100)

        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        # التحقق من المخزون عبر المتغيرات أو المخزون المباشر
        if self.variants.exists():
            return self.variants.filter(stock__gt=0).exists()
        return self.stock > 0

    @property
    def total_stock(self):
        if self.variants.exists():
            return self.variants.aggregate(total=models.Sum('stock'))['total'] or 0
        return self.stock

    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    def clean(self):
        if self.value.attribute != self.attribute:
            raise ValidationError("القيمة لا تنتمي إلى الخاصية")

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image of {self.product.name}"


class ProductVideo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos', verbose_name='المنتج')
    video = models.FileField(upload_to='products/videos/', verbose_name='فيديو')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'فيديو المنتج'
        verbose_name_plural = 'فيديوهات المنتجات'

    def __str__(self):
        return f"فيديو لـ {self.product.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='المنتج')
    name = models.CharField(max_length=100, verbose_name='اسم المتغير', blank=True, default='')
    sku = models.CharField(max_length=100, verbose_name='رمز المتغير')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='السعر')
    stock = models.PositiveIntegerField(default=0, verbose_name='المخزون')
    image = models.ImageField(upload_to='products/variants/', blank=True, null=True, verbose_name='صورة المتغير')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    attributes = models.ManyToManyField(AttributeValue, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'sku']
        verbose_name = 'متغير المنتج'
        verbose_name_plural = 'متغيرات المنتجات'

    def __str__(self):
        if self.name:
            return f"{self.product.name} - {self.name}"
        return f"{self.product.name} - {self.sku}"

    @property
    def is_in_stock(self):
        return self.stock > 0


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
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, verbose_name='المتغير')
    quantity = models.PositiveIntegerField(default=1, verbose_name='الكمية')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'عنصر السلة'
        verbose_name_plural = 'عناصر السلة'
        unique_together = ['cart', 'variant']

    def __str__(self):
        return f"{self.quantity}x {self.variant.product.name}"

    @property
    def product(self):
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

    PAYMENT_CHOICES = [
        ('cod', 'الدفع عند الاستلام'),
        ('card', 'بطاقة ائتمان'),
        ('apple_pay', 'Apple Pay'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='المستخدم')
    order_number = models.CharField(max_length=20, unique=True, verbose_name='رقم الطلب')

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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod', verbose_name='طريقة الدفع')
    payment_status = models.BooleanField(default=False, verbose_name='تم الدفع')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random
            import string
            self.order_number = 'ORD' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='الطلب')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='المنتج')
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

    class Meta:
        verbose_name = 'المفضلة'
        verbose_name_plural = 'المفضلات'
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


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
