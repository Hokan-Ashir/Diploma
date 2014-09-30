from collections import defaultdict
import logging
from multiprocessing import Queue
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.commonFunctions.processProxy import processProxy
from pyhtmlanalyzer.databaseUtils.databaseConnector import databaseConnector
from pyhtmlanalyzer.databaseUtils.databaseWrapperFunctions import databaseWrapperFunctions
from pyhtmlanalyzer.full.html.htmlAnalyzer import htmlAnalyzer
from pyhtmlanalyzer.full.script.scriptAnalyzer import scriptAnalyzer
from pyhtmlanalyzer.full.url.urlAnalyzer import urlAnalyzer
from pyhtmlanalyzer.neuronetUtils.neuroNetsController import neuroNetsController

__author__ = 'hokan'

class pyHTMLAnalyzer:
    __modulesRegister = None
    # neuroNets controller
    __controller = None
    __activeModulesDictionary = defaultdict(bool)

    # predefined section name of analyzed functions
    __databaseSectionName = 'Analyze functions database'

    # predefined number of objects simultaneously analysing
    __numberOfObjectsSimultaneouslyAnalysing = 5

    def __init__(self, configFileName):
        self.__initialize(configFileName)

    def __initialize(self, configFileName):
        self.__modulesRegister = modulesRegister()
        logger = logging.getLogger(self.__class__.__name__)
        configList = self.getConfigList(configFileName)
        self.createDatabaseFromFile(configFileName)

        self.setModule(htmlAnalyzer(configList[0]))
        self.setModule(scriptAnalyzer(configList[1]))
        self.setModule(urlAnalyzer(configList[2]))

        # networks part
        validPagesFileName = 'validPages'
        invalidPagesFileName = 'invalidPages'
        self.__controller = neuroNetsController(invalidPagesFileName, validPagesFileName)
        logger.info("Getting invalid data from pages to train networks...")
        invalidDataDict = self.getNetworkTrainDataFromFile(invalidPagesFileName, False)
        logger.info("Getting valid data from pages to train networks...")
        validDataDict = self.getNetworkTrainDataFromFile(validPagesFileName, True)
        self.__controller.trainNetworks(invalidDataDict, validDataDict)

    def createDatabaseFromFile(self, configFileName, deleteTablesContent = True):
        databaseInfo = commonFunctions.getSectionContent(configFileName, r'[^\n\s=,]+',
                                                         self.__databaseSectionName)
        user = None
        password = None
        hostName = None
        databaseName = None
        try:
            info = databaseInfo[configNames.databaseInfoModuleName]
            for item in info:
                if item[0] == configNames.user:
                    user = item[1]
                elif item[0] == configNames.password:
                    password = item[1]
                elif item[0] == configNames.host:
                    hostName = item[1]
                elif item[0] == configNames.database:
                    databaseName = item[1]

        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)

        connector = databaseConnector()
        connector.createORMClasses(user, password, hostName, databaseName, recreateDatabase=True,
                                       cleanTablesContent=deleteTablesContent)

    # numberOfObjectsSimultaneouslyAnalysing
    def getNumberOfObjectsSimultaneouslyAnalysing(self):
        return self.__numberOfObjectsSimultaneouslyAnalysing

    def setNumberOfObjectsSimultaneouslyAnalysing(self, value):
        self.__numberOfObjectsSimultaneouslyAnalysing = value

    # module section
    def getModules(self):
        return self.__modulesRegister.getClassInstanceDictionary()

    def getModuleByName(self, moduleName):
        return self.__modulesRegister.getClassInstance(moduleName)

    def setModule(self, moduleInstance, moduleInstanceName = None):
        self.__modulesRegister.registerClassInstance(moduleInstance, moduleInstanceName)
        if moduleInstanceName is not None:
            self.setIsActiveModule(moduleInstanceName)
        else:
            self.setIsActiveModule(moduleInstance.__name__)

    def removeModule(self, moduleName):
        self.__modulesRegister.unregisterClassInstance(moduleName)
        del self.__activeModulesDictionary[moduleName]

    # isActive section
    def setIsActiveModule(self, moduleName, isActive = True):
        self.__activeModulesDictionary[moduleName] = isActive

    def getIsActiveModule(self, moduleName):
        return self.__activeModulesDictionary[moduleName]

    # get config list for various analyzer modules
    def getConfigList(self, configFileName):
        result = commonFunctions.getSectionContent(configFileName, r'[^\n\s=,]+',
                                                    'Extractors features')

        # html features
        htmlConfigDict = {}
        try:
            for item in result['htmlAnalyzer']:
                htmlConfigDict[item[0]] = item[1:]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            pass

        # script features
        scriptConfigDict = {}
        try:
            for item in result['scriptAnalyzer']:
                scriptConfigDict[item[0]] = item[1:]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            pass

        # uri features
        urlConfigDict = {}
        try:
            for item in result['urlAnalyzer']:
                urlConfigDict[item[0]] = item[1:]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            pass

        return [htmlConfigDict, scriptConfigDict, urlConfigDict]

    # to run specific function in specific module, simply activate module via "set @module_name Active" functions
    # and pass function name to some of this function wrappers - "getNumberOfAnalyzedHTMLFileFeaturesByFunction"
    # or "getNumberOfAnalyzedPageFeaturesByFunction"
    #
    # NOTE: all functions run it separate processes
    def getNumberOfAnalyzedAbstractObjectFeaturesByFunction(self, openedObject, uri, functionName):
        if openedObject.getXMLData() is None or openedObject.getPageReady() is None:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("Insufficient number of parameters:\n - xmlData (%s)\n - pageReady (%s)"
                         % (openedObject.getXMLData(),
                            openedObject.getPageReady()))
            return

        resultDict = {}
        processQueue = Queue()
        proxyProcessesList = []

        # start process for each module
        for moduleName, module in self.getModules().items():
            if self.getIsActiveModule(moduleName):
                # {'numberOfProcesses' : 1}
                process = processProxy(None, [module, {'object': openedObject,
                                                       'uri': uri},
                                              processQueue, functionName], commonFunctions.callFunctionByNameQeued)
                proxyProcessesList.append(process)
                process.start()

        # wait for process joining
        #for process in proxyProcessesList:
        #    process.join()

        # gather all data
        for i in xrange(0, len(proxyProcessesList)):
            queueResult = processQueue.get()
            resultList = queueResult[1]
            # if function returns nothing (like print function, for example)
            if resultList is None or not resultList:
                resultDict = resultList
            else:
                resultDict[resultList[1]] = resultList[0]

        return resultDict

    # to run specific function in specific module, just
    def getNumberOfAnalyzedHTMLFileFeaturesByFunction(self, objectName, functionName = 'getAllAnalyzeReport'):
        openedFile = commonConnectionUtils.openFile(objectName)
        if openedFile == []:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("Cannot analyze file: impossible to open file (%s)" % objectName)
            return

        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(openedFile, objectName, functionName)

    def getNumberOfAnalyzedPageFeaturesByFunction(self, objectName, functionName = 'getAllAnalyzeReport'):
        openedPage = commonConnectionUtils.openPage(objectName)
        if openedPage == []:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("Cannot analyze page: impossible to open page (%s)" % objectName)
            return

        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(openedPage, objectName, functionName)
    #
    ###################################################################################################################

    def getTotalNumberOfAnalyzedObjectsFeatures(self, listOfObjects, isPages = True):
        if len(listOfObjects) == 0:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning("No objects passed to analyze. Aborting analysis")
            return None

        functionName = 'getNumberOfAnalyzedPageFeaturesByFunction' \
            if isPages else 'getNumberOfAnalyzedHTMLFileFeaturesByFunction'
        processQueue = Queue()
        proxyProcessesList = []
        resultDict = {}
        # start process for each page
        for object in listOfObjects:
            proxy = processProxy(None, [self, {'objectName' : object}, processQueue, functionName],
                                 commonFunctions.callFunctionByNameQeued)
            proxyProcessesList.append(proxy)
            proxy.start()

        # wait for process joining
        #for process in proxyProcessesList:
        #    process.join()

        # gather all data
        for i in xrange(0, len(proxyProcessesList)):
            resultDict[listOfObjects[i]] = processQueue.get()

        return resultDict

    def getTotalNumberOfAnalyzedPagesFeatures(self, listOfPages):
        return self.getTotalNumberOfAnalyzedObjectsFeatures(listOfPages)

    def getTotalNumberOfAnalyzedFilesFeatures(self, listOfFiles):
        return self.getTotalNumberOfAnalyzedObjectsFeatures(listOfFiles, False)

    def updateObjects(self, analyzeData, pageRowId):
        connector = databaseConnector()

        # construct dictionary of previous rows for each module ...
        # ... that page references to ...
        dictOfPreviousRowIds = {}
        ORMClass = self.__modulesRegister.getORMClass('page')
        tableFks = list(ORMClass.__table__.foreign_keys)
        for FK in tableFks:
            # get table name TO WHICH references current FK
            targetTableName = FK.target_fullname.split('.')[0]
            columnFKName = FK.parent.description
            result = connector.select(ORMClass, [columnFKName], configNames.id, pageRowId)
            if targetTableName not in dictOfPreviousRowIds:
                dictOfPreviousRowIds[targetTableName] = []

            for item in result:
                dictOfPreviousRowIds[targetTableName].append(getattr(item, columnFKName))

        # ... and that references to page
        for ormClassName, ORMClass in self.__modulesRegister.getORMClassDictionary().items():
            tableFks = list(ORMClass.__table__.foreign_keys)
            for FK in tableFks:
                # get table name TO WHICH references current FK
                targetTableName = FK.target_fullname.split('.')[0]
                # this FK doesn't references to page
                if targetTableName != 'page':
                    continue
                else:
                    columnFKName = FK.parent.description
                    result = connector.select(ORMClass, [configNames.id], columnFKName, pageRowId)
                    if targetTableName not in dictOfPreviousRowIds:
                        dictOfPreviousRowIds[ormClassName] = []

                    for item in result:
                        dictOfPreviousRowIds[ormClassName].append(getattr(item, configNames.id))

        dictOfInsertedIds = {}
        for moduleName, moduleValue in analyzeData.items():
            dictOfInsertedIds[moduleName] = databaseWrapperFunctions.recursivelyUpdateObjects(moduleName,
                                                                                              moduleValue,
                                                                                              dictOfPreviousRowIds[moduleName])

    def insertObjects(self, analyzeData, pageRowId):
        dictOfInsertedIds = {}
        for moduleName, moduleValue in analyzeData.items():
            dictOfInsertedIds[moduleName] = databaseWrapperFunctions.recursivelyInsertData(moduleName,
                                                                                           moduleValue)

        dictOfInsertedIds['page'] = [pageRowId]
        databaseWrapperFunctions.attachForeignKeys(dictOfInsertedIds)

    def __insertDataInDatabase(self, analyzedObjectName, analyzedObjectValue, isValid):
        connector = databaseConnector()
        # update or insert data
        pageRow = connector.select(self.__modulesRegister.getORMClass('page'), [configNames.id], 'url',
                                       analyzedObjectName)
        if pageRow:
            # page row already exists
            # if isValid is None - page do not changed at all, nothing to update
            if isValid is not None:
                connector.update(self.__modulesRegister.getORMClass('page'), pageRow[0].id, 'isValid', isValid)
                self.updateObjects(analyzedObjectValue, pageRow[0].id)
        else:
            # page row doesn't exists - create new one and all data within
            Page = self.__modulesRegister.getORMClass('page')
            newPage = Page(analyzedObjectName, isValid)
            pageRowId = connector.insertObject(newPage)
            self.insertObjects(analyzedObjectValue, pageRowId)

    def __getNetworkTrainDataFromObjects(self, listOfObjects, allObjectsAreValid = True, isPages = True):
        dictOfInputParameters = {}

        analysingBlocks = len(listOfObjects) / self.__numberOfObjectsSimultaneouslyAnalysing
        for i in xrange(0, analysingBlocks + 1):
            logger = logging.getLogger(self.__class__.__name__)
            logger.info('List of analysing objects:')
            logger.info(listOfObjects[i * self.__numberOfObjectsSimultaneouslyAnalysing :
                (i + 1) * self.__numberOfObjectsSimultaneouslyAnalysing])

            # in case len(listOfObjects) % self.__numberOfObjectsSimultaneouslyAnalysing == 0
            if listOfObjects[i * self.__numberOfObjectsSimultaneouslyAnalysing :
                (i + 1) * self.__numberOfObjectsSimultaneouslyAnalysing] == []:
                break
            # get analyze data itself
            resultDict = self.getTotalNumberOfAnalyzedObjectsFeatures(
                listOfObjects[i * self.__numberOfObjectsSimultaneouslyAnalysing :
                (i + 1) * self.__numberOfObjectsSimultaneouslyAnalysing],
                isPages
            )
            for analyzedObjectName, analyzedObjectValue in resultDict.items():
                if analyzedObjectValue[1] is None:
                    logger = logging.getLogger(self.__class__.__name__)
                    logger.warning("Object '%s' cannot be analyzed - errors during data extraction. Continuing ..."
                                   % analyzedObjectName)
                    continue

                # flatten all dicts and lists (which is not FKs to some tables)
                # remove all FKs columns (dict keys) from analyzedObjectValue
                modulesDict = analyzedObjectValue[1]
                for moduleName, moduleValueList in modulesDict.items():
                    listOfListsOfInputParameters = []
                     # delete FKs elements
                    # ... that current module references to ...
                    ORMClass = self.__modulesRegister.getORMClass(moduleName)
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
                        for ormClassName, ORMClass in self.__modulesRegister.getORMClassDictionary().items():
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

                self.__insertDataInDatabase(analyzedObjectName, analyzedObjectValue[1], allObjectsAreValid)

        return dictOfInputParameters

    def getNetworkTrainDataFromFile(self, fileName, allObjectsAreValid):
        objectList = commonFunctions.getObjectNamesFromFile(fileName)
        return self.__getNetworkTrainDataFromObjects(objectList, allObjectsAreValid)

    def getNetworkTrainDataFromPages(self, listOfPages, allObjectsAreValid):
        return self.__getNetworkTrainDataFromObjects(listOfPages, allObjectsAreValid)

    def getNetworkTrainDataFromFiles(self, listOfFiles, allObjectsAreValid):
        return self.__getNetworkTrainDataFromObjects(listOfFiles, allObjectsAreValid, False)

    def __analyzeObjects(self, listOfObjects, isPages = True):
        # TODO optimize analyze call - before doing analysis, get URLVoid data about this host,
        # and if number of detected engines less than 50% - DO NOT analyze page at all (it is valid),
        # if number of detected engines >50% - DO NOT analyze page either (it is NOT valid)
        # else - analyze page

        analysingBlocks = len(listOfObjects) / self.__numberOfObjectsSimultaneouslyAnalysing
        for i in xrange(0, analysingBlocks + 1):
            logger = logging.getLogger(self.__class__.__name__)
            logger.info('List of analysing objects:')
            logger.info(listOfObjects[i * self.__numberOfObjectsSimultaneouslyAnalysing :
                (i + 1) * self.__numberOfObjectsSimultaneouslyAnalysing])

            # in case len(listOfObjects) % self.__numberOfObjectsSimultaneouslyAnalysing == 0
            if listOfObjects[i * self.__numberOfObjectsSimultaneouslyAnalysing :
                (i + 1) * self.__numberOfObjectsSimultaneouslyAnalysing] == []:
                break

            # get analyze data itself
            resultDict = self.getTotalNumberOfAnalyzedObjectsFeatures(
                listOfObjects[i * self.__numberOfObjectsSimultaneouslyAnalysing :
                (i + 1) * self.__numberOfObjectsSimultaneouslyAnalysing],
                isPages
            )
            for analyzedObjectName, analyzedObjectValue in resultDict.items():
                if analyzedObjectValue[1] is None:
                    logger = logging.getLogger(self.__class__.__name__)
                    logger.warning("Object '%s' cannot be analyzed - errors during data extraction. Continuing ..."
                                   % analyzedObjectName)
                    continue

                # get isValid-solution
                isValid = self.__controller.analyzeObjectViaNetworks(analyzedObjectValue[1])
                self.__insertDataInDatabase(analyzedObjectName, analyzedObjectValue[1], isValid)

    def analyzePages(self, listOfPages):
        self.__analyzeObjects(listOfPages)

    def analyzeFiles(self, listOfFiles):
        self.__analyzeObjects(listOfFiles, False)
    #
    ###################################################################################################################