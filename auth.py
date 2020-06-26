from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .models import MicrosoftUser


User = get_user_model()

class MSALAuthBackend(ModelBackend):
    def authenticate(self, request, oid=None):
        if not oid:
            return None

        try:
            return MicrosoftUser.objects.get(oid=oid).user
        except MicrosoftUser.DoesNotExist:
            return None


    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
