import logging
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.neuronetUtils.neuroNet import neuroNet
from pyhtmlanalyzer.neuronetUtils.weightsController import weightsController

__author__ = 'hokan'

class neuroNetsController:
    __networksDict = {}
    __weightsController = None
    __solutionBorderValue = 0.5

    # predefined networks directory
    __networksDirectory = './networks'

    def __init__(self):
        self.__initialize()

    def __initialize(self):
        register = modulesRegister()

        # set weights for register modules
        self.__weightsController = weightsController()

        # load networks from files, if it's possible
        # first create networks stubs
        for moduleName in register.getClassInstanceDictionary().keys():
            self.__networksDict[moduleName] = neuroNet()

    def attemptToLoadNetworksFromFiles(self, invalidPagesFileName, validPagesFileName):
        logger = logging.getLogger(self.__class__.__name__)
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

        # indicate that networks not loaded
        raise IOError

    def trainNetworks(self, invalidDataDict, validDataDict, numberOfInnerNeurons = None, outputDirectory =
    __networksDirectory):
        logger = logging.getLogger(self.__class__.__name__)

        logger.info("Creating and training networks ...")
        # create train networks
        for moduleName, moduleValueList in validDataDict.items():
            self.__networksDict[moduleName] = neuroNet(len(moduleValueList[0]), 1, numberOfInnerNeurons)

            # create common (valid and invalid) input values list of lists
            inputDataList = moduleValueList + invalidDataDict[moduleName]
            outputDataList = ([[True]] * len(moduleValueList)) + ([[False]] * len(invalidDataDict[moduleName]))
            logger.info("Network name: " + moduleName)
            logger.info(self.__trainNetworkWithData(moduleName, inputDataList, outputDataList, 200))
            logger.info("Saving '%s' network to directory '%s'" % (moduleName, outputDirectory))
            self.__networksDict[moduleName].saveNetworkToDirectory(moduleName, outputDirectory)
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
            moduleResultValue = 0
            if len(dictOfInputParameters[networkName]) != 0:
                for item in dictOfInputParameters[networkName]:
                    if self.__networksDict[networkName].getNumberOfInputParameters() == len(item):
                        pageChanged = True
                        moduleResultValue = moduleResultValue \
                                            + abs(self.__networksDict[networkName].analyzeData(item)) \
                                            * self.__weightsController.getModuleWeight(networkName)
                        logger.info('Analyze data value: %s' % str(self.__networksDict[networkName].analyzeData(item)))
                        logger.info("Network \'%s\' module weight: %s" % (networkName,
                                                                   str(self.__weightsController.getModuleWeight(networkName))))

                moduleResultValue = moduleResultValue / len(dictOfInputParameters[networkName])
            solution = solution + moduleResultValue * self.__weightsController.getModuleValueWeight(networkName)
            logger.info("Network \'%s\' module value weight: %s" % (networkName,
                                                                    self.__weightsController.getModuleValueWeight(
                                                                        networkName)))

        logger.info('Non round solution value: %s' % str(solution))
        # round solution
        solution = True if abs(solution) >= self.__solutionBorderValue else False
        logger.info("Result solution is: " + str(solution))
        logger.info("Page changed: " + str(pageChanged))

        return None if not pageChanged else solution

    def getSolutionBorderValue(self):
        return self.__solutionBorderValue

    def setSolutionBorderValue(self, value):
        self.__solutionBorderValue = value

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