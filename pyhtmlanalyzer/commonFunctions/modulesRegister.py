__author__ = 'hokan'

class modulesRegister(object):
    __instance = None

    __classInstanceDictionary = {}
    __ormClassDictionary = {}

    # declared as singleton
    # TODO check multi-threading
    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super(modulesRegister, cls).__new__(cls)

        return cls.__instance

    # class instance section
    def getClassInstanceDictionary(self):
        return self.__classInstanceDictionary

    def registerClassInstance(self, classInstance, classInstanceName = None):
        if classInstanceName is not None:
            self.__classInstanceDictionary[classInstanceName] = classInstance
        else:
            self.__classInstanceDictionary[classInstance.__name__] = classInstance

    def unregisterClassInstance(self, classInstanceName):
        del self.__classInstanceDictionary[classInstanceName]

    def getClassInstance(self, classInstanceName):
        return self.__classInstanceDictionary[classInstanceName]



    # ORM class section
    def getORMClassDictionary(self):
        return self.__ormClassDictionary

    def registerORMClass(self, ormClass, ormClassName = None):
        if ormClassName is not None:
            self.__ormClassDictionary[ormClassName] = ormClass
        else:
            self.__ormClassDictionary[ormClass.__name__] = ormClass

    def unregisterORMClass(self, ormClassName):
        del self.__ormClassDictionary[ormClassName]

    def getORMClass(self, ormClassName):
        return self.__ormClassDictionary[ormClassName]