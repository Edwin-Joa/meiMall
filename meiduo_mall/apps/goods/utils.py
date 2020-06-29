from django.template import loader
from django.conf import settings
from .models import GoodsChannel,GoodsCategory,SKU,SKUImage,SKUSpecification,GoodsSpecification,SpecificationOption
from collections import OrderedDict
import os
from copy import deepcopy

def get_breadcrumb(category):

    dict = {
        'cat1':'',
        'cat2':'',
        'cat3':'',
    }

    if category.parent is None:
        dict['cat1'] = category.name


    elif category.parent.parent is None:
        dict['cat2'] = category.name
        dict['cat1'] = category.parent.name

    elif category.parent.parent.parent is None:
        dict['cat3'] = category.name
        dict['cat2'] = category.parent.name
        dict['cat1'] = category.parent.parent.name

    return dict


def get_categories():

    categories = OrderedDict()

    channels = GoodsChannel.objects.order_by(
        'group_id',
        'sequence'
    )

    for channel in channels:
        # 如果是第一次遍历到该分组，则为该分组添加一个新的key（该key即为group_id）
        if channel.group_id not in categories:
            categories[channel.group_id] = {
                'channels': [],
                'sub_cats': []
            }

            # 构建当前分组的频道和分类信息
        cat1 = channel.category
        categories[channel.group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })

        # 所有父级分类是cat1这个1级分类的2级分类
        cat2s = GoodsCategory.objects.filter(
            parent=cat1  #
        )

        for cat2 in cat2s:
            cat3_list = []  # 根据cat2这个2级分类获取3级分类

            cat3s = GoodsCategory.objects.filter(
                parent=cat2
            )

            for cat3 in cat3s:
                cat3_list.append({
                    'id': cat3.id,
                    'name': cat3.name
                })

            categories[channel.group_id]['sub_cats'].append({
                'id': cat2.id,
                'name': cat2.name,
                'sub_cats': cat3_list  # 填充三级分类
            })
    return categories

def get_goods_and_spec(sku_id):

    sku = SKU.objects.get(pk=sku_id)
    # 记录当前sku的选项组合
    cur_sku_spec_options = SKUSpecification.objects.filter(sku=sku).order_by('spec_id')
    cur_sku_options = []
    for temp in cur_sku_spec_options:
        cur_sku_options.append(temp.option_id)
    goods = sku.goods
    # 罗列出和当前sku同类的所有商品的选项和商品id的映射关系
    sku_options_mapping = {}
    skus = SKU.objects.filter(goods=goods)
    for temp_sku in skus:
        sku_spec_options = SKUSpecification.objects.filter(sku=temp_sku).order_by('spec_id')
        sku_options = []
        for temp in sku_spec_options:
            sku_options.append(temp.option_id)
        sku_options_mapping[tuple(sku_options)] = temp_sku.id






    sku.images = SKUImage.objects.filter(sku=sku)

    goods = sku.goods

    specs = GoodsSpecification.objects.filter(goods=goods).order_by('id')



    for index,spec in enumerate(specs):
        options = SpecificationOption.objects.filter(spec=spec)

        temp_list = deepcopy(cur_sku_options)

        for option in options:
            temp_list[index] = option.id


            option.sku_id = sku_options_mapping.get(tuple(temp_list))

        specs.spec_options = options

    return goods,sku,specs


def generate_static_sku_detail_html(sku_id):

    # =================categories参数的获取，即频道信息的获取，同generate_index内的

    categories = get_categories()

    goods,sku,specs = get_goods_and_spec(sku_id)

    # ====================构建模板参数=========================
    context = {
        'categories':categories,
        'goods':goods,
        'specs':specs,
        'sku':sku
    }
    # 获取模板
    template = loader.get_template('detail.html')

    # 调用模板渲染函数，得出完整的html页面
    sku_html_text = template.render(context=context)


    # 写入静态文件
    file_path = os.path.join(
        settings.GENERATED_STATIC_HTML_DIR,
        'goods/' + str(sku_id) + '.html'
    )
    with open(file_path,'w',encoding='utf-8') as f:
        f.write(sku_html_text)

