from datetime import datetime, date
import json
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.databaseUtils.databaseConnector import databaseConnector

__author__ = 'hokan'

class databaseWrapperFunctions:
    @staticmethod
    def attachForeignKeys(dictOfForeignKeys):
        # no FKs, nothing to attach
        if not dictOfForeignKeys:
            return

        register = modulesRegister()
        connector = databaseConnector()
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

    @staticmethod
    def recursivelyInsertData(tableName, dataList):
        register = modulesRegister()
        connector = databaseConnector()
        listOfInsertedIds = []
        for item in dataList:
            dictOfFKs = {}
            for name, value in item.items():
                tableFks = list(register.getORMClass(tableName).__table__.foreign_keys)
                for FK in tableFks:
                    # get table name TO WHICH references current FK
                    fkTableName = FK.target_fullname.split('.')[0]
                    if fkTableName == name:
                        dictOfFKs[name] = databaseWrapperFunctions.recursivelyInsertData(name, value)

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

            databaseWrapperFunctions.attachForeignKeys(dictOfFKs)
            listOfInsertedIds.append(newRowId)

        return listOfInsertedIds

    @staticmethod
    def invalidateFKColumns(tableName, tableIdList, listOfChildTableNames):
        register = modulesRegister()
        connector = databaseConnector()
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

    @staticmethod
    def recursivelyDeleteObjects(tableIdList, ORMClass, listOfChildTableNames, tableData):
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

                databaseWrapperFunctions.recursivelyDeleteObjects(
                    [getattr(innerItem, columnFKName) for innerItem in result],
                    childORMClass, childTableNames,
                    tableData[tableIdList.index(item)][targetTableName]
                )

            connector.deleteObject(ORMClass, configNames.id, item)

    # tableData is list of future rows
    @staticmethod
    def recursivelyUpdateObjects(tableName, tableData, tableIdList):
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
                    databaseWrapperFunctions.recursivelyUpdateObjects(targetTableName,
                                                    tableData[0][targetTableName],
                                                    [getattr(item, columnFKName) for item in result])
                    listOfFKTableNames.append(targetTableName)

            # remove all FK data before update parent object
            for item in listOfFKTableNames:
                del tableData[0][item]

            # remove 'get' from beginning of future column name and decapitalize first character
            # as we done it before in databaseConnector, when create database
            for columnName, columnValue in tableData[0].items():
                tempString = columnName.lstrip('get')
                # get from http://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript
                dthandler = lambda obj: (obj.isoformat()
                                         if isinstance(obj, datetime)
                                            or isinstance(obj, date)
                                         else None)
                # serialize via JSON all dict and list values (assumed, that in DB corresponding rows has String type)
                if type(tableData[0][columnName]) is list \
                    or type(tableData[0][columnName]) is dict:
                        tableData[0][columnName] = json.dumps(tableData[0][columnName], default=dthandler)
                tableData[0][tempString[0].lower() + tempString[1:]] = tableData[0].pop(columnName)

            # update parent object
            connector.updateByDict(ORMClass, tableIdList[0], tableData[0])

        # need to update more than one row, so we have no idea which row must be updated with which data
        # so we delete all rows recursively and recreate them
        else:
            # check if any rows in tableData has only @id key, this means that this data not changed and must not be
            # updated by any NEW information, so we basically delete all rows like:
            # row['id'] in tableIdList
            itemsToDelete = []
            for item in tableData:
                if len(item) == 1 \
                    and configNames.id in item \
                    and item[configNames.id] in tableIdList:
                    tableIdList.remove(item[configNames.id])
                    itemsToDelete.append(item)

            # remove items that is not need to delete
            for item in itemsToDelete:
                tableData.remove(item)

            # table data doesn't changed at all - nothing to update
            if not tableIdList:
                return

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
            dictOfParentTableIds = databaseWrapperFunctions.invalidateFKColumns(tableName, tableIdList,
                                                                                listOfChildTableNames)

            # recursively delete other rows
            databaseWrapperFunctions.recursivelyDeleteObjects(tableIdList, ORMClass, listOfChildTableNames, tableData)

            # recursively insert other rows
            dictOfInsertedIds = {}
            dictOfInsertedIds[tableName] = databaseWrapperFunctions.recursivelyInsertData(tableName, tableData)

            # attach foreign keys
            databaseWrapperFunctions.attachForeignKeys(dict(dictOfInsertedIds.items() + dictOfParentTableIds.items()))