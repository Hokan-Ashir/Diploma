from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.databaseUtils.databaseConnector import databaseConnector
from pyhtmlanalyzer.databaseUtils.databaseWrapperFunctions import databaseWrapperFunctions

__author__ = 'hokan'

class analyzerDatabaseFunctions:
    @staticmethod
    def updateObjects(analyzeData, pageRowId):
        connector = databaseConnector()
        register = modulesRegister()

        # construct dictionary of previous rows for each module ...
        # ... that page references to ...
        dictOfPreviousRowIds = {}
        ORMClass = register.getORMClass(configNames.page)
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
                if targetTableName != configNames.page:
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
    @staticmethod
    def insertObjects(analyzeData, pageRowId):
        dictOfInsertedIds = {}
        for moduleName, moduleValue in analyzeData.items():
            dictOfInsertedIds[moduleName] = databaseWrapperFunctions.recursivelyInsertData(moduleName,
                                                                                           moduleValue)

        dictOfInsertedIds[configNames.page] = [pageRowId]
        databaseWrapperFunctions.attachForeignKeys(dictOfInsertedIds)

    @staticmethod
    def insertDataInDatabase(analyzedObjectName, analyzedObjectValue, isValid):
        connector = databaseConnector()
        register = modulesRegister()

        # update or insert data
        pageRow = connector.select(register.getORMClass(configNames.page), [configNames.id], 'url',
                                       analyzedObjectName)
        if pageRow:
            # page row already exists
            # if isValid is None - page do not changed at all, nothing to update
            if isValid is not None:
                connector.update(register.getORMClass(configNames.page), pageRow[0].id, 'isValid', isValid)
                analyzerDatabaseFunctions.updateObjects(analyzedObjectValue, pageRow[0].id)
        else:
            # page row doesn't exists - create new one and all data within
            Page = register.getORMClass(configNames.page)
            newPage = Page(analyzedObjectName, isValid)
            pageRowId = connector.insertObject(newPage)
            analyzerDatabaseFunctions.insertObjects(analyzedObjectValue, pageRowId)