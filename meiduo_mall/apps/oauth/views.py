from django.shortcuts import render
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from QQLoginTool.QQtool import OAuthQQ
from oauth.models import OauthQQUser
import logging
logger = logging.getLogger('django')
from django.contrib.auth import login
from oauth.utils import generate_access_token
# Create your views here.


class QQFirstView(View):
    def get(self,request):
        next = request.GET.get('next')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        login_url = oauth.get_qq_url()

        return JsonResponse({'code':0,'errmsg':'ok','login_rul':login_url})

class QQUserView(View):
    def get(self,request):
        code = request.GET.get('code')
        if not code:
            return JsonResponse({'code':400,'errmsg':'缺少code参数'})
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            access_token = oauth.get_access_token('code')

            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400,'errmsg':'oauth2.0认证失败，即获取请求信息失败'})
        pass

