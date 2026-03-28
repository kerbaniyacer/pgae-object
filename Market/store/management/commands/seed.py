from django.core.management.base import BaseCommand
from store.models import Category, Attribute, Product, ProductVariant, ProductImage, User, Profile
from decimal import Decimal
import random


# ============================================
# الفئات بالعربية والخصائص بالإنجليزية
# ============================================

DATA = {
    "الإلكترونيات": {
        "أجهزة الكمبيوتر": [
            "RAM", "Storage", "Processor", "GPU",
            "Screen Size", "Operating System"
        ],
        "الهواتف": [
            "RAM", "Storage", "Battery",
            "Camera", "Operating System"
        ],
        "الإكسسوارات": [
            "Type", "Compatibility", "Brand"
        ]
    },

    "الأزياء": {
        "ملابس رجالية": [
            "Size", "Color", "Material", "Brand"
        ],
        "ملابس نسائية": [
            "Size", "Color", "Material", "Brand"
        ],
        "الأحذية": [
            "Size", "Color", "Material", "Gender"
        ]
    },

    "المنزل والمطبخ": {
        "الأثاث": [
            "Material", "Dimensions", "Color", "Weight"
        ],
        "أجهزة المطبخ": [
            "Power", "Capacity", "Brand", "Voltage"
        ],
        "الديكور": [
            "Style", "Material", "Color"
        ]
    },

    "الجمال والعناية": {
        "العناية بالبشرة": [
            "Skin Type", "Ingredients", "Volume"
        ],
        "مستحضرات التجميل": [
            "Color", "Type", "Brand"
        ],
        "العناية بالشعر": [
            "Hair Type", "Volume", "Ingredients"
        ]
    },

    "الرياضة": {
        "معدات اللياقة": [
            "Weight", "Material", "Usage"
        ],
        "ملابس رياضية": [
            "Size", "Material", "Gender"
        ]
    },

    "السيارات": {
        "اكسسوارات السيارات": [
            "Compatibility", "Brand", "Material"
        ],
        "أدوات": [
            "Type", "Usage", "Material"
        ]
    },

    "الألعاب": {
        "ألعاب الأطفال": [
            "Age Range", "Material", "Type"
        ],
        "تعليمية": [
            "Skill Level", "Age Range"
        ]
    },

    "الكتب": {
        "تعليمية": [
            "Author", "Language", "Pages"
        ],
        "روايات": [
            "Author", "Genre", "Language"
        ]
    },

    "الحيوانات الأليفة": {
        "طعام": [
            "Animal Type", "Weight", "Ingredients"
        ],
        "اكسسوارات": [
            "Material", "Usage"
        ]
    },

    "البناء والأدوات": {
        "أدوات كهربائية": [
            "Power", "Brand", "Voltage"
        ],
        "أدوات يدوية": [
            "Material", "Usage", "Type"
        ]
    },

    "المواد الغذائية": {
        "مشروبات": [
            "Volume", "Flavor", "Ingredients"
        ],
        "وجبات خفيفة": [
            "Weight", "Flavor", "Ingredients"
        ]
    }
}


# ============================================
# منتجات تجريبية
# ============================================

