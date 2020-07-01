from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
import json,pickle,base64
from django_redis import get_redis_connection
from apps.goods.models import SKU


# Create your views here.

class CartsView(View):
    def post(self,request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected',True)

        if not all([sku_id,count]):
            return JsonResponse({
                'code':400,'errmsg':'缺少必传参数'
            })

        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({
                'code':400,'errmsg':'商品不存在'
            })

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({
                'code':400,'errmsg':'count有误'
            })

        if selected:
            if not isinstance(selected,bool):
                return JsonResponse({
                    'code':400,'errmsg':'selected有误'
                })

        if request.user.is_authenticated:
            conn = get_redis_connection('carts')
            pl = conn.pipeline()
            pl.hincrby(f'carts_{request.user.id}',sku_id,count)

            if selected:
                pl.sadd(f'selected_{request.user.id}',sku_id)

            pl.execute()

            return JsonResponse({'code':0,'errmsg':'添加购物车成功'})

        else:
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                count += cart_dict[sku_id]['count']

            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = JsonResponse({'code':0,'errmsg':'ok'})

            response.set_cookie('carts',cart_data)

            return response


    def get(self,request):
        user = request.user

        if user.is_authenticated:
            conn = get_redis_connection('carts')
            item_dict = conn.hgetall(f'carts_{user.id}')
            cart_selected = conn.smembers(f'selected_{user.id}')
            cart_dict = {}

            for sku_id,count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count':int(count),
                    'selected': sku_id in cart_selected
                }

        else:
            cookie_cart = request.COOKIE.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b16decode(cookie_cart.encode()))
            else:
                cart_dict = {}

        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id':sku.id,
                'name':sku.name,
                'count':cart_dict.get(sku.id).get('count'),
                'selected':cart_dict.get(sku.id).get('selected'),
                'default_image_url':sku.default_image_url,
                'price':sku.price,
                'amount':sku.price * cart_dict.get(sku.id).get('count'),
            })

        return JsonResponse({'code':0,'errmsg':'ok','cart_skus':cart_skus})


    def put(self,request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected',True)

        if not all([sku_id,count]):
            return JsonResponse({'code':400,'errmsg':'缺少必传参数'})

        try:
            sku = SKU.objects.filter(id=sku_id)
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'sku_id不存在'})

        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':400,'errmsg':'count有误'})

        if selected:
            if not isinstance(selected,bool):
                return JsonResponse({'code':400,'errmsg':'selected有误'})


        user = request.user

        if user.is_authenticated:
            conn = get_redis_connection('carts')
            pl = conn.pipeline()

            pl.hset(f'carts_{user.id}',sku_id,count)

            if selected:
                pl.sadd(f'selected_{user.id}',sku_id)
            else:
                pl.srem(f'selected_{user.id}',sku_id)
            pl.execute()

            try:
                sku = SKU.objects.get(id=sku_id)
            except Exception as e:
                return JsonResponse({'code':400,'errmsg':'sku_id不存在'})


            cart_sku = {
                'id':sku_id,
                'count':count,
                'selected':selected,
                'name':sku.name,
                'default_image_url':sku.default_image_url,
                'price':sku.price,
                'amount':count * sku.price
            }

            return  JsonResponse({'code':0,'errmsg':'修改购物车成功','cart_sku':cart_sku})

        else:
            cookie_cart = request.COOKIE.get('carts')

            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }

            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            cart_sku = {
                'id':sku_id,
                'count':count,
                'selected':selected
            }
            response = JsonResponse({
                'code':0,'errmsg':'修改购物车数据成功',
                'cart_sku':cart_sku
            })

            response.set_cookie('carts',cart_data)

            return response

    def delete(self,request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'sku_id不存在'})

        user = request.user

        if user.is_authenticated:

            conn = get_redis_connection('carts')
            pl = conn.pipeline()

            pl.hdel(f'carts_{user.id}',sku_id)
            pl.srem(f'selected_{user.id}',sku_id)
            pl.execute()

            return JsonResponse({'code':0,'errmsg':'删除商品成功'})

        else:

            cookie_cart = request.COOKIE.get('carts')

            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encodde()))
            else:
                cart_dict = {}

            response = JsonResponse({'code':0,'errmsg':'删除商品成功'})

            if sku_id in cart_dict:
                del cart_dict[sku_id]

                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

                response.set_cookie('carts',cart_data)

            return response


class CartSelectAllView(View):
    def put(self,request):

        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected',True)

        if selected:
            if not isinstance(selected,bool):
                return JsonResponse({'code':400,'errmsg':'参数selected有误'})

        user = request.user

        if user.is_authenticated:
            conn = get_redis_connection('carts')
            item_dict = conn.hgetall(f'carts_{user.id}')
            sku_ids = item_dict.keys()

            if selected:
                conn.sadd(f'selected_{user.id}',*sku_ids)
            else:
                conn.srem(f'selected_{user.id}',*sku_ids)

            return JsonResponse({'code':0,'errmsg':'全选购物车成功'})

        else:
            cookie_cart = request.COOKIE.get('carts')
            response = JsonResponse({'code':0,'errmsg':'全选购物车成功'})

            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encodde()))

                for sku_id in cart_dict.keys():
                    cart_dict[sku_id]['selected'] = selected

                cart_data = pickle.dumps(base64.b64encode(cart_dict)).decode()

                response.set_cookie('carts',cart_data)
            return response


class CartsSimpleView(View):
    def get(self,request):

        user = request.user

        if user.is_authenticated:
            conn = get_redis_connection('carts')
            item_dict = conn.hgetall(f'carts_{user.id}')
            cart_selected = conn.smembers(f'selected_{user.id}')

            cart_dict = {}

            for sku_id,count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count':int(count),
                    'selected':sku_id in cart_selected
                }

        else:

            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}


        cart_skus = []
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_skus.append({
                'id':sku.id,
                'name':sku.name,
                'count':cart_dict.get(sku.id).get('count'),
                'default_image_url':sku.default_image_url
            })

        return JsonResponse({'code':0,'errmsg':'ok','cart_skus':cart_skus})