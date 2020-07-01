
from django.conf import settings
from django.template import loader

import os,sys
# sys.path.insert(0,'../../')

from apps.goods.utils import get_categories,get_goods_and_spec
from meiduo_mall.celery_tasks.main import celery_app



@celery_app.task(name='generate_static_sku_detail_html')
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
        settings.GENERATED_STATIC_HTML_FILES_DIR,
        'goods/' + str(sku_id) + '.html'
    )
    with open(file_path,'w',encoding='utf-8') as f:
        f.write(sku_html_text)