SAMPLE_PRODUCTS = [
    {
        "name": "آيفون 15 برو ماكس",
        "category": "الهواتف",
        "parent": "الإلكترونيات",
        "price": Decimal("150000"),
        "old_price": Decimal("165000"),
        "stock": 25,
        "brand": "Apple",
        "description": "أحدث هاتف من آبل مع شريحة A17 Pro وكاميرا 48 ميجابكسل"
    },
    {
        "name": "سامسونج جالكسي S24 الترا",
        "category": "الهواتف",
        "parent": "الإلكترونيات",
        "price": Decimal("130000"),
        "old_price": Decimal("145000"),
        "stock": 30,
        "brand": "Samsung",
        "description": "هاتف ذكي متطور مع قلم S Pen مدمج وشاشة Dynamic AMOLED"
    },
    {
        "name": "لابتوب HP Pavilion",
        "category": "أجهزة الكمبيوتر",
        "parent": "الإلكترونيات",
        "price": Decimal("95000"),
        "old_price": None,
        "stock": 15,
        "brand": "HP",
        "description": "لابتوب للأعمال مع معالج Intel Core i7 وذاكرة 16GB"
    },
    {
        "name": "سماعات AirPods Pro 2",
        "category": "الإكسسوارات",
        "parent": "الإلكترونيات",
        "price": Decimal("35000"),
        "old_price": Decimal("42000"),
        "stock": 50,
        "brand": "Apple",
        "description": "سماعات لاسلكية مع خاصية إلغاء الضوضاء النشط"
    },
    {
        "name": "قميص رجالي أنيق",
        "category": "ملابس رجالية",
        "parent": "الأزياء",
        "price": Decimal("4500"),
        "old_price": Decimal("6000"),
        "stock": 100,
        "brand": "Zara",
        "description": "قميص قطني أنيق مناسب للعمل والمناسبات"
    },
    {
        "name": "فستان سهرة أنيق",
        "category": "ملابس نسائية",
        "parent": "الأزياء",
        "price": Decimal("12000"),
        "old_price": None,
        "stock": 40,
        "brand": "H&M",
        "description": "فستان سهرة أنيق بتصميم عصري"
    },
    {
        "name": "حذاء رياضي نايكي",
        "category": "الأحذية",
        "parent": "الأزياء",
        "price": Decimal("18000"),
        "old_price": Decimal("22000"),
        "stock": 60,
        "brand": "Nike",
        "description": "حذاء رياضي مريح مع تقنية Air Max"
    },
    {
        "name": "كنبة مودرن",
        "category": "الأثاث",
        "parent": "المنزل والمطبخ",
        "price": Decimal("85000"),
        "old_price": None,
        "stock": 10,
        "brand": "IKEA",
        "description": "كنبة مريحة بتصميم مودرن وألوان متنوعة"
    },
    {
        "name": "خلاط كهربائي",
        "category": "أجهزة المطبخ",
        "parent": "المنزل والمطبخ",
        "price": Decimal("8500"),
        "old_price": Decimal("10000"),
        "stock": 35,
        "brand": "Philips",
        "description": "خلاط قوي متعدد الاستخدامات"
    },
    {
        "name": "كريم ترطيب البشرة",
        "category": "العناية بالبشرة",
        "parent": "الجمال والعناية",
        "price": Decimal("2500"),
        "old_price": None,
        "stock": 80,
        "brand": "Nivea",
        "description": "كريم ترطيب للبشرة الجافة والمتحسسة"
    },
    {
        "name": "دومبل 10 كجم",
        "category": "معدات اللياقة",
        "parent": "الرياضة",
        "price": Decimal("5000"),
        "old_price": Decimal("6500"),
        "stock": 45,
        "brand": "Decathlon",
        "description": "دومبل مطلي بالكروم وزن 10 كجم"
    },
    {
        "name": "غطاء سيارة مقاوم للماء",
        "category": "اكسسوارات السيارات",
        "parent": "السيارات",
        "price": Decimal("3500"),
        "old_price": None,
        "stock": 25,
        "brand": "AutoGuard",
        "description": "غطاء سيارة مقاوم للماء والأشعة فوق البنفسجية"
    },
    {
        "name": "لعبة ليغو للمبدعين",
        "category": "ألعاب الأطفال",
        "parent": "الألعاب",
        "price": Decimal("7500"),
        "old_price": Decimal("9000"),
        "stock": 55,
        "brand": "LEGO",
        "description": "مجموعة ليغو للبناء والإبداع - 500 قطعة"
    },
    {
        "name": "رواية البؤساء",
        "category": "روايات",
        "parent": "الكتب",
        "price": Decimal("1200"),
        "old_price": None,
        "stock": 100,
        "brand": "فيكتور هوغو",
        "description": "رواية أدبية كلاسيكية من روائع الأدب العالمي"
    },
    {
        "name": "طعام قطط رويال كانين",
        "category": "طعام",
        "parent": "الحيوانات الأليفة",
        "price": Decimal("4500"),
        "old_price": Decimal("5500"),
        "stock": 70,
        "brand": "Royal Canin",
        "description": "طعام جاف للقطط البالغة - 2 كجم"
    },
]


