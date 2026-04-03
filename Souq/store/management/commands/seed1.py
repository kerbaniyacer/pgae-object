"""
سكريبت لملء قاعدة البيانات بالفئات والخصائص والمنتجات
- الفئات بالعربية
- الخصائص بالإنجليزية
- منتجات لحساب التاجر "admin"
- دعم إضافة صورة افتراضية لجميع المنتجات
"""

import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files import File
from store.models import (
    Category, Attribute, AttributeValue, 
    Product, ProductVariant, ProductImage
)


class Command(BaseCommand):
    help = 'ملء قاعدة البيانات بالفئات والخصائص والمنتجات'

    def add_arguments(self, parser):
        parser.add_argument(
            '--image',
            type=str,
            help='مسار الصورة الافتراضية لجميع المنتجات',
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
            AttributeValue.objects.all().delete()
            Attribute.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ تم مسح البيانات القديمة'))
        
        # التحقق من الصورة
        default_image_path = options.get('image')
        default_image = None
        
        if default_image_path and os.path.exists(default_image_path):
            self.stdout.write(f'📷 تم العثور على الصورة: {default_image_path}')
        elif default_image_path:
            self.stdout.write(self.style.WARNING(f'⚠️ الصورة غير موجودة: {default_image_path}'))
        
        # الحصول على المستخدم admin
        try:
            admin_user = User.objects.get(username='admin')
            self.stdout.write(f'✓ المستخدم: {admin_user.username}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ المستخدم admin غير موجود!'))
            return

        # ==========================================
        # البيانات: الفئات العربية مع الخصائص الإنجليزية
        # ==========================================
        categories_data = {
            'إلكترونيات': {
                'attributes': {
                    'Brand': ['Samsung', 'Apple', 'Huawei', 'Xiaomi', 'Sony', 'LG', 'HP', 'Dell'],
                    'Color': ['Black', 'White', 'Silver', 'Gold', 'Blue', 'Red'],
                    'Warranty': ['1 Year', '2 Years', '3 Years'],
                },
                'children': {
                    'هواتف ذكية': {
                        'attributes': {
                            'Storage': ['64GB', '128GB', '256GB', '512GB', '1TB'],
                            'RAM': ['4GB', '6GB', '8GB', '12GB', '16GB'],
                            'Screen Size': ['6.1"', '6.5"', '6.7"'],
                            'Battery': ['4000mAh', '4500mAh', '5000mAh'],
                            'Camera': ['48MP', '64MP', '108MP', '200MP'],
                            '5G': ['Yes', 'No'],
                            'OS': ['Android', 'iOS'],
                        }
                    },
                    'لابتوب': {
                        'attributes': {
                            'Processor': ['Intel Core i5', 'Intel Core i7', 'AMD Ryzen 5', 'AMD Ryzen 7', 'Apple M2', 'Apple M3'],
                            'RAM': ['8GB', '16GB', '32GB'],
                            'Storage': ['256GB SSD', '512GB SSD', '1TB SSD'],
                            'Screen Size': ['13.3"', '14"', '15.6"'],
                        }
                    },
                    'سماعات': {
                        'attributes': {
                            'Type': ['In-Ear', 'On-Ear', 'Over-Ear'],
                            'Connectivity': ['Wired', 'Bluetooth'],
                            'Noise Cancellation': ['Active', 'Passive', 'None'],
                            'Battery Life': ['6 hours', '12 hours', '24 hours', '30+ hours'],
                        }
                    },
                    'ساعات ذكية': {
                        'attributes': {
                            'Display': ['AMOLED', 'LCD', 'OLED'],
                            'Water Resistant': ['IP67', 'IP68', '5ATM'],
                            'Battery Life': ['1 day', '3 days', '7 days', '14 days'],
                            'GPS': ['Yes', 'No'],
                        }
                    },
                }
            },
            
            'أجهزة منزلية': {
                'attributes': {
                    'Brand': ['Samsung', 'LG', 'Bosch', 'Whirlpool', 'Haier', 'Toshiba'],
                    'Color': ['White', 'Silver', 'Black'],
                    'Warranty': ['1 Year', '2 Years', '5 Years'],
                    'Energy Rating': ['A+++', 'A++', 'A+', 'A'],
                },
                'children': {
                    'ثلاجات': {
                        'attributes': {
                            'Capacity': ['300L', '400L', '500L', '600L'],
                            'Type': ['Single Door', 'Double Door', 'Side by Side', 'French Door'],
                            'Frost Free': ['Yes', 'No'],
                            'Inverter': ['Yes', 'No'],
                        }
                    },
                    'غسالات': {
                        'attributes': {
                            'Capacity': ['7kg', '8kg', '9kg', '10kg'],
                            'Type': ['Front Load', 'Top Load'],
                            'Spin Speed': ['1000 RPM', '1200 RPM', '1400 RPM'],
                        }
                    },
                    'تلفزيونات': {
                        'attributes': {
                            'Screen Size': ['43"', '50"', '55"', '65"', '75"'],
                            'Resolution': ['Full HD', '4K UHD', '8K'],
                            'Display Type': ['LED', 'QLED', 'OLED'],
                            'Smart TV': ['Yes', 'No'],
                            'Refresh Rate': ['60Hz', '120Hz'],
                        }
                    },
                }
            },
            
            'ملابس': {
                'attributes': {
                    'Brand': ['Nike', 'Adidas', 'Puma', 'Zara', 'H&M'],
                    'Material': ['Cotton', 'Polyester', 'Wool', 'Denim'],
                    'Size': ['S', 'M', 'L', 'XL', 'XXL'],
                    'Color': ['Black', 'White', 'Blue', 'Red', 'Grey', 'Navy'],
                },
                'children': {
                    'رجالي': {
                        'attributes': {
                            'Fit': ['Slim', 'Regular', 'Loose'],
                            'Sleeve': ['Short', 'Long'],
                            'Pattern': ['Solid', 'Striped', 'Checkered'],
                        }
                    },
                    'نسائي': {
                        'attributes': {
                            'Fit': ['Slim', 'Regular', 'Loose'],
                            'Length': ['Mini', 'Midi', 'Maxi'],
                            'Style': ['Casual', 'Formal', 'Party'],
                        }
                    },
                    'أحذية': {
                        'attributes': {
                            'Size': ['40', '41', '42', '43', '44', '45'],
                            'Type': ['Sneakers', 'Boots', 'Sandals', 'Formal'],
                        }
                    },
                }
            },
            
            'مستحضرات تجميل': {
                'attributes': {
                    'Brand': ["L'Oreal", 'Maybelline', 'MAC', 'Nivea', 'Dove'],
                    'Skin Type': ['All', 'Oily', 'Dry', 'Sensitive'],
                    'Volume': ['30ml', '50ml', '100ml', '200ml'],
                },
                'children': {
                    'عناية بالبشرة': {
                        'attributes': {
                            'Product Type': ['Cleanser', 'Serum', 'Moisturizer', 'Sunscreen'],
                            'Concern': ['Anti-Aging', 'Acne', 'Hydration', 'Brightening'],
                        }
                    },
                    'عطور': {
                        'attributes': {
                            'Concentration': ['Eau de Parfum', 'Eau de Toilette'],
                            'Volume': ['50ml', '75ml', '100ml'],
                            'Fragrance Family': ['Floral', 'Woody', 'Oriental', 'Fresh'],
                            'Gender': ['Men', 'Women', 'Unisex'],
                        }
                    },
                }
            },
            
            'رياضة ولياقة': {
                'attributes': {
                    'Brand': ['Nike', 'Adidas', 'Puma', 'Under Armour'],
                    'Size': ['S', 'M', 'L', 'XL'],
                },
                'children': {
                    'معدات رياضية': {
                        'attributes': {
                            'Type': ['Dumbbells', 'Yoga Mat', 'Resistance Bands', 'Jump Rope'],
                            'Weight': ['2kg', '5kg', '10kg', '15kg', '20kg'],
                        }
                    },
                    'ملابس رياضية': {
                        'attributes': {
                            'Type': ['T-Shirt', 'Shorts', 'Pants', 'Jacket'],
                            'Fit': ['Tight', 'Regular', 'Loose'],
                        }
                    },
                }
            },
        }

        # ==========================================
        # إنشاء الفئات والخصائص
        # ==========================================
        created_categories = 0
        created_attributes = 0
        created_values = 0
        
        for cat_name, cat_data in categories_data.items():
            category, created = Category.objects.get_or_create(
                name=cat_name,
                parent=None,
                defaults={'is_active': True}
            )
            if created:
                created_categories += 1
                self.stdout.write(f'✓ الفئة: {cat_name}')
            
            if 'attributes' in cat_data:
                for attr_name, values in cat_data['attributes'].items():
                    attribute, created = Attribute.objects.get_or_create(
                        name=attr_name,
                        category=category
                    )
                    if created:
                        created_attributes += 1
                    
                    for value in values:
                        attr_value, created = AttributeValue.objects.get_or_create(
                            attribute=attribute,
                            value=value
                        )
                        if created:
                            created_values += 1
            
            if 'children' in cat_data:
                for child_name, child_data in cat_data['children'].items():
                    child_category, created = Category.objects.get_or_create(
                        name=child_name,
                        parent=category,
                        defaults={'is_active': True}
                    )
                    if created:
                        created_categories += 1
                        self.stdout.write(f'  ✓ {child_name}')
                    
                    if 'attributes' in child_data:
                        for attr_name, values in child_data['attributes'].items():
                            attribute, created = Attribute.objects.get_or_create(
                                name=attr_name,
                                category=child_category
                            )
                            if created:
                                created_attributes += 1
                            
                            for value in values:
                                attr_value, created = AttributeValue.objects.get_or_create(
                                    attribute=attribute,
                                    value=value
                                )
                                if created:
                                    created_values += 1

        self.stdout.write(self.style.SUCCESS(
            f'📊 الفئات: {created_categories} | الخصائص: {created_attributes} | القيم: {created_values}'
        ))

        # ==========================================
        # إنشاء المنتجات
        # ==========================================
        self.stdout.write('\n🛍️ بدء إنشاء المنتجات...')
        
        products_data = [
            # هواتف ذكية
            {
                'name': 'iPhone 15 Pro Max',
                'category': 'هواتف ذكية',
                'description': 'أحدث هاتف من آبل مع شاشة Super Retina XDR ومعالج A17 Pro القوي.',
                'brand': 'Apple',
                'variants': [
                    {'name': '128GB - أسود', 'sku': 'IP15PM-128-BLK', 'price': 149999, 'old_price': 169999, 'stock': 25, 'attrs': {'Storage': '128GB', 'Color': 'Black'}},
                    {'name': '256GB - أبيض', 'sku': 'IP15PM-256-WHT', 'price': 169999, 'old_price': 189999, 'stock': 30, 'attrs': {'Storage': '256GB', 'Color': 'White'}},
                    {'name': '512GB - ذهبي', 'sku': 'IP15PM-512-GLD', 'price': 199999, 'old_price': 219999, 'stock': 15, 'attrs': {'Storage': '512GB', 'Color': 'Gold'}},
                ]
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'category': 'هواتف ذكية',
                'description': 'هاتف سامسونج الرائد مع قلم S Pen مدمج وشاشة Dynamic AMOLED 2X.',
                'brand': 'Samsung',
                'variants': [
                    {'name': '256GB - أسود', 'sku': 'S24U-256-BLK', 'price': 129999, 'old_price': 149999, 'stock': 40, 'attrs': {'Storage': '256GB', 'Color': 'Black'}},
                    {'name': '512GB - بنفسجي', 'sku': 'S24U-512-PUR', 'price': 149999, 'old_price': 169999, 'stock': 20, 'attrs': {'Storage': '512GB', 'Color': 'Purple'}},
                ]
            },
            {
                'name': 'Xiaomi 14 Ultra',
                'category': 'هواتف ذكية',
                'description': 'هاتف شاومي المميز بكاميرا Leica الاحترافية ومعالج Snapdragon 8 Gen 3.',
                'brand': 'Xiaomi',
                'variants': [
                    {'name': '256GB - أسود', 'sku': 'XM14U-256-BLK', 'price': 89999, 'old_price': 99999, 'stock': 35, 'attrs': {'Storage': '256GB', 'Color': 'Black'}},
                    {'name': '512GB - أبيض', 'sku': 'XM14U-512-WHT', 'price': 99999, 'old_price': 109999, 'stock': 25, 'attrs': {'Storage': '512GB', 'Color': 'White'}},
                ]
            },
            # لابتوب
            {
                'name': 'MacBook Pro 14" M3 Pro',
                'category': 'لابتوب',
                'description': 'لابتوب آفل الاحترافي مع شريحة M3 Pro القوية. شاشة Liquid Retina XDR.',
                'brand': 'Apple',
                'variants': [
                    {'name': '18GB/512GB - فضي', 'sku': 'MBP14-M3P-512', 'price': 249999, 'old_price': 279999, 'stock': 15, 'attrs': {'Processor': 'Apple M3', 'RAM': '18GB', 'Storage': '512GB SSD'}},
                    {'name': '36GB/1TB - فضي', 'sku': 'MBP14-M3P-1TB', 'price': 299999, 'old_price': 329999, 'stock': 10, 'attrs': {'Processor': 'Apple M3', 'RAM': '36GB', 'Storage': '1TB SSD'}},
                ]
            },
            {
                'name': 'Dell XPS 15',
                'category': 'لابتوب',
                'description': 'لابتوب ديل المميز بتصميم أنيق وشاشة OLED مذهلة.',
                'brand': 'Dell',
                'variants': [
                    {'name': '16GB/512GB - فضي', 'sku': 'XPS15-I7-512', 'price': 179999, 'old_price': 199999, 'stock': 12, 'attrs': {'Processor': 'Intel Core i7', 'RAM': '16GB', 'Storage': '512GB SSD'}},
                ]
            },
            # سماعات
            {
                'name': 'AirPods Pro 2',
                'category': 'سماعات',
                'description': 'سماعات آبل اللاسلكية مع إلغاء الضوضاء النشط وصوت مكاني.',
                'brand': 'Apple',
                'variants': [
                    {'name': 'أبيض', 'sku': 'APP2-WHT', 'price': 29999, 'old_price': 34999, 'stock': 50, 'attrs': {'Type': 'In-Ear', 'Color': 'White'}},
                ]
            },
            {
                'name': 'Sony WH-1000XM5',
                'category': 'سماعات',
                'description': 'أفضل سماعات لإلغاء الضوضاء في العالم. صوت Hi-Fi.',
                'brand': 'Sony',
                'variants': [
                    {'name': 'أسود', 'sku': 'SONY-XM5-BLK', 'price': 44999, 'old_price': 52999, 'stock': 30, 'attrs': {'Type': 'Over-Ear', 'Color': 'Black'}},
                    {'name': 'فضي', 'sku': 'SONY-XM5-SLV', 'price': 44999, 'old_price': 52999, 'stock': 25, 'attrs': {'Type': 'Over-Ear', 'Color': 'Silver'}},
                ]
            },
            # ساعات ذكية
            {
                'name': 'Apple Watch Series 9',
                'category': 'ساعات ذكية',
                'description': 'ساعة آبل الذكية الجديدة مع ميزة Double Tap.',
                'brand': 'Apple',
                'variants': [
                    {'name': '45mm GPS - أسود', 'sku': 'AW9-45-BLK', 'price': 54999, 'old_price': 59999, 'stock': 20, 'attrs': {'Display': 'OLED'}},
                    {'name': '45mm GPS - فضي', 'sku': 'AW9-45-SLV', 'price': 54999, 'old_price': 59999, 'stock': 18, 'attrs': {'Display': 'OLED'}},
                ]
            },
            {
                'name': 'Samsung Galaxy Watch 6',
                'category': 'ساعات ذكية',
                'description': 'ساعة سامسونج الذكية بنظام Wear OS.',
                'brand': 'Samsung',
                'variants': [
                    {'name': '44mm - أسود', 'sku': 'GW6-44-BLK', 'price': 34999, 'old_price': 39999, 'stock': 35, 'attrs': {'Display': 'AMOLED'}},
                ]
            },
            # تلفزيونات
            {
                'name': 'Samsung Neo QLED 65"',
                'category': 'تلفزيونات',
                'description': 'تلفزيون سامسونج 4K مع تقنية Mini LED.',
                'brand': 'Samsung',
                'variants': [
                    {'name': '65 بوصة', 'sku': 'SAM-QLED-65', 'price': 299999, 'old_price': 349999, 'stock': 8, 'attrs': {'Screen Size': '65"', 'Resolution': '4K UHD'}},
                ]
            },
            {
                'name': 'LG OLED 55" C3',
                'category': 'تلفزيونات',
                'description': 'تلفزيون LG OLED بألوان حقيقية وسود عميق.',
                'brand': 'LG',
                'variants': [
                    {'name': '55 بوصة', 'sku': 'LG-OLED-C3-55', 'price': 249999, 'old_price': 279999, 'stock': 12, 'attrs': {'Screen Size': '55"', 'Resolution': '4K UHD'}},
                ]
            },
            # ثلاجات
            {
                'name': 'Samsung Refrigerator Side by Side',
                'category': 'ثلاجات',
                'description': 'ثلاجة سامسونج بابين بسعة 600 لتر.',
                'brand': 'Samsung',
                'variants': [
                    {'name': '600L - فضي', 'sku': 'SAM-REF-SS-600', 'price': 189999, 'old_price': 219999, 'stock': 10, 'attrs': {'Capacity': '600L', 'Type': 'Side by Side'}},
                ]
            },
            # غسالات
            {
                'name': 'LG Washing Machine Front Load',
                'category': 'غسالات',
                'description': 'غسالة LG أمامية بسعة 9 كجم.',
                'brand': 'LG',
                'variants': [
                    {'name': '9kg - أبيض', 'sku': 'LG-WM-FL-9', 'price': 89999, 'old_price': 99999, 'stock': 15, 'attrs': {'Capacity': '9kg', 'Type': 'Front Load'}},
                ]
            },
            # ملابس رجالي
            {
                'name': 'Nike Dri-FIT T-Shirt',
                'category': 'رجالي',
                'description': 'تيشيرت نايكي رياضي بتقنية Dri-FIT للتهوية.',
                'brand': 'Nike',
                'variants': [
                    {'name': 'S - أسود', 'sku': 'NK-DRIFT-S-BLK', 'price': 4999, 'stock': 100, 'attrs': {'Size': 'S', 'Color': 'Black'}},
                    {'name': 'M - أسود', 'sku': 'NK-DRIFT-M-BLK', 'price': 4999, 'stock': 120, 'attrs': {'Size': 'M', 'Color': 'Black'}},
                    {'name': 'L - أبيض', 'sku': 'NK-DRIFT-L-WHT', 'price': 4999, 'stock': 80, 'attrs': {'Size': 'L', 'Color': 'White'}},
                    {'name': 'XL - أزرق', 'sku': 'NK-DRIFT-XL-BLU', 'price': 4999, 'stock': 60, 'attrs': {'Size': 'XL', 'Color': 'Blue'}},
                ]
            },
            {
                'name': 'Adidas Originals Hoodie',
                'category': 'رجالي',
                'description': 'هودي أديداس كلاسيكي بخطوط الثلاثة المميزة.',
                'brand': 'Adidas',
                'variants': [
                    {'name': 'M - أسود', 'sku': 'AD-HOOD-M-BLK', 'price': 12999, 'old_price': 15999, 'stock': 50, 'attrs': {'Size': 'M', 'Color': 'Black'}},
                    {'name': 'L - رمادي', 'sku': 'AD-HOOD-L-GRY', 'price': 12999, 'old_price': 15999, 'stock': 45, 'attrs': {'Size': 'L', 'Color': 'Grey'}},
                ]
            },
            # أحذية
            {
                'name': 'Nike Air Max 270',
                'category': 'أحذية',
                'description': 'حذاء نايكي الرسمي مع وسادة Air Max.',
                'brand': 'Nike',
                'variants': [
                    {'name': '42 - أسود/أبيض', 'sku': 'NK-AM270-42-BW', 'price': 24999, 'old_price': 29999, 'stock': 20, 'attrs': {'Size': '42', 'Type': 'Sneakers'}},
                    {'name': '43 - أسود/أبيض', 'sku': 'NK-AM270-43-BW', 'price': 24999, 'old_price': 29999, 'stock': 18, 'attrs': {'Size': '43', 'Type': 'Sneakers'}},
                    {'name': '44 - أسود/أبيض', 'sku': 'NK-AM270-44-BW', 'price': 24999, 'old_price': 29999, 'stock': 15, 'attrs': {'Size': '44', 'Type': 'Sneakers'}},
                ]
            },
            # عطور
            {
                'name': 'Bleu de Chanel',
                'category': 'عطور',
                'description': 'عطر شانيل الرجالي الكلاسيكي.',
                'brand': 'Chanel',
                'variants': [
                    {'name': '100ml', 'sku': 'CHANEL-BLEU-100', 'price': 45000, 'old_price': 52000, 'stock': 25, 'attrs': {'Volume': '100ml', 'Gender': 'Men'}},
                    {'name': '50ml', 'sku': 'CHANEL-BLEU-50', 'price': 32000, 'old_price': 38000, 'stock': 30, 'attrs': {'Volume': '50ml', 'Gender': 'Men'}},
                ]
            },
            {
                'name': 'Dior Sauvage',
                'category': 'عطور',
                'description': 'عطر ديور سافاج الشهير.',
                'brand': 'Dior',
                'variants': [
                    {'name': '100ml', 'sku': 'DIOR-SVG-100', 'price': 42000, 'old_price': 48000, 'stock': 28, 'attrs': {'Volume': '100ml', 'Gender': 'Men'}},
                ]
            },
            # معدات رياضية
            {
                'name': 'Dumbbells Set',
                'category': 'معدات رياضية',
                'description': 'طقم دمبل قابل للتعديل.',
                'brand': 'Generic',
                'variants': [
                    {'name': '10kg', 'sku': 'DBL-SET-10', 'price': 15000, 'stock': 20, 'attrs': {'Weight': '10kg'}},
                    {'name': '20kg', 'sku': 'DBL-SET-20', 'price': 25000, 'stock': 15, 'attrs': {'Weight': '20kg'}},
                ]
            },
            {
                'name': 'Yoga Mat Premium',
                'category': 'معدات رياضية',
                'description': 'سجادة يوجا احترافية.',
                'brand': 'Generic',
                'variants': [
                    {'name': 'بنفسجي', 'sku': 'YOGA-MAT-PUR', 'price': 4999, 'stock': 50, 'attrs': {}},
                    {'name': 'أزرق', 'sku': 'YOGA-MAT-BLU', 'price': 4999, 'stock': 45, 'attrs': {}},
                ]
            },
        ]

        created_products = 0
        created_variants = 0
        
        for prod_data in products_data:
            try:
                category = Category.objects.get(name=prod_data['category'])
            except Category.DoesNotExist:
                continue
            
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'seller': admin_user,
                    'category': category,
                    'description': prod_data['description'],
                    'brand': prod_data.get('brand', ''),
                    'is_active': True,
                    'is_featured': random.choice([True, False]),
                    'Specifications': f'<p>{prod_data["description"]}</p>',
                }
            )
            
            if created:
                created_products += 1
                self.stdout.write(f'  ✓ منتج: {prod_data["name"]}')
                
                # إضافة الصورة إذا تم تحديدها
                if default_image_path and os.path.exists(default_image_path):
                    with open(default_image_path, 'rb') as img_file:
                        product.image.save(
                            os.path.basename(default_image_path),
                            File(img_file),
                            save=True
                        )
                        # إنشاء ProductImage أيضاً
                        ProductImage.objects.create(
                            product=product,
                            image=product.image,
                            is_main=True
                        )
            
            # إنشاء المتغيرات
            for var_data in prod_data['variants']:
                variant, created = ProductVariant.objects.get_or_create(
                    product=product,
                    sku=var_data['sku'],
                    defaults={
                        'name': var_data['name'],
                        'price': var_data['price'],
                        'old_price': var_data.get('old_price', None),
                        'stock': var_data['stock'],
                        'is_active': True,
                    }
                )
                
                if created:
                    created_variants += 1
                    
                    if 'attrs' in var_data:
                        for attr_name, attr_value in var_data['attrs'].items():
                            try:
                                attr = Attribute.objects.get(name=attr_name, category=category)
                                val = AttributeValue.objects.get(attribute=attr, value=attr_value)
                                variant.attributes.add(val)
                            except (Attribute.DoesNotExist, AttributeValue.DoesNotExist):
                                pass

        self.stdout.write(self.style.SUCCESS(
            f'\n📦 المنتجات: {created_products} | المتغيرات: {created_variants}'
        ))
        
        self.stdout.write(self.style.SUCCESS('\n✅ تم إكمال عملية ملء قاعدة البيانات بنجاح!'))
        self.stdout.write('🌐 يمكن الآن تسجيل الدخول بحساب admin لإدارة المنتجات والفئات.')