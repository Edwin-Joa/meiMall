from django.shortcuts import render
from django.views import View
from django.http import JsonResponse,HttpResponse
from django_redis import get_redis_connection
from meiduo_mall.libs.captcha.captcha import captcha
# from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import ccp_send_sms_code
import logging
from random import randint
logger = logging.getLogger('django')
# Create your views here.


class ImageCodeView(View):
    def get(self,request,uuid):
        text,image = captcha.generate_captcha()
        conn = get_redis_connection('verify_code')
        try:
            conn.setex(f'img_{uuid}',300,text)
        except Exception as e:
            logger.info('写入数据库出错')
            return JsonResponse({'code':400,'errmsg':'写入数据库出错'})
        return HttpResponse(image,content_type='image/jpg')


class SmsCodeView(View):
    def get(self,request,mobile):
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        if not all([image_code_client,uuid]):
            return JsonResponse({'code':400,'errmsg':'缺少必传参数'})

        conn = get_redis_connection('verify_code')
        image_code_server = conn.get(f'img_{uuid}').decode()
        flag = conn.get(f'{mobile}_flag')



        if flag:
            return JsonResponse({'code':400,'errmsg':'请勿频繁发送短信验证码'})

        pl= conn.pipeline()

        try:
            pl.delete(f'img_{uuid}')
        except Exception as e:
            logger.info('访问数据库出错')
            return JsonResponse({'code':400,'errmsg':'访问数据库出错'})

        if not image_code_server:
            return JsonResponse({'code':400,'errmsg':'图形验证码失效'})

        try:
            pl.setex(f'{mobile}_flag',60,1)
        except Exception as e:
            logger.info('sms_flag写入失败')

        if image_code_client.lower() != image_code_server.lower():
            return JsonResponse({'code':400,'errmsg':'验证码错误'})

        sms_code = '%06d'%(randint(0,999999))
        logger.info('sms_code:',sms_code)

        try:
            pl.setex(f'sms_code_{mobile}',300,sms_code)
        except Exception as e:
            logger.info('手机验证码写入失败')

        pl.execute()

        # CCP().send_template_sms('15173161429',[sms_code,5],1)
        ccp_send_sms_code.delay(mobile,sms_code)

        return JsonResponse({'code':0,'errmsg':'短信发送成功'})