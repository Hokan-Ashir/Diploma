__author__ = 'hokan'

class MethodProxy(object):
    def __init__(self, obj, method):
        self.obj = obj
        if isinstance(method, basestring):
            self.methodName = method
        else:
            assert callable(method)
            self.methodName = method.func_name

    def __call__(self, *args, **kwargs):
        return getattr(self.obj, self.methodName)(*args, **kwargs)

class MethodProxyWithMethodName(MethodProxy):
    def __call__(self, *args, **kwargs):
        return [self.methodName, getattr(self.obj, self.methodName)(*args, **kwargs)]