from collections import defaultdict
import json
import logging
from multiprocessing import Queue
from datetime import datetime, date
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

    def __invalidateFKColumns(self, tableName, tableIdList, listOfChildTableNames):
        connector = databaseConnector()
        register = modulesRegister()
        dictOfParentTableIds = {}

        # search for tables that references to tableName
        for ORMClass in register.getORMClassDictionary().values():
            tableFks = list(ORMClass.__table__.foreign_keys)
            for FK in tableFks:
                # get table name TO WHICH references current FK
                targetTableName = FK.target_fullname.split('.')[0]
                if tableName != targetTableName:
                    continue
                else:
                    columnFKName = FK.parent.description
                    # select parent table Ids, so as invalidate FK column value, which references to tableName
                    for ids in tableIdList:
                        result = connector.select(ORMClass, [configNames.id], columnFKName, ids)
                        # TODO check if result need to be checked
                        parentTableId = result[0]
                        # invalidate FK column value
                        connector.update(ORMClass, getattr(parentTableId, configNames.id), columnFKName, None)

                        if targetTableName not in dictOfParentTableIds:
                            dictOfParentTableIds[targetTableName] = []

                        dictOfParentTableIds[targetTableName].append(getattr(parentTableId, configNames.id))

        # also search for tables that tableName references to
        ORMClass = register.getORMClass(tableName)
        tableFks = list(ORMClass.__table__.foreign_keys)
        for FK in tableFks:
            # get table name TO WHICH references current FK
            targetTableName = FK.target_fullname.split('.')[0]

            # this is parent table to tableName
            if targetTableName not in listOfChildTableNames:
                columnFKName = FK.parent.description
                for ids in tableIdList:
                    result = connector.select(ORMClass, [columnFKName], configNames.id, ids)
                    # TODO check if result need to be checked
                    parentTableId = result[0]
                    # get columns name TO WHICH references current FK
                    columnTableName = FK.target_fullname.split('.')[1]
                    # invalidate FK column value
                    connector.update(ORMClass, ids, columnFKName, None)

                    if targetTableName not in dictOfParentTableIds:
                        dictOfParentTableIds[targetTableName] = []

                    dictOfParentTableIds[targetTableName].append(getattr(parentTableId, columnFKName))

        return dictOfParentTableIds


    def __recursivelyDeleteObjects(self, tableIdList, ORMClass, listOfChildTableNames, tableData):
        connector = databaseConnector()
        register = modulesRegister()
        tableFks = list(ORMClass.__table__.foreign_keys)
        for item in tableIdList:
            for FK in tableFks:
                # get table name TO WHICH references current FK
                targetTableName = FK.target_fullname.split('.')[0]
                # delete only child tables
                if targetTableName not in listOfChildTableNames:
                    continue

                columnFKName = FK.parent.description
                result = connector.select(ORMClass, [columnFKName], configNames.id, item)

                # invalidate child FK column
                connector.update(ORMClass, item, columnFKName, None)

                # TODO check if result need to be checked
                childORMClass = register.getORMClass(targetTableName)

                # get child tables of new child
                # TODO refactor, cause of too many input parameters in this function
                childTableFks = list(ORMClass.__table__.foreign_keys)
                childTableNames = []
                for innerFK in childTableFks:
                    # get table name TO WHICH references current FK
                    childTargetTableName = innerFK.target_fullname.split('.')[0]
                    for innerItem in tableData[tableIdList.index(item)][targetTableName]:
                        # if FK references to table which is not in tableData, such table is not child
                        if childTargetTableName not in innerItem:
                            continue
                        else:
                            childTableNames.append(childTargetTableName)

                self.__recursivelyDeleteObjects([getattr(innerItem, columnFKName) for innerItem in result],
                                                childORMClass, childTableNames,
                                                tableData[tableIdList.index(item)][targetTableName])

            connector.deleteObject(ORMClass, configNames.id, item)

    # tableData is list of future rows
    def __recursivelyUpdateObjects(self, tableName, tableData, tableIdList):
        connector = databaseConnector()
        register = modulesRegister()
        ORMClass = register.getORMClass(tableName)
        tableFks = list(ORMClass.__table__.foreign_keys)

        # need to update single row, so we actually able to get its id and update it
        if len(tableData) == 1:

            # tableData dict has only @id key, so this object not needed to be updated
            if configNames.id in tableData[0]:
                return

            listOfFKTableNames = []
            for FK in tableFks:
                # get table name TO WHICH references current FK
                targetTableName = FK.target_fullname.split('.')[0]
                if targetTableName not in tableData[0]:
                    # simply can't find such table name in dict of foreign keys, nothing special
                    continue
                else:
                    columnFKName = FK.parent.description
                    result = connector.select(register.getORMClass(tableName),
                                                     [columnFKName], configNames.id,
                                                     tableIdList[0])
                    # TODO check if result need to be checked
                    self.__recursivelyUpdateObjects(targetTableName,
                                                    tableData[0][targetTableName],
                                                    [getattr(item, columnFKName) for item in result])
                    listOfFKTableNames.append(targetTableName)

            # remove all FK data before update parent object
            for item in listOfFKTableNames:
                del tableData[0][item]

            # update parent object
            connector.updateByDict(ORMClass, tableIdList[0], tableData[0])

        # need to update more than one row, so we have no idea which row must be updated with which data
        # so we delete all rows recursively and recreate them
        else:
            # check if any rows in tableData has only @id key, this means that this data not changed and must not be
            # updated by any NEW information, so we basically delete all rows like:
            # row['id'] in tableIdList
            for item in tableData:
                if len(item) == 1 \
                    and configNames.id in item \
                    and item[configNames.id] in tableIdList:
                    tableIdList.remove(item[configNames.id])
                    del item

            # get list of all tables that depends on tableName
            # later, when we will be invalidating parent table Ids, we will need to know which table
            # is "child" of tableName and which is not
            listOfChildTableNames = []
            for FK in tableFks:
                # get table name TO WHICH references current FK
                targetTableName = FK.target_fullname.split('.')[0]
                for item in tableData:
                    # if FK references to table which is not in tableData, such table is not child
                    if targetTableName not in item:
                        continue
                    else:
                        listOfChildTableNames.append(targetTableName)


            # temporary invalidate all FK columns, which has values from tableIdList (make them all null)
            # this is needed by 2 reasons:
            # - if somebody will access this FK columns they will have null values and there will be no error
            # - we have to get parent tables PK, so we can attach recreated rows back to its parents
            dictOfParentTableIds = self.__invalidateFKColumns(tableName, tableIdList, listOfChildTableNames)

            # recursively delete other rows
            self.__recursivelyDeleteObjects(tableIdList, ORMClass, listOfChildTableNames, tableData)

            # recursively insert other rows
            dictOfInsertedIds = {}
            dictOfInsertedIds[tableName] = self.__recursivelyInsertData(tableName, tableData)

            # attach foreign keys
            self.__attachForeignKeys(dict(dictOfInsertedIds.items() + dictOfParentTableIds.items()))

    def updateObjects(self, analyzeData, pageRowId):
        connector = databaseConnector()
        register = modulesRegister()

        # construct dictionary of previous rows for each module ...
        # ... that page references to ...
        dictOfPreviousRowIds = {}
        ORMClass = register.getORMClass('page')
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
        for ormClassName, ORMClass in register.getORMClassDictionary().items():
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
            dictOfInsertedIds[moduleName] = self.__recursivelyUpdateObjects(moduleName, moduleValue,
                                                                            dictOfPreviousRowIds[moduleName])

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
                if fkTableName not in dictOfForeignKeys:
                    # simply can't find such table name in dict of foreign keys, nothing special
                    continue
                else:
                    # get column name which contain FK to other table
                    masterTableColumnName = FK.parent.description
                    for item in dictOfForeignKeys[fkTableName]:
                        for keyId in keyIdList:
                            connector.update(ORMClass, keyId, masterTableColumnName, item)

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
            for columnName, columnValue in item.items():
                tempString = columnName.lstrip('get')
                # get from http://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript
                dthandler = lambda obj: (obj.isoformat()
                                         if isinstance(obj, datetime)
                                            or isinstance(obj, date)
                                         else None)
                # serialize via JSON all dict and list values (assumed, that in DB corresponding rows has String type)
                if type(item[columnName]) is list \
                    or type(item[columnName]) is dict:
                        item[columnName] = json.dumps(item[columnName], default=dthandler)
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
                self.updateObjects(analyzedObjectValue[1], pageRow[0].id)
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