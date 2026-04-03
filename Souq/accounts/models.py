from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
