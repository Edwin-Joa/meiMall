from django.shortcuts import render
from django.views import View
from .models import GoodsCategory,SKU
from django.http import JsonResponse
from django.core.paginator import Paginator,EmptyPage
from .utils import get_breadcrumb
from haystack.views import SearchView
# Create your views here.



class ListView(View):
    def get(self,request,category_id):

        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')


        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'获取mysql数据出错'})
        # breadcrumb = {
        #     'cat1':'1',
        #     'cat2':'2',
        #     'cat3':'3'
        # }
        breadcrumb = get_breadcrumb(category)


        try:
            skus = SKU.objects.filter(category=category,
                                      is_launched=True).order_by(ordering)
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'获取mysql数据库出错'})

        paginator = Paginator(skus,page_size)

        try:
            page_skus = paginator.page(page)

        except EmptyPage:
            return  JsonResponse({'code':400,'errmsg':'page数据出错'})

        total_page = paginator.num_pages

        list = []

        for sku in page_skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'name':sku.name,
                'price':sku.price
            })

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'breadcrumb':breadcrumb,
            'list':list,
            'count':total_page
        })


class HotGoodsView(View):
    def get(self,request,category_id):
        try:
            skus = SKU.objects.filter(category_id=category_id,is_launched=True).order_by('-sales')[:2]
        except Exception as e:
            return JsonResponse({'code':400,'errmsg':'获取商品出错'})

        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'name':sku.name,
                'price':sku.price
            })

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'hot_skus':hot_skus
        })


class MySearchView(SearchView):
    '''重写searchview类'''
    def create_response(self):
        page = self.request.GET.get('page')

        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id':sku.object.id,
                'name':sku.object.name,
                'price':sku.object.price,
                'default_image_url':sku.object.default_image_url,
                'searchkey':context.get('query'),
                'page_size':context['page'].paginator.num_pages,
                # 'page_size':context['paginator'].per_page,
                'count':context['page'].paginator.count,
                # 'count':context['paginator'].count
            })

        return JsonResponse(data_list,safe=False)

