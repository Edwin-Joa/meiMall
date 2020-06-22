from django.http import JsonResponse



def my_decorator(func):
    def wrapper(request,*args,**kwargs):
        if request.user.is_authenticated:
            print('自定义扩展类验证成功')
            return func(request,*args,**kwargs)
        else:
            print('扩展类验证失败')
            return JsonResponse({'code':400,'errmsg':'请登录后重试'})
    return wrapper


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls,**initkwargs):
        view = super().as_view(**initkwargs)
        print('自定义的扩展类被调用')
        return my_decorator(view)





