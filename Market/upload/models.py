from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='المستخدم')
    is_seller = models.BooleanField(default=False, verbose_name='تاجر')
    phone = models.CharField(max_length=20, blank=True, verbose_name='رقم الهاتف')
    address = models.CharField(max_length=255, blank=True, verbose_name='العنوان')
    city = models.CharField(max_length=100, blank=True, verbose_name='المدينة')
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
    slug = models.SlugField(unique=True, blank=True, verbose_name='الرابط')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='الصورة')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'الفئة'
        verbose_name_plural = 'الفئات'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def products_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='الفئة')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', verbose_name='البائع')
    name = models.CharField(max_length=255, verbose_name='اسم المنتج')
    slug = models.SlugField(unique=True, blank=True, verbose_name='الرابط')
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

    class Meta:
        verbose_name = 'المنتج'
        verbose_name_plural = 'المنتجات'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Calculate discount percentage
        if self.old_price and self.old_price > self.price:
            self.discount = int((self.old_price - self.price) / self.old_price * 100)
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='المنتج')
    image = models.ImageField(upload_to='products/gallery/', verbose_name='الصورة')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'صورة المنتج'
        verbose_name_plural = 'صور المنتجات'

    def __str__(self):
        return f"صورة لـ {self.product.name}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', verbose_name='المستخدم', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name='مفتاح الجلسة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'سلة المشتريات'
        verbose_name_plural = 'سلال المشتريات'

    def __str__(self):
        return f"سلة {self.user.username if self.user else self.session_key}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='السلة')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='المنتج')
    quantity = models.PositiveIntegerField(default=1, verbose_name='الكمية')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'عنصر السلة'
        verbose_name_plural = 'عناصر السلة'
        unique_together = ['cart', 'product']

    @property
    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


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
    city = models.CharField(max_length=100, verbose_name='المدينة')
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
