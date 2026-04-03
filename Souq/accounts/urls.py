from django.urls import path, re_path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    # ============================================
    # AUTH (Accounts)
    # ============================================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
]  
