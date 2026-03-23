from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Wird beim ersten Social/OIDC-Login aufgerufen.
        Legt lokalen User an und setzt is_active=False.
        """
        user = sociallogin.user
        data = sociallogin.account.extra_data or {}

        # E-Mail aus OIDC-Daten holen
        email = (
            data.get("email")
            or data.get("preferred_username")
            or user.email
        )

        # Namen aus OIDC-Daten holen
        first_name = data.get("given_name", user.first_name or "")
        last_name = data.get("family_name", user.last_name or "")

        # Fallback-Username aus E-Mail
        username = user.username
        if not username:
            if email:
                username = email.split("@")[0]
            else:
                username = f"oidc_user_{sociallogin.account.uid}"

    
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exclude(pk=user.pk).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user.username = username
        user.email = email or ""
        user.first_name = first_name
        user.last_name = last_name

       
        user.is_active = False

        user.save()
        sociallogin.save(request)

        return user