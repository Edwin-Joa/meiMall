from collections import OrderedDict
from django.conf import settings
from django.template import loader
import os
import time
from apps.goods.models import GoodsChannel, GoodsCategory
from apps.contents.models import ContentCategory, Content


def generate_index_html():
    '''
    生成首页静态页面：
    1. 获取动态数据——模板参数
    2. 模板渲染——模板参数填充到html页面中
    :return:
    '''


    # ===============目录动态数据部分======================
    # 新建categories的有序字典
    categories = OrderedDict()

    channels = GoodsChannel.objects.order_by(
        'group_id',
        'sequence'
    )

    for channel in channels:
        # 如果是第一次遍历到该分组，则为该分组添加一个新的key（该key即为group_id）
        if channel.group_id not in categories:
            categories[channel.group_id] = {
                'channels':[],
                'sub_cats':[]
            }

            # 构建当前分组的频道和分类信息
        cat1 = channel.category
        categories[channel.group_id]['channels'].append({
            'id':cat1.id,
            'name':cat1.name,
            'url':channel.url
        })

        # 所有父级分类是cat1这个1级分类的2级分类
        cat2s = GoodsCategory.objects.filter(
            parent = cat1  #
        )

        for cat2 in cat2s:
            cat3_list = [] # 根据cat2这个2级分类获取3级分类

            cat3s = GoodsCategory.objects.filter(
                parent=cat2
            )

            for cat3 in cat3s:
                cat3_list.append({
                    'id':cat3.id,
                    'name':cat3.name
                })

            categories[channel.group_id]['sub_cats'].append({
                'id': cat2.id,
                'name': cat2.name,
                'sub_cats': cat3_list  # 填充三级分类
            })

    # ==================广告部分=======================
    contents = {}
    content_cats = ContentCategory.objects.all()
    for content_cat in content_cats:
        contents[content_cat.key] = Content.objects.filter(
            category=content_cat,
            status=True
        ).order_by('sequence')


    # ==================模板参数部分====================
    context = {
        'categories':categories,
        'contents':contents
    }

    # 模板页面渲染，获取模板，把数据添加进去并生成页面==========
    # loader.get_template()函数，传入模板文件，构建一个模板对象
    template = loader.get_template('index.html')

    # context：模板参数，动态输数据，用于填充页面
    # 返回值就是一个html页面文本数据
    index_html = template.render(context=context)

    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR,'index.html')

    with open(file_path,'w',encoding='utf-8') as f:
        f.write(index_html)

