from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.core.cache import cache
from django.contrib.auth import login,logout
from .models import Area
from apps.users.models import Address
from meiduo_mall.utils.views import LoginRequiredMixin
import json,re
import logging
logger = logging.getLogger('django')


# Create your views here.

class ProvinceAreaView(View):
    def get(self,request):
        province_list = cache.get('province_list')

        if not province_list:
            try:
                province_list = []
                q_province = Area.objects.filter(parent__isnull=True)

                for p in q_province:
                    province_list.append({'id':p.id,'name':p.name})

                cache.set('province_list',province_list,3600)

            except Exception as e:
                return JsonResponse({'code':400,'errmsg':'省区信息获取失败'})

        return JsonResponse({'code':0,'errmsg':'ok','province_list':province_list})


class SubAreaView(View):
    def get(self,request,pk):
        sub_data = cache.get('sub_area_'+str(pk))
        if sub_data is None:
            try:
                q_subs = Area.objects.filter(parent_id=pk)
                parent = Area.objects.get(id=pk)
                sub_list = []
                for s in q_subs:
                    sub_list.append({'id':s.id,'name':s.name})
                sub_data = {'id':parent.id,'name':parent.name,'subs':sub_list}

                cache.set('sub_area_'+str(pk),sub_data,3600)
            except Exception as e:
                return JsonResponse({'code':400,'errmsg':'获取区级数据失败'})

        return JsonResponse({'code':0,'errmsg':'ok','sub_data':sub_data})

class GetAddressView(View):
    def get(self,request):
        addresses = Address.objects.filter(user=request.user,is_deleted=False)
        addresses_list = []
        for i in addresses:
            address_dict = {
                'id':i.id,
                'title':i.title,
                'receiver':i.receiver,
                'province':i.province.name,
                'city':i.city.name,
                'district':i.district.name,
                'place':i.place,
                'mobile':i.mobile,
                'tel':i.tel,
                'email':i.email
            }
            default_address = request.user.default_address
            if default_address.id == i.id:
                addresses_list.insert(0,address_dict)
            else:
                addresses_list.append(address_dict)

        default_id = request.user.default_address_id
        return JsonResponse({'code':0,'errmsg':'ok','addresses':addresses_list,'default_address_id':default_id})


class CreateAddressView(View):
    def post(self,request):
        try:
            count = Address.objects.filter(user=request.user,is_deleted=False).count()
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'获取地址数据出错'})
        if count>20:
            return JsonResponse({'code':400,'errmsg':'超过地址数量上限'})

        dict = json.loads(request.body.decode())
        receiver = dict.get('receiver')
        province_id =dict.get('province_id')
        city_id = dict.get('city_id')
        district_id = dict.get('district_id')
        place = dict.get('place')
        mobile = dict.get('mobile')
        tel = dict.get('tel')
        email = dict.get('email')

        if not all([receiver,province_id,city_id,district_id,place,mobile]):
            return JsonResponse({'code':400,'errmsg':'缺少必传参数'})

        # 参数校验



        try:
            address = Address.objects.create(
                user=request.user,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                title=receiver,
                receiver=receiver,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email)
            if not request.user.default_address:
                request.user.default_address=address
                request.user.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400,'errmsg':'存入数据库出错'})


        form_data = {
            'id':address.id,
            'title':address.title,
            'receiver':address.receiver,
            'province':address.province.name,
            'city':address.city.name,
            'district':address.district.name,
            'place':address.place,
            'mobile':address.mobile,
            'tel':address.tel,
            'email':address.email}

        return JsonResponse({'code':0,'errmsg':'ok','address':form_data})


class UpdateDestroyAddressView(View):
    def put(self,request,address_id):
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                     'errmsg': '地址更新出错'})

        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        return JsonResponse({'code': 0,
                                     'errmsg': 'ok','address':address_dict})


    def delete(self,request,address_id):
        address = Address.objects.get(id=address_id)
        try:
            address.is_deleted=True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                     'errmsg': '删除地址出错'})
        return JsonResponse({'code': 0,
                                     'errmsg': 'ok'})

    def put(self,request,address_id):

        try:
            address = Address.objects.get(id=address_id)
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                     'errmsg': '设置默认地址出错'})

        return JsonResponse({'code': 0,
                                     'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(View):
    def put(self,request,address_id):
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            address = Address.objects.get(id=address_id)
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                     'errmsg': '修改地址标题失败'})
        return JsonResponse({'code': 0,
                                     'errmsg': 'ok'})


class ChangePasswordView(LoginRequiredMixin,View):
    def put(self,request):
        json_dict = json.loads(request.body.decode())
        old_password = json_dict.get('old_password')
        new_password = json_dict.get('new_password')
        new_password2 = json_dict.get('new_password2')

        if not all([old_password,new_password,new_password2]):
            return JsonResponse({'code': 400,
                                     'errmsg': '缺少必传参数'})

        result = request.user.check_password(old_password)
        if not result:
            return JsonResponse({'code': 400,
                                     'errmsg': '密码错误'})

        if not re.match('^[a-zA-Z0-9-_?+]{8,20}$',new_password):
            return JsonResponse({'code': 400,
                                     'errmsg': '密码格式错误'})
        if new_password!=new_password2:
            return JsonResponse({'code': 400,
                                     'errmsg': '两次密码不相同'})
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                     'errmsg': '修改密码失败'})
        logout(request)
        response = JsonResponse({'code': 0,
                                     'errmsg': 'ok'})
        response.delete_cookie('username')

        return response