class Command(BaseCommand):
    help = "تعبئة قاعدة البيانات بالفئات والخصائص والمنتجات التجريبية"

    def add_arguments(self, parser):
        parser.add_argument(
            '--products',
            action='store_true',
            help='إضافة منتجات تجريبية',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='حذف البيانات القديمة قبل التعبئة',
        )

    def handle(self, *args, **kwargs):
        
        clean = kwargs.get('clean', False)
        add_products = kwargs.get('products', False)

        if clean:
            self.stdout.write("🧹 جاري تنظيف البيانات القديمة...")
            ProductImage.objects.all().delete()
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            Attribute.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("✓ تم حذف البيانات القديمة"))

        # ============================================
        # إنشاء الفئات والخصائص
        # ============================================
        
        self.stdout.write("📁 جاري إنشاء الفئات والخصائص...")
        
        categories_count = 0
        attributes_count = 0

        for main_cat_name, subcats in DATA.items():
            # إنشاء الفئة الرئيسية
            main_category, created = Category.objects.get_or_create(
                name=main_cat_name,
                defaults={'is_active': True}
            )
            if created:
                categories_count += 1

            for subcat_name, attributes in subcats.items():
                # إنشاء الفئة الفرعية
                sub_category, created = Category.objects.get_or_create(
                    name=subcat_name,
                    parent=main_category,
                    defaults={'is_active': True}
                )
                if created:
                    categories_count += 1

                # إنشاء الخصائص
                attr_objs = []
                for attr_name in attributes:
                    # التحقق من عدم وجود الخاصية مسبقاً
                    if not Attribute.objects.filter(
                        name=attr_name, 
                        category=sub_category
                    ).exists():
                        attr_objs.append(Attribute(
                            name=attr_name,
                            category=sub_category
                        ))

                if attr_objs:
                    Attribute.objects.bulk_create(attr_objs)
                    attributes_count += len(attr_objs)

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ تم إنشاء {categories_count} فئة و {attributes_count} خاصية"
            )
        )

        # ============================================
        # إنشاء منتجات تجريبية
        # ============================================

        if add_products:
            self.stdout.write("🛍️ جاري إنشاء المنتجات التجريبية...")
            
            # الحصول على مستخدم بائع (أو إنشاء واحد)
            seller = User.objects.filter(profile__is_seller=True).first()
            
            if not seller:
                # إنشاء مستخدم بائع تجريبي
                seller = User.objects.create_user(
                    username='seller_demo',
                    email='seller@souq.dz',
                    password='demo123456'
                )
                Profile.objects.create(
                    user=seller,
                    is_seller=True,
                    store_name='متجر تجريبي',
                    store_description='متجر تجريبي للعرض',
                    phone='0555123456'
                )
                self.stdout.write(self.style.SUCCESS("✓ تم إنشاء مستخدم بائع تجريبي"))

            products_count = 0
            variants_count = 0

            for product_data in SAMPLE_PRODUCTS:
                # البحث عن الفئة
                try:
                    parent_cat = Category.objects.get(
                        name=product_data['parent'], 
                        parent__isnull=True
                    )
                    category = Category.objects.get(
                        name=product_data['category'],
                        parent=parent_cat
                    )
                except Category.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ لم يتم العثور على فئة: {product_data['category']}")
                    )
                    continue

                # التحقق من عدم وجود المنتج مسبقاً
                if Product.objects.filter(name=product_data['name']).exists():
                    continue

                # إنشاء المنتج
                product = Product.objects.create(
                    name=product_data['name'],
                    category=category,
                    seller=seller,
                    description=product_data['description'],
                    price=product_data['price'],
                    old_price=product_data.get('old_price'),
                    stock=product_data['stock'],
                    brand=product_data.get('brand', ''),
                    is_active=True,
                    is_featured=random.choice([True, False, False]),
                )

                # إنشاء متغير افتراضي للمنتج
                ProductVariant.objects.create(
                    product=product,
                    name='افتراضي',
                    price=product.price,
                    stock=product.stock,
                    sku=f'{product.id}-default'
                )

                products_count += 1
                variants_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ تم إنشاء {products_count} منتج و {variants_count} متغير"
                )
            )

        # ============================================
        # ملخص
        # ============================================
        
        total_categories = Category.objects.count()
        total_attributes = Attribute.objects.count()
        total_products = Product.objects.count()
        total_variants = ProductVariant.objects.count()

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("📊 ملخص قاعدة البيانات:"))
        self.stdout.write(f"  📁 الفئات: {total_categories}")
        self.stdout.write(f"  ⚙️ الخصائص: {total_attributes}")
        self.stdout.write(f"  🛍️ المنتجات: {total_products}")
        self.stdout.write(f"  📦 المتغيرات: {total_variants}")
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("🔥 تمت التعبئة بنجاح!"))
