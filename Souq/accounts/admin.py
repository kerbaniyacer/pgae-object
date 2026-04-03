from django.contrib import admin
from .models import Profile
# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_seller', 'phone', 'wilaya', 'baladia', 'store_name')
    list_filter = ('is_seller', 'wilaya', 'baladia')
    search_fields = ('user__username', 'phone', 'store_name')
    readonly_fields = ('created_at', 'updated_at')

