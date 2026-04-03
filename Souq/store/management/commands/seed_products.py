"""
سكريبت لملء قاعدة البيانات بالفئات والعلامات التجارية والمنتجات ومتغيراتها
مطابق لموديلز المشروع الحالية (استخدام JSONField للمتغيرات)
"""

import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files import File
from store.models import Category, Brand, Product, ProductVariant, ProductImage


class Command(BaseCommand):
    help = 'ملء قاعدة البيانات بالفئات والعلامات التجارية والمنتجات ومتغيراتها'

    def add_arguments(self, parser):
        parser.add_argument(
            '--image',
            type=str,
            help='مسار الصورة الافتراضية لجميع المنتجات (اختياري)',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='مسح البيانات القديمة قبل الإنشاء',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 بدء عملية ملء قاعدة البيانات...')
        
        # مسح البيانات القديمة
        if options['clean']:
            self.stdout.write('🗑️ مسح البيانات القديمة...')
            ProductImage.objects.all().delete()
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            Brand.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ تم مسح البيانات القديمة'))
        
        # التحقق من الصورة
        default_image_path = options.get('image')
        
        if default_image_path and os.path.exists(default_image_path):
            self.stdout.write(f'📷 تم العثور على الصورة: {default_image_path}')
        elif default_image_path:
            self.stdout.write(self.style.WARNING(f'⚠️ الصورة غير موجودة: {default_image_path}'))
        
        # الحصول على المستخدم admin
        try:
            admin_user = User.objects.get(username='admin')
            self.stdout.write(f'✓ المستخدم: {admin_user.username}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ المستخدم admin غير موجود! قم بإنشائه أولاً.'))
            return

        # ==========================================
        # 1. إنشاء الفئات
        # ==========================================
        self.stdout.write('\n📂 جاري إنشاء الفئات...')
        categories_data = {
            'إلكترونيات': ['هواتف ذكية', 'لابتوب', 'سماعات', 'ساعات ذكية'],
            'أجهزة منزلية': ['ثلاجات', 'غسالات', 'تلفزيونات'],
            'ملابس': ['رجالي', 'نسائي', 'أحذية'],
            'مستحضرات تجميل': ['عناية بالبشرة', 'عطور'],
            'رياضة ولياقة': ['معدات رياضية', 'ملابس رياضية'],
        }
        
        created_categories = 0
        for parent_name, children in categories_data.items():
            parent_cat, created = Category.objects.get_or_create(
                name=parent_name, parent=None, defaults={'is_active': True}
            )
            if created: created_categories += 1
            
            for child_name in children:
                child_cat, created = Category.objects.get_or_create(
                    name=child_name, parent=parent_cat, defaults={'is_active': True}
                )
                if created: created_categories += 1

        self.stdout.write(self.style.SUCCESS(f'📊 تم إنشاء {created_categories} فئة'))

        # ==========================================
        # 2. إنشاء العلامات التجارية (Brands)
        # ==========================================
        self.stdout.write('\n🏷️ جاري إنشاء العلامات التجارية...')
        brands_list = ['Apple', 'Samsung', 'Xiaomi', 'Sony', 'LG', 'Dell', 'Nike', 'Adidas', 'Chanel', 'Dior', 'Generic']
        brands_objs = {}
        
        for brand_name in brands_list:
            brand, _ = Brand.objects.get_or_create(
                name=brand_name,
                defaults={'slug': brand_name.lower().replace(' ', '-')}
            )
            brands_objs[brand_name] = brand

        self.stdout.write(self.style.SUCCESS(f'🏷️ تم التأكد من {len(brands_list)} علامة تجارية'))

        # ==========================================
        # 3. إنشاء المنتجات والمتغيرات
        # ==========================================
        self.stdout.write('\n🛍️ بدء إنشاء المنتجات...')
        
        products_data = [
            {
                'name': 'iPhone 15 Pro Max',
                'category': 'هواتف ذكية',
                'brand': 'Apple',
                'description': 'أحدث هاتف من آبل مع شاشة Super Retina XDR ومعالج A17 Pro القوي.',
                'variants': [
                    {'name': '128GB - أسود', 'sku': 'IP15PM-128-BLK', 'price': 149999, 'old_price': 169999, 'stock': 25, 'attrs': {'الذاكرة': '128GB', 'اللون': 'أسود'}},
                    {'name': '256GB - أبيض', 'sku': 'IP15PM-256-WHT', 'price': 169999, 'old_price': 189999, 'stock': 30, 'attrs': {'الذاكرة': '256GB', 'اللون': 'أبيض'}},
                    {'name': '512GB - ذهبي', 'sku': 'IP15PM-512-GLD', 'price': 199999, 'old_price': 219999, 'stock': 15, 'attrs': {'الذاكرة': '512GB', 'اللون': 'ذهبي'}},
                ]
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'category': 'هواتف ذكية',
                'brand': 'Samsung',
                'description': 'هاتف سامسونج الرائد مع قلم S Pen مدمج وشاشة Dynamic AMOLED 2X.',
                'variants': [
                    {'name': '256GB - أسود', 'sku': 'S24U-256-BLK', 'price': 129999, 'old_price': 149999, 'stock': 40, 'attrs': {'الذاكرة': '256GB', 'اللون': 'أسود'}},
                    {'name': '512GB - بنفسجي', 'sku': 'S24U-512-PUR', 'price': 149999, 'old_price': 169999, 'stock': 20, 'attrs': {'الذاكرة': '512GB', 'اللون': 'بنفسجي'}},
                ]
            },
            {
                'name': 'MacBook Pro 14" M3 Pro',
                'category': 'لابتوب',
                'brand': 'Apple',
                'description': 'لابتوب آبل الاحترافي مع شريحة M3 Pro وشاشة Liquid Retina XDR.',
                'variants': [
                    {'name': '18GB/512GB - فضي', 'sku': 'MBP14-M3P-512', 'price': 249999, 'old_price': 279999, 'stock': 15, 'attrs': {'المعالج': 'Apple M3 Pro', 'الرام': '18GB', 'التخزين': '512GB SSD'}},
                    {'name': '36GB/1TB - فضي', 'sku': 'MBP14-M3P-1TB', 'price': 299999, 'old_price': 329999, 'stock': 10, 'attrs': {'المعالج': 'Apple M3 Pro', 'الرام': '36GB', 'التخزين': '1TB SSD'}},
                ]
            },
            {
                'name': 'Nike Dri-FIT T-Shirt',
                'category': 'رجالي',
                'brand': 'Nike',
                'description': 'تيشيرت نايكي رياضي بتقنية Dri-FIT للتهوية.',
                'variants': [
                    {'name': 'S - أسود', 'sku': 'NK-DRIFT-S-BLK', 'price': 4999, 'stock': 100, 'attrs': {'المقاس': 'S', 'اللون': 'أسود'}},
                    {'name': 'M - أبيض', 'sku': 'NK-DRIFT-M-WHT', 'price': 4999, 'stock': 120, 'attrs': {'المقاس': 'M', 'اللون': 'أبيض'}},
                    {'name': 'XL - أزرق', 'sku': 'NK-DRIFT-XL-BLU', 'price': 4999, 'stock': 60, 'attrs': {'المقاس': 'XL', 'اللون': 'أزرق'}},
                ]
            },
            {
                'name': 'Nike Air Max 270',
                'category': 'أحذية',
                'brand': 'Nike',
                'description': 'حذاء نايكي الرسمي مع وسادة Air Max.',
                'variants': [
                    {'name': '42 - أسود', 'sku': 'NK-AM270-42', 'price': 24999, 'old_price': 29999, 'stock': 20, 'attrs': {'المقاس': '42', 'اللون': 'أسود'}},
                    {'name': '43 - أبيض', 'sku': 'NK-AM270-43', 'price': 24999, 'old_price': 29999, 'stock': 18, 'attrs': {'المقاس': '43', 'اللون': 'أبيض'}},
                ]
            },
            {
                'name': 'Bleu de Chanel',
                'category': 'عطور',
                'brand': 'Chanel',
                'description': 'عطر شانيل الرجالي الكلاسيكي.',
                'variants': [
                    {'name': '100ml', 'sku': 'CHANEL-BLEU-100', 'price': 45000, 'old_price': 52000, 'stock': 25, 'attrs': {'الحجم': '100ml'}},
                    {'name': '50ml', 'sku': 'CHANEL-BLEU-50', 'price': 32000, 'old_price': 38000, 'stock': 30, 'attrs': {'الحجم': '50ml'}},
                ]
            },
            {
                'name': 'Yoga Mat Premium',
                'category': 'معدات رياضية',
                'brand': 'Generic',
                'description': 'سجادة يوجا احترافية مقاومة للانزلاق.',
                'variants': [
                    {'name': 'بنفسجي', 'sku': 'YOGA-MAT-PUR', 'price': 4999, 'stock': 50, 'attrs': {'اللون': 'بنفسجي'}},
                    {'name': 'أزرق', 'sku': 'YOGA-MAT-BLU', 'price': 4999, 'stock': 45, 'attrs': {'اللون': 'أزرق'}},
                ]
            }
        ]

        created_products = 0
        created_variants = 0
        
        for prod_data in products_data:
            try:
                category = Category.objects.get(name=prod_data['category'])
            except Category.DoesNotExist:
                continue
            
            brand_obj = brands_objs.get(prod_data.get('brand'))
            
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'seller': admin_user,
                    'category': category,
                    'brand': brand_obj,
                    'description': prod_data['description'],
                    'is_active': True,
                    'is_featured': random.choice([True, False]),
                }
            )
            
            if created:
                created_products += 1
                self.stdout.write(f'  ✓ منتج: {prod_data["name"]}')
                
                # إضافة الصورة إن وجدت
                if default_image_path and os.path.exists(default_image_path):
                    with open(default_image_path, 'rb') as img_file:
                        product.image.save(
                            os.path.basename(default_image_path),
                            File(img_file),
                            save=True
                        )
                        ProductImage.objects.create(product=product, image=product.image, is_main=True)
            
            # إنشاء المتغيرات
            for index, var_data in enumerate(prod_data['variants']):
                # حساب نسبة الخصم تلقائياً
                discount = 0
                if var_data.get('old_price') and var_data['price'] < var_data['old_price']:
                    discount = int(((var_data['old_price'] - var_data['price']) / var_data['old_price']) * 100)

                variant, created = ProductVariant.objects.get_or_create(
                    product=product,
                    sku=var_data['sku'],
                    defaults={
                        'name': var_data['name'],
                        'price': var_data['price'],
                        'old_price': var_data.get('old_price'),
                        'discount': discount, # يتم حساب الخصم
                        'stock': var_data['stock'],
                        'is_active': True,
                        'is_main': (index == 0), # تحديد أول متغير كمتغير رئيسي
                        'attributes': var_data.get('attrs', {}) # حفظ القيم داخل JSONField
                    }
                )
                
                if created:
                    created_variants += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n📦 المنتجات: {created_products} | المتغيرات: {created_variants}'
        ))
        self.stdout.write(self.style.SUCCESS('\n✅ تم إكمال العملية بنجاح!'))