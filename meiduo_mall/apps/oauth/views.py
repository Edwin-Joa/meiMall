from django.shortcuts import render
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from QQLoginTool.QQtool import OAuthQQ
from apps.oauth.models import OauthQQUser
import logging,json,re
logger = logging.getLogger('django')
from apps.users.models import User
from django.contrib.auth import login
from .utils import generate_access_token,check_access_token
from apps.carts.utils import merge_cart_cookie_to_redis
# Create your views here.


class QQFirstView(View):
    def get(self,request):
        next = request.GET.get('next')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        login_url = oauth.get_qq_url()
        # print(login_url)
        return JsonResponse({'code':0,'errmsg':'ok','login_url':login_url})

class QQUserView(View):
    def get(self,request):
        code = request.GET.get('code')
        if not code:
            return JsonResponse({'code':400,'errmsg':'缺少code参数'})
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next,)
        try:
            access_token = oauth.get_access_token(code)

            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400,'errmsg':'oauth2.0认证失败，即获取请求信息失败'})

        try:
            qq_user = OauthQQUser.objects.get(openid=openid)
        except OauthQQUser.DoesNotExist as e:
            # 用户没有绑定，返回加密后对openid —— 前端让用户数据用户名和密码，后续接口再去判断绑定
            token = generate_access_token(openid)
            return JsonResponse({
                'code': 400,
                'errmsg': '未绑定',
                'access_token': token
            })
        else:
            # 如果用户已经绑定了qq，说明用户已经注册过了"美多用户
            login(request, qq_user.user)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('username', qq_user.user.username)
            return response

    def post(self,request):
        dict = json.loads(request.body.decode())
        mobile = dict.get('mobile')
        password = dict.get('password')
        sms_code_client = dict.get('sms_code')
        access_token = dict.get('access_token')

        if not all([mobile,password,sms_code_client]):
            return JsonResponse({'code':400,'errmsg':'缺少必传参数'})
        if not re.match('^1[3-9]\d{9}$',mobile):
            return JsonResponse({'code':400,'errmsg':'电话号码有误'})
        if not re.match('^[a-zA-Z0-9]{8,20}$',password):
            return JsonResponse({'code':400,'errmsg':'密码格式错误'})
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get(f'sms_code_{mobile}')

        if sms_code_server is None:
            return JsonResponse({'code':400,'errmsg':'验证码失效'})
        if sms_code_client != sms_code_server.decode():
            return JsonResponse({'code':400,'errmsg':'验证码有误'})
        openid = check_access_token(access_token)

        if not openid:
            return JsonResponse({'code':400,'errmsg':'缺少openid'})
        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            user = User.objects.create_user(username=mobile,password=password,mobile=mobile)
        else:
            if not user.check_password(password):
                return JsonResponse({'code':400,'errmsg':'输入密码有误'})
        try:
            OauthQQUser.objects.create(openid=openid,user=user)
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'存入数据库失败'})
        login(request,user)
        response = JsonResponse({'code':0,'errmsg':'ok'})
        response.set_cookie('username',user.username,max_age=3600*24*14)
        response = merge_cart_cookie_to_redis(request=request,user=user,response=response)


        return response

