from collections import defaultdict
import logging
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.multiprocessing.methodProxy import MethodProxy
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.commonFunctions.multiprocessing.nodaemonWrappers import NoDaemonPool
from pyhtmlanalyzer.databaseUtils.databaseConnector import databaseConnector
from pyhtmlanalyzer.databaseUtils.databaseWrapperFunctions import databaseWrapperFunctions
from pyhtmlanalyzer.full.html.htmlExtractor import htmlExtractor
from pyhtmlanalyzer.full.script.scriptExtractor import scriptExtractor
from pyhtmlanalyzer.full.url.urlExtractor import urlExtractor
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

        self.setModule(htmlExtractor(configList[0]))
        self.setModule(scriptExtractor(configList[1]))
        self.setModule(urlExtractor(configList[2]))

        # networks part
        validPagesFileName = 'testDataSet/validPages/validPages'
        invalidPagesFileName = 'testDataSet/invalidPages/invalidPages'
        self.__controller = neuroNetsController()
        try:
            self.__controller.attemptToLoadNetworksFromFiles(validPagesFileName, invalidPagesFileName)
        except IOError:
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
            for item in result['htmlExtractor']:
                htmlConfigDict[item[0]] = item[1:]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            pass

        # script features
        scriptConfigDict = {}
        try:
            for item in result['scriptExtractor']:
                scriptConfigDict[item[0]] = item[1:]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            pass

        # uri features
        urlConfigDict = {}
        try:
            for item in result['urlExtractor']:
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
        def collectResults(result):
            if result:
                # if function returns nothing (like print function, for example)
                #if resultList is None or not resultList:
                #    resultDict = resultList
                #else:
                resultDict[result[1]] = result[0]

        processPool = NoDaemonPool(processes=self.__numberOfObjectsSimultaneouslyAnalysing)

        # start process for each module
        for moduleName, module in self.getModules().items():
            if self.getIsActiveModule(moduleName):
                # 'numberOfProcesses' : 1
                methodProxy = MethodProxy(module, functionName)
                processPool.apply_async(methodProxy, (), {'object': openedObject, 'uri': uri, 'numberOfProcesses' :
                    3},
                                        callback=collectResults)

        processPool.close()
        processPool.join()

        return [uri, resultDict]

    # to run specific function in specific module, just
    def getNumberOfAnalyzedHTMLFileFeaturesByFunction(self, objectName, functionName = 'getAllAnalyzeReport'):
        openedFile = commonConnectionUtils.openFile(objectName)
        if openedFile == []:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("Cannot analyze file: impossible to open file (%s)" % objectName)
            return [objectName, None]

        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(openedFile, objectName, functionName)

    def getNumberOfAnalyzedPageFeaturesByFunction(self, objectName, functionName = 'getAllAnalyzeReport'):
        openedPage = commonConnectionUtils.openPage(objectName)
        if openedPage == []:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("Cannot analyze page: impossible to open page (%s)" % objectName)
            return [objectName, None]

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

        resultDict = {}

        processPool = NoDaemonPool(processes=self.__numberOfObjectsSimultaneouslyAnalysing)
        methodProxy = MethodProxy(self, functionName)

        # start processes
        result = processPool.map(methodProxy, listOfObjects)

        processPool.close()
        processPool.join()

        for item in result:
            if item[1]:
                resultDict[item[0]] = item[1]
            else:
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning("Object '%s' cannot be analyzed - errors during data extraction. Continuing ..."
                                % item[0])

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
        # get analyze data itself
        resultDict = self.getTotalNumberOfAnalyzedObjectsFeatures(listOfObjects,isPages)
        for analyzedObjectName, analyzedObjectValue in resultDict.items():
            # flatten all dicts and lists (which is not FKs to some tables)
            # remove all FKs columns (dict keys) from analyzedObjectValue
            for moduleName, moduleValueList in analyzedObjectValue.items():
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

            self.__insertDataInDatabase(analyzedObjectName, analyzedObjectValue, allObjectsAreValid)

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

        # get analyze data itself
        resultDict = self.getTotalNumberOfAnalyzedObjectsFeatures(listOfObjects, isPages)
        for analyzedObjectName, analyzedObjectValue in resultDict.items():
            # get isValid-solution
            isValid = self.__controller.analyzeObjectViaNetworks(analyzedObjectValue)
            self.__insertDataInDatabase(analyzedObjectName, analyzedObjectValue, isValid)

    def analyzePages(self, listOfPages):
        self.__analyzeObjects(listOfPages)

    def analyzeFiles(self, listOfFiles):
        self.__analyzeObjects(listOfFiles, False)
    #
    ###################################################################################################################