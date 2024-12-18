from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import AuthUser, JWTAuthentication
from rest_framework_simplejwt.tokens import Token

from core import settings
from terminal_api.models import User


def enforce_csrf(request):
    """
    Enforce CSRF validation.
    """
    check = CSRFCheck(None)
    # populates request.META['CSRF_COOKIE'], which is used in process_view()
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        # CSRF failed, bail with explicit error message
        raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")


class CookieJWTAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = User

    def authenticate(self, request):
        header = self.get_header(request)

        print(request.COOKIES, header is None)
        if header is None:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"]) or None
        else:
            raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        # enforce_csrf(request)
        return self.get_user(validated_token), validated_token
