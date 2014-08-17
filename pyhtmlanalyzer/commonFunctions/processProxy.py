import logging
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
    __classInstance = None
    __arguments = None
    __methodName = None

    def __init__(self, classInstance, arguments, methodName):
        super(processProxy, self).__init__()
        self.__classInstance = classInstance
        self.__arguments = arguments
        self.__methodName = methodName

    def run(self):
        result = None
        if self.__classInstance is None:
            result = self.__methodName(*self.__arguments)
        else:
            try:
                result = getattr(self.__classInstance, self.__methodName)(**self.__arguments)
            except Exception, error:
                logger = logging.getLogger(self.__class__.__name__)
                logger.exception(error)
                pass

        return result