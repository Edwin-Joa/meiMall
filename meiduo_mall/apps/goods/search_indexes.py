
from haystack import indexes
from .models import SKU

# 此处定义的是一个haystack 模型类，对应ES搜索中的索引表
# 注意事项：
# 1. 模型类的名字： <django模型类>Index
# 2. 继承：indexes.SearchIndex,indexes.Indexable
# 3. 定义的类属性text（固定的名字）——在es中检索的字段
class SKUIndex(indexes.SearchIndex,indexes.Indexable):
    # document=True:定义当前text是用于检索的es检索表中的字段
    text = indexes.CharField(document=True,use_template=True)

    def get_model(self):
        return SKU

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_launched=True)

