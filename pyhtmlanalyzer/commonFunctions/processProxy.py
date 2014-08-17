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
        result = None
        if self.classInstance is None:
            result = self.methodName(*self.arguments)
        else:
            try:
                result = getattr(self.classInstance, self.methodName)(**self.arguments)
            except TypeError, error:
                # TODO write to log "No such function exists"
                pass

        return result