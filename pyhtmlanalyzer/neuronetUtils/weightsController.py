import logging
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister

__author__ = 'hokan'

class weightsController:
     # this dictionary is respond for result solution (valid/invalid), by passing each module weight in result function
    # In another words it store values that represents HOW MUCH each module (i.e. scriptModule) AND each value
    # (i.e. script piece of current page) affects on result
    # i.e:
    # isValid = isValid * (weightsDict[moduleName] * networkDict[moduleName].analyzeData(...))
    #
    # stores list of 2 values, first - weight of current module, second - weight of each value of current module
    __weightsDict = {}

    def __init__(self):
        register = modulesRegister()
        for moduleName in register.getClassInstanceDictionary().keys():
            self.__weightsDict[moduleName] = [1, 1]

    def getModuleWeight(self, moduleName):
        try:
            return self.__weightsDict[moduleName][0]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            return 0.0

    def getModuleValueWeight(self, moduleName):
        try:
            return self.__weightsDict[moduleName][1]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            return 0.0

    def setModuleWeight(self, moduleName, weight):
        try:
            self.__weightsDict[moduleName][0] = weight
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)

    def setModuleValueWeight(self, moduleName, weight):
        try:
            self.__weightsDict[moduleName][1] = weight
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)