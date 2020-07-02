from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from django.utils import timezone
from django.db import transaction
from apps.users.models import Address
from apps.goods.models import SKU
import json

from .models import OrderInfo,OrderGoods

from decimal import Decimal
# Create your views here.





class OrderSettlementView(View):

    def get(self,request):
        user = request.user

        try:
            addresses = Address.objects.filter(user=request.user,is_deleted=False)
        except Exception as e:
            addresses = None

        conn = get_redis_connection('carts')
        item_dict = conn.hgetall(f'carts_{user.id}')
        cart_selected = conn.smembers(f'selected_{user.id}')
        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(item_dict[sku_id])

        sku_list = []

        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image_url,
                'count': cart[sku.id],
                'price':sku.price
            })

        freight = Decimal('10.00')

        list = []
        for address in addresses:
            list.append({
                'id':address.id,
                'province':address.province.name,
                'city':address.city.name,
                'district':address.district.name,
                'place':address.place,
                'receiver':address.receiver,
                'mobile':address.mobile
            })

            context = {
                'addresses':list,
                'skus':sku_list,
                'freight':freight,
            }

            return JsonResponse({'code':0,'errmsg':'ok','context':context})


class OrderCommitView(View):

    def post(self,request):
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        if not all([address_id,pay_method]):
            return  JsonResponse({'code':400,'errmsg':'缺少必传参数'})
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'参数address_id有误'})

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code':400,'errmsg':'参数pay_method'})

        user = request.user

        order_id = timezone.localtime().strftime('%Y%m%H%M%S') + ('{:0>9d}'.format(user.id))


        with transaction.atomic():
            save_id = transaction.savepoint()


            order = OrderInfo.objects.create(
                order_id = order_id,
                user = user,
                address = address,
                total_count = 0,
                total_amount = Decimal('10.00'),
                freight = Decimal('0'),
                pay_method=pay_method,
                status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
            if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']
            else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
            )

            conn = get_redis_connection('carts')
            item_dict = conn.hgetall(f'carts_{user.id}')
            cart_selected = conn.smembers(f'selected_{user.id}')
            carts = {}
            for sku_id in cart_selected:
                carts[int(sku_id)] = int(item_dict[sku_id])

            sku_ids = carts.keys()


            for sku_id in sku_ids:
                sku = SKU.objects.get(id=sku_id)
                sku_count = carts[sku.id]
                if sku_count>sku.stock:
                    return JsonResponse({'code':400,'errmsg':'库存不足'})

                sku.stock -= sku_count
                sku.sales += sku_count
                sku.save()

                OrderGoods.objects.create(
                    order = order,
                    sku=sku,
                    count = sku_count,
                    price=sku.price,
                )

                order.total_count += sku_count
                order.total_amount += (sku_count* sku.price)

            order.total_amount += order.freight
            order.save()

            transaction.savepoint_commit(save_id)


        pl = conn.pipeline()
        pl.hdel(f'carts_{user.id}',*cart_selected)
        pl.srem(f'selected_{user.id}',*cart_selected)
        pl.execute()

        return JsonResponse({'code':0,'errmsg':'ok','order_id':order.order_id})





