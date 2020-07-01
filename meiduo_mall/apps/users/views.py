from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from django.contrib.auth import login,authenticate,logout
from .models import User
from apps.goods.models import SKU
import logging
import json
import re
from meiduo_mall.celery_tasks.email.tasks import send_verify_email
from apps.carts.utils import merge_cart_cookie_to_redis


logger = logging.getLogger('django')
# Create your views here.



class UsernameCountView(View):
    def get(self,request,username):
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            logger.info('连接数据库失败')
            return JsonResponse({'code':400,'errmsg':'数据库访问失败'})

        return JsonResponse({'code':0,'errmsg':'ok','count':count})

class MobileCountView(View):
    def get(self,request,mobile):
        try:
            count = User.objects.filter(username=mobile).count()
        except Exception as e:
            logger.info('连接数据库失败')
            return JsonResponse({'code':400,'errmsg':'数据库访问失败'})

        return JsonResponse({'code':0,'errmsg':'ok','count':count})


class RegisterView(View):
    def post(self,request):
        # 获取参数 前端采用json数据的传输方式
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        sms_code_client = dict.get('sms_code')
        allow = dict.get('allow')

        redis_conn = get_redis_connection('verify_code')

        # 校验参数
        if not all([username,password,password2,mobile,sms_code_client,allow]):
            return JsonResponse({'code':400,'errmsg':'缺少必传参数'})

        # 检验用户名
        # 由于前端和路由匹配的过程中已经进行过正则匹配判断，所以这里对某些参数的校验可以省略

        # 校验密码
        if password != password2:
            return JsonResponse({'code':400,'errmsg':'两次密码输入不同'})

        # 校验手机号码

        # 校验短信验证码
        sms_code_server = redis_conn.get(f'sms_code_{mobile}')

        if sms_code_client != sms_code_server.decode():
            return JsonResponse({'code':400,'errmsg':'短信验证码有误'})

        # 将用户信息存入数据库
        try:
            user = User.objects.create_user(username=username,password=password,mobile=mobile)
        except Exception as e:
            logger.info('用户信息写入失败')
        # 状态保持，将user的信息通过session写入redis数据库，并sessionid存入cookie
        login(request,user)
        #响应结果
        response = JsonResponse({'code':0,'msg':'ok'})
        response.set_cookie('username',user.username,max_age=3600*24*14)

        return response


class LoginView(View):
    def post(self,request):
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        remembered = dict.get('remembered')

        if not all([username,password]):
            return JsonResponse({'code':400,'errmsg':'缺少必传参数'})

        # 自己写的验证登录方式
        # count = User.objects.filter(username=username).count()
        # if count == 0:
        #     return JsonResponse({'code':400,'errmsg':'请先注册用户账号'})
        # user = User.objects.filter(username=username)
        # pw_server = user.get(password)
        #
        # if password != pw_server:
        #     return JsonResponse({'code':400,'errmsg':'密码错误'})

        #
        user = authenticate(username=username,password=password)
        if user is None:
            return JsonResponse({'code':400,'errmsg':'用户名或密码错误'})

        login(request,user)

        if remembered != True:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        response = JsonResponse({'code':0,'msg':'ok'})
        response.set_cookie('username',user.username,max_age=3600*24*14)

        response = merge_cart_cookie_to_redis(request=request,user=user,response=response)


        return response


class LogoutView(View):
    def delete(self,request):
        logout(request)

        response = JsonResponse({'code':0,'errmsg':'ok'})
        response.delete_cookie('username')
        return response

from meiduo_mall.utils.views import LoginRequiredMixin,my_decorator
# from django.utils.decorators import method_decorator
# from django.contrib.auth.mixins import LoginRequiredMixin

class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):
        print('用户中心函数')
        info_data = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active':request.user.email_active
        }


        response = JsonResponse({'code':0,'errmsg':'ok','info_data':info_data})
        return response


class EmailView(View):
    def put(self,request):
        dict = json.loads(request.body.decode())
        email = dict.get('email')
        if not email:
            return JsonResponse({'code':400,'errmsg':'缺少邮箱参数'})
        if not re.match('^[a-z0-9A-Z]+[.-/]*[a-z0-9A-Z]+@[0-9a-zA-Z]+[.-/]*[a-zA-Z]+$',email):
            return JsonResponse({'code':400,'errmsg':'邮箱格式错误'})
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400,'errmsg':'添加邮箱失败'})

        # email = '<' + email + '>'
        verify_url = request.user.generate_verify_email_url()
        send_verify_email.delay(email,verify_url)

        return JsonResponse({'code':0,'errmsg':'添加邮箱成功'})


class VerifyEmailView(View):
    def put(self,request):
        token = request.GET.get('token')
        if not token:

            return JsonResponse({'code':400,'errmsg':'缺少token'})
        user = User.check_verify_email_token(token)
        if not user:
            return JsonResponse({'code':400,'errmsg':'无效的token'})
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400,'errmsg':'激活邮件失败'})
        return JsonResponse({'code':0,'errmsg':'ok'})


class UserBrowseHistory(View):
    def post(self,request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        user_id = request.user.id
        # 检验商品是否存在
        try:
            SKU.objects.filter(pk=sku_id)
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'商品已售罄'})

        conn = get_redis_connection('history')
        pl = conn.pipeline()

        pl.lrem(f'history_{user_id}',0,sku_id)
        pl.lpush(f'history_{user_id}',sku_id)
        pl.ltrim(f'history_{user_id}',0,4)

        pl.execute()

        return JsonResponse({'code':0,'errmsg':'ok'})

    def get(self,request):
        conn = get_redis_connection('history')
        sku_ids = conn.lrange(f'history_{request.user.id}',0,-1)

        skus = []

        for sku_id in sku_ids:
            try:
                sku = SKU.objects.get(pk=sku_id)
            except Exception as e:
                continue
            skus.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image_url,
                'price':sku.price
            })

        return JsonResponse({'code':0,'errmsg':'ok','skus':skus})


