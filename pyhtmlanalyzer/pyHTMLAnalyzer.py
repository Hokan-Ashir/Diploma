from collections import defaultdict
import logging
from multiprocessing import Queue
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.commonFunctions.processProxy import processProxy
from pyhtmlanalyzer.databaseUtils.databaseConnector import databaseConnector
from pyhtmlanalyzer.full.html.htmlAnalyzer import htmlAnalyzer
from pyhtmlanalyzer.full.script.scriptAnalyzer import scriptAnalyzer
from pyhtmlanalyzer.full.url.urlAnalyzer import urlAnalyzer

__author__ = 'hokan'

class pyHTMLAnalyzer:
    __modulesRegister = None
    __activeModulesDictionary = defaultdict(bool)

    # predefined section name of analyzed functions
    __databaseSectionName = 'Analyze functions database'

    def __init__(self, configFileName):
        self.__modulesRegister = modulesRegister()
        configList = self.getConfigList(configFileName)
        self.createDatabaseFromFile(configFileName)
        self.setModule(htmlAnalyzer(configList[0]))
        self.setModule(scriptAnalyzer(configList[1]))
        self.setModule(urlAnalyzer(configList[2]))

    def createDatabaseFromFile(self, configFileName):
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
        #connector.createDatabase(user, password, hostname, databaseName)
        connector.createDatabaseTables(user, password, hostName, databaseName, recreateDatabase=True,
                                       createTablesSeparately=False)


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
    def getNumberOfAnalyzedAbstractObjectFeaturesByFunction(self, xmldata, pageReady, uri, functionName):
        if xmldata is None or pageReady is None:
            print("Insufficient number of parameters")
            return
        resultDict = {}
        processQueue = Queue()
        proxyProcessesList = []

        # start process for each module
        for moduleName, module in self.getModules().items():
            if self.getIsActiveModule(moduleName):
                # {'numberOfProcesses' : 1}
                process = processProxy(None, [module, {'xmldata' : xmldata, 'pageReady' : pageReady, 'uri' : uri},
                                              processQueue, functionName], commonFunctions.callFunctionByNameQeued)
                proxyProcessesList.append(process)
                process.start()

        # wait for process joining
        for process in proxyProcessesList:
            process.join()

        # gather all data
        for i in xrange(0, len(proxyProcessesList)):
            resultList = processQueue.get()[1]
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
            print("Cannot analyze file")
            return

        xmldata = openedFile[0]
        pageReady = openedFile[1]
        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(xmldata, pageReady, objectName, functionName)

    def getNumberOfAnalyzedPageFeaturesByFunction(self, objectName, functionName = 'getAllAnalyzeReport'):
        openedPage = commonConnectionUtils.openPage(objectName)
        if openedPage == []:
            print("Cannot analyze page")
            return

        xmldata = openedPage[0]
        pageReady = openedPage[1]
        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(xmldata, pageReady, objectName, functionName)
    #
    ###################################################################################################################

    def getTotalNumberOfAnalyzedObjectsFeatures(self, listOfObjects, isPages = True):
        if len(listOfObjects) == 0:
            print("No objects passed to analyze")
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
        for process in proxyProcessesList:
            process.join()

        # gather all data
        for i in xrange(0, len(proxyProcessesList)):
            resultDict[listOfObjects[i]] = processQueue.get()

        return resultDict

    def getTotalNumberOfAnalyzedPagesFeatures(self, listOfPages):
        return self.getTotalNumberOfAnalyzedObjectsFeatures(listOfPages)

    def getTotalNumberOfAnalyzedFilesFeatures(self, listOfFiles):
        return self.getTotalNumberOfAnalyzedObjectsFeatures(listOfFiles, False)

    # TODO replace with neuro-net
    def analyzeObjectStub(self, analyzeData):
        return True

    def updateObjects(self, analyzeData, pageRowId):
        connector = databaseConnector()
        register = modulesRegister()
        tableRelationsDictionary = connector.getTablesRelationDictionary()
        for moduleName, moduleValue in analyzeData.items():
            if not moduleValue:
                continue

            # search for foreign keys in relations connected to "page" table
            for relation in tableRelationsDictionary['page']:
                parsedRelation = relation.replace(' ', '').split(':')
                if moduleName == parsedRelation[1]:
                    # found "slave"-table, get its foreign key
                    # TODO improve on relations
                    connector.select(register.getORMClass(moduleName), [configNames.id], parsedRelation[0], )

            # TODO get fk on existing tables via tableRelationsDictionary and pageRowId
            connector.update(register.getORMClass(moduleName), )
            print()

    def __attachForeignKeys(self, dictOfForeignKeys):
        # no FKs, nothing to attach
        if not dictOfForeignKeys:
            return

        connector = databaseConnector()
        register = modulesRegister()
        for tableName, keyIdList in dictOfForeignKeys.items():
            ORMClass = register.getORMClass(tableName)
            tableFks = list(ORMClass.__table__.foreign_keys)
            for FK in tableFks:
                # get table name TO WHICH references current FK
                fkTableName = FK.target_fullname.split('.')[0]
                try:
                    if dictOfForeignKeys[fkTableName]:
                        # get column name which contain FK to other table
                        masterTableColumnName = FK.parent.description
                        for item in dictOfForeignKeys[fkTableName]:
                            for keyId in keyIdList:
                                connector.update(ORMClass, keyId, masterTableColumnName, item)
                except KeyError, error:
                    # simply can't find such table name in dict of foreign keys, nothing special
                    continue

    def __recursivelyInsertData(self, tableName, dataList):
        connector = databaseConnector()
        register = modulesRegister()
        listOfInsertedIds = []
        for item in dataList:
            dictOfFKs = {}
            for name, value in item.items():
                tableFks = list(register.getORMClass(tableName).__table__.foreign_keys)
                for FK in tableFks:
                    # get table name TO WHICH references current FK
                    fkTableName = FK.target_fullname.split('.')[0]
                    if fkTableName == name:
                        dictOfFKs[name] = self.__recursivelyInsertData(name, value)

            Class = register.getORMClass(tableName)

            # delete FK references from new row data
            for key in dictOfFKs.keys():
                del item[key]

            # remove 'get' from beginning of future column name and decapitalize first character
            # as we done it before in databaseConnector, when create database
            for columnName in item.keys():
                tempString = columnName.lstrip('get')
                item[tempString[0].lower() + tempString[1:]] = item.pop(columnName)

            newRow = Class(**item)
            newRowId = connector.insertObject(newRow)
            dictOfFKs[tableName] = [newRowId]

            self.__attachForeignKeys(dictOfFKs)
            listOfInsertedIds.append(newRowId)

        return listOfInsertedIds


    def insertObjects(self, analyzeData, pageRowId):
        dictOfInsertedIds = {}
        for moduleName, moduleValue in analyzeData.items():
            dictOfInsertedIds[moduleName] = self.__recursivelyInsertData(moduleName, moduleValue)

        dictOfInsertedIds['page'] = [pageRowId]
        self.__attachForeignKeys(dictOfInsertedIds)



    def analyzeObjects(self, listOfObjects, isPages = True):
        connector = databaseConnector()
        register = modulesRegister()

        # get analyze data itself
        resultDict = self.getTotalNumberOfAnalyzedObjectsFeatures(listOfObjects, isPages)
        for analyzedObjectName, analyzedObjectValue in resultDict.items():

            # get isValid-solution
            isValid = self.analyzeObjectStub(analyzedObjectValue)

            # update or insert data
            pageRow = connector.select(register.getORMClass('page'), [configNames.id], 'url', analyzedObjectName)
            if pageRow:
                # page row already exists
                connector.update(register.getORMClass('page'), pageRow[0].id, 'isValid', isValid)
                self.updateObjects(analyzedObjectValue, pageRow[0].id)
            else:
                # page row doesn't exists - create new one and all data within
                Page = register.getORMClass('page')
                newPage = Page(analyzedObjectName, isValid)
                pageRowId = connector.insertObject(newPage)
                self.insertObjects(analyzedObjectValue[1], pageRowId)


    def analyzePages(self, listOfPages):
        self.analyzeObjects(listOfPages)

    def analyzeFiles(self, listOfFiles):
        self.analyzeObjects(listOfFiles, False)
    #
    ###################################################################################################################