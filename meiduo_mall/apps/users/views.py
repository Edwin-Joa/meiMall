from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from .models import User
import logging
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