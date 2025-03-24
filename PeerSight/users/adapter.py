from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """Automatically approve Google logins without asking for signup confirmation."""
        return True
    
    def get_login_redirect_url(self, request):
        """Redirect new users directly to their respective dashboard after Google login."""
        return "/route_user/"
    


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Automatically sign up users who log in with Google
        without showing the intermediate signup page.
        """
        return True  # This skips the `/accounts/3rdparty/signup/` page