import logging
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.neuronetUtils.neuroNet import neuroNet

__author__ = 'hokan'

class neuroNetsController:
    __networksDict = {}
    # this dictionary is respond for result solution (valid/invalid), by passing each module weight in result function
    # In another words it store values that represents HOW MUCH each module (i.e. scriptModule) AND each value
    # (i.e. script piece of current page) affects on result
    # i.e:
    # isValid = isValid * (weightsDict[moduleName] * networkDict[moduleName].analyzeData(...))
    #
    # stores list of 2 values, first - weight of current module, second - weight of each value of current module
    __networksResultSolutionWeightsDict = {}

    # predefined networks directory
    __networksDirectory = './networks'

    def __init__(self, invalidPagesFileName, validPagesFileName):
        self.__initialize(invalidPagesFileName, validPagesFileName)

    def __initialize(self, invalidPagesFileName, validPagesFileName):
        logger = logging.getLogger(self.__class__.__name__)
        register = modulesRegister()

        # set weights for register modules
        # TODO make own function or module for this stuff, cause it's one of the main controlling mechanisms
        for moduleName in register.getClassInstanceDictionary().keys():
            self.__networksResultSolutionWeightsDict[moduleName] = [1, 1]

        # load networks from files, if it's possible
        # first create networks stubs
        for moduleName in register.getClassInstanceDictionary().keys():
            self.__networksDict[moduleName] = neuroNet()

        # load networks from files
        logger.info("Loading networks from files ...")
        loadingSuccess = False
        try:
            loadingSuccess = self.loadNetworksFromDirectory(self.__networksDirectory)
        except Exception, error:
            logger.exception(error)

        if loadingSuccess:
            logger.info("Loading networks succeeded")
            return

        # something is wrong - not all files exist, or directory - create networks from
        # valid and invalid data
        logger.info("Loading networks failed")

        # gather train data
        invalidPagesList = commonFunctions.getObjectNamesFromFile(invalidPagesFileName)
        validPagesList = commonFunctions.getObjectNamesFromFile(validPagesFileName)

        # check that both lists consist of UNIQUE data, if not - abort everything
        nonUniquePages = []
        for item in validPagesList:
            if item in invalidPagesList:
                nonUniquePages.append(item)

        if nonUniquePages:
            logger.error('This pages exists in both valid and invalid pages lists')
            for item in nonUniquePages:
                logger.error(item)

            logger.error('Cannot perform analysis further. Application will be terminated')
            raise Exception('Pages duplication in valid and invalid lists')

    def trainNetworks(self, invalidDataDict, validDataDict):
        logger = logging.getLogger(self.__class__.__name__)

        logger.info("Creating and training networks ...")
        # create train networks
        for moduleName, moduleValueList in validDataDict.items():
            self.__networksDict[moduleName] = neuroNet(len(moduleValueList[0]))

            # create common (valid and invalid) input values list of lists
            inputDataList = moduleValueList + invalidDataDict[moduleName]
            outputDataList = ([[True]] * len(moduleValueList)) + ([[False]] * len(invalidDataDict[moduleName]))
            logger.info("Network name: " + moduleName)
            logger.info(self.__trainNetworkWithData(moduleName, inputDataList, outputDataList, 200))
            logger.info("Saving '%s' network to directory '%s'" % (moduleName, self.__networksDirectory))
            self.__networksDict[moduleName].saveNetworkToDirectory(moduleName, self.__networksDirectory)
            logger.info("Network '%s' saved" % moduleName)

    def analyzeObjectViaNetworks(self, analyzeDataDict):
        register = modulesRegister()
        dictOfInputParameters = {}

        # gather data for analysis
        for moduleName, moduleValueList in analyzeDataDict.items():
                listOfListsOfInputParameters = []
                 # delete FKs elements
                # ... that current module references to ...
                ORMClass = register.getORMClass(moduleName)
                tableFks = list(ORMClass.__table__.foreign_keys)
                for dictOfModuleValues in moduleValueList:
                    deletedData = {}
                    for FK in tableFks:
                        # get table name TO WHICH references current FK
                        targetTableName = FK.target_fullname.split('.')[0]
                        if targetTableName in dictOfModuleValues:
                            deletedData[targetTableName] = dictOfModuleValues[targetTableName]
                            del dictOfModuleValues[targetTableName]

                    # ... and that references to current module
                    for ormClassName, ORMClass in register.getORMClassDictionary().items():
                        tableFks = list(ORMClass.__table__.foreign_keys)
                        for FK in tableFks:
                            # get table name TO WHICH references current FK
                            targetTableName = FK.target_fullname.split('.')[0]
                            if targetTableName in dictOfModuleValues:
                                deletedData[targetTableName] = dictOfModuleValues[targetTableName]
                                del dictOfModuleValues[targetTableName]

                    listOfListsOfInputParameters.append(commonFunctions.recursiveFlattenDict(dictOfModuleValues))

                    # restore deleted data, cause this is needed for database
                    for name, value in deletedData.items():
                        dictOfModuleValues[name] = value

                if moduleName not in dictOfInputParameters:
                    dictOfInputParameters[moduleName] = listOfListsOfInputParameters
                else:
                    dictOfInputParameters[moduleName] = dictOfInputParameters[moduleName] + listOfListsOfInputParameters

        logger = logging.getLogger(self.__class__.__name__)
        # pass data to neuro-nets, get isValid solution

        # this flag represent cases, when all data from page DOESN'T changed, so "isValid" value must NOT changed
        # either; such cases can be find when NO inputValue has expected length, that mean each inputValue contains
        # row previous id
        pageChanged = False
        # TODO check abs() calls
        solution = 0
        for networkName in self.__networksDict.keys():
            logger.info("Gathering result solution from network '%s'" % networkName)
            moduleResultValue = 1
            for item in dictOfInputParameters[networkName]:
                if self.__networksDict[networkName].getNumberOfInputParameters() == len(item):
                    pageChanged = True
                    moduleResultValue = moduleResultValue \
                                        * abs(self.__networksDict[networkName].analyzeData(item)) \
                                        * self.__networksResultSolutionWeightsDict[networkName][1]

            solution = solution + moduleResultValue * self.__networksResultSolutionWeightsDict[networkName][0]

        # round solution
        # TODO also make this parameter, border value (0.5), configurable
        solution = True if abs(solution) >= 0.5 else False
        logger.info("Result solution is: " + str(solution))
        logger.info("Page changed: " + str(pageChanged))

        return None if not pageChanged else solution

    def __trainNetworkWithData(self, networkName, listOfInputParameters, listOfOutputParameters, numberOfEpochs = None):
        return self.__networksDict[networkName].trainNetworkWithData(listOfInputParameters, listOfOutputParameters, numberOfEpochs)

    def loadNetworksFromDirectory(self, directoryPath):
        try:
            for networkName in self.__networksDict.keys():
                if not self.loadNetworkFromDirectory(networkName, directoryPath):
                    return False
            return True
        except Exception, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            return False

    def loadNetworkFromDirectory(self, networkName, directoryPath):
        try:
            network = self.__networksDict[networkName]
            return network.loadNetworkFromDirectory(networkName, directoryPath)
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error(error)
            logger.error("Network '%s' doesn't exists" % networkName)
            return False
        except Exception, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            return False

    def saveNetworksToDirectory(self, directoryPath):
        try:
            for networkName in self.__networksDict.keys():
                self.saveNetworkToDirectory(networkName, directoryPath)
            return True
        except Exception, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            return False

    def saveNetworkToDirectory(self, networkName, directoryPath):
        try:
            network = self.__networksDict[networkName]
            network.saveNetworkToDirectory(networkName, directoryPath)
            return True
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error(error)
            logger.error("Network '%s' doesn't exists" % networkName)
            return False
        except Exception, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            return False