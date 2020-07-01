from django_redis import get_redis_connection
from django.http import JsonResponse
import pickle,base64

def merge_cart_cookie_to_redis(request,user,response):
    cookie_cart = request.COOKIES.get('carts')

    if not cookie_cart:
        return response
    cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

    new_dict = {}
    new_add = []
    new_remove = []

    for sku_id,item in cart_dict.items():
        new_dict[sku_id] = item['count']

        if item['selected']:
            new_add.append(sku_id)
        else:
            new_remove.append(sku_id)

    conn = get_redis_connection('carts')
    pl = conn.pipeline()

    pl.hmset(f'carts_{user.id}',new_dict)

    if new_add:
        pl.sadd(f'selected_{user.id}',*new_add)
    if new_remove:
        pl.srem(f'selected_{user.id}',*new_remove)
    pl.execute()

    response.delete_cookie('carts')

    return response