from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from store.views import error_view, handler404_view, handler500_view, handler403_view, handler400_view

handler404 = 'store.views.handler404_view'
handler500 = 'store.views.handler500_view'
handler403 = 'store.views.handler403_view'
handler400 = 'store.views.handler400_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', include('accounts.urls')),
    path('', include('store.urls')),
    path('error/<int:error_code>/', error_view, name='error_page'),
]

# ⭐ أضف الميديا أولاً قبل الـ catch-all
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])