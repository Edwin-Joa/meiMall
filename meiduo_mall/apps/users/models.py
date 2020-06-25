from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer,BadData
from django.conf import settings
# Create your models here.

class User(AbstractUser):
    mobile = models.CharField(max_length=11,verbose_name='手机号',unique=True)
    email_active = models.BooleanField(default=False,verbose_name='邮箱验证状态')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def generate_verify_email_url(self):
        setializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,expires_in=60*60*24)
        data = {'user_id':self.id,'email':self.email}
        token = setializer.dumps(data).decode()
        verify_url = settings.EMAIL_VERIFY_URL + token
        return verify_url

    @staticmethod
    def check_verify_email_token(token):
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,expires_in=60*60*24)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            user_id = data.get('user_id')
            email = data.get('email')

        try:
            user = User.objects.get(id=user_id,email=email)
        except Exception as e:
            return None
        else:
            return user



