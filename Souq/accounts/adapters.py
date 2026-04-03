from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        email = sociallogin.user.email

        if not email:
            return

        process = sociallogin.state.get('process')

        try:
            existing_user = User.objects.get(email=email)

            # 🔥 تسجيل دخول
            if process == 'login':
                sociallogin.connect(request, existing_user)
                return  # يكمل ويحول حسب LOGIN_REDIRECT_URL

            # 🔥 تسجيل جديد
            elif process == 'signup':
                sociallogin.connect(request, existing_user)

        except User.DoesNotExist:
            # 🔥 مستخدم جديد
            request.session['sociallogin'] = sociallogin.serialize()
            raise ImmediateHttpResponse(redirect('/complete-profile/'))