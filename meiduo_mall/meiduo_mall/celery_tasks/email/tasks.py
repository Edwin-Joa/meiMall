from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.getLogger('django')
from meiduo_mall.celery_tasks.main import celery_app

@celery_app.task(name='send_verify_email')
def send_verify_email(to_email,verify_url):
    subject = '美多商城邮箱验证'
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)

    result = send_mail(subject,'',settings.EMAIL_FROM,[to_email,'edwin_joa@163.com'],html_message=html_message)
    return result



