from django.contrib.auth.backends import ModelBackend
import re
from apps.users.models import User


def get_user_by_account(account):
    try:
        if re.match('1[3-9]\d{9}',account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except Exception as e:
        return None
    else:
        return user

class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)

        if user and user.check_password(password):
            return user








