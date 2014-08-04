from multiprocessing import Process

__author__ = 'hokan'


# must be called as
# class Foo:
#    def bar(self, u):
#        print("Hello " + str(u))
#
# classInstance = Foo()
# u = 1
# p1 = ProcessProxy(classInstance, [u], 'bar')
class processProxy(Process):
    classInstance = None
    arguments = None
    methodName = None

    def __init__(self, classInstance, arguments, methodName):
        super(processProxy, self).__init__()
        self.classInstance = classInstance
        self.arguments = arguments
        self.methodName = methodName

    def run(self):
        if len(self.classInstance.__class__.__bases__) != 0:
            for className in self.classInstance.__class__.__bases__:
                for funcName, funcValue in className.__dict__.items():
                    if str(funcName) == self.methodName and callable(funcValue):
                        try:
                            getattr(self.classInstance, funcName)(*self.arguments)
                        except TypeError:
                            pass
                        return

        for funcName, funcValue in self.classInstance.__class__.__dict__.items():
                if str(funcName) == self.methodName and callable(funcValue):
                    try:
                        getattr(self.classInstance, funcName)(*self.arguments)
                    except TypeError:
                        pass
                    return