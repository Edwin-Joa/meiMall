from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from django.contrib.auth import login,authenticate
from .models import User
import logging
import json
import re

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
        return JsonResponse({'code':0,'msg':'ok'})


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

        return JsonResponse({'code':0,'msg':'ok'})

