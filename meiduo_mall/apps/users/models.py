from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer,BadData
from django.conf import settings
from meiduo_mall.utils.BaseModel import BaseModel
# Create your models here.

class User(AbstractUser):
    mobile = models.CharField(max_length=11,verbose_name='手机号',unique=True)
    email_active = models.BooleanField(default=False,verbose_name='邮箱验证状态')

    default_address = models.ForeignKey('Address',related_name='users',null=True,blank=True,on_delete=models.SET_NULL,verbose_name='默认地址')


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


class Address(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='addresses',verbose_name='地址')

    province = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,related_name='procince_addresses',verbose_name='省')
    city = models.ForeignKey('areas.Area',
                             on_delete=models.PROTECT,related_name='city_addresses',verbose_name='市')
    district = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,related_name='district_addresses',verbose_name='区')
    title = models.CharField(max_length=20,verbose_name='地址名称')

    receiver = models.CharField(max_length=20,verbose_name='收件人')

    place = models.CharField(max_length=50,verbose_name='详细地址')

    mobile = models.CharField(max_length=11,verbose_name='手机号')

    tel = models.CharField(max_length=20,
                           null=True,blank=True,default='',verbose_name='固定电话')

    email = models.CharField(max_length=40,
                             null=True,blank=True,default='',verbose_name='电子邮箱')

    is_deleted = models.BooleanField(default=False,verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']


