from sqlalchemy import Integer, Float, String, Boolean, Column, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions

__author__ = 'hokan'

class databaseConnector():
    # Base class object, will be base class for any ORM class created
    Base = None
    # database engine object
    engine = None
    # ORM classes dictionary
    classDict = {}

    def __init__(self, user = None, password = None, hostname = None, databaseName = None):
        if user is not None \
            and password is not None \
            and hostname is not None \
            and databaseName is not None:
            self.engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        self.Base = declarative_base()

    # columnNames and columnTypes must have same length
    def createTable(self, tableName, columnNames, columnTypes):
        columnValues = []

        # then create values for column names according to its types
        for item in columnTypes:
            if item == 'Integer':
                typeObject = Integer
            elif item == 'Float':
                typeObject = Float
            elif item == 'String':
                typeObject = String(255)
            elif item == 'Boolean':
                typeObject = Boolean
            else:
                # TODO log
                continue

            columnValues.append(Column(typeObject))

        # prepare ORM-class methods
        methodsDict = {}

        # create __init__ method
        # prepare code
        initCode = ('''
def __init__ (self, %s):
    %s
        ''' % (
            ', '.join(columnNames),
            # DO NOT forget to include 4 whitespaces, we still writing python!
            '\n    '.join(['self.' + str(item) + ' = ' + str(item) for item in columnNames])
        ))

        # compile it
        exec initCode in methodsDict

        # create __repr__ method
        reprCode = ('''
def __repr__ (self):
    return '<%s(%s)> %% (%s)'
        ''' % (
            tableName,
            ('%s, ' * len(columnNames))[:-2],
            ', '.join(['self.' + str(item) for item in columnNames])
        ))

        # compile it
        exec reprCode in methodsDict

        methodsList = [methodsDict['__init__'], methodsDict['__repr__']]
        methodNamesList = ['__init__', '__repr__']

        # at last append id member to class ...
        columnNames.append('id')
        columnValues.append(Column(Integer, primary_key=True))

        # ... and __tablename__ member to class
        columnNames.append('__tablename__')
        columnValues.append(tableName)

        SomeClass = commonFunctions.makeClass(tableName, [self.Base], columnNames, columnValues, methodsList,
                                        methodNamesList)
        self.classDict[tableName] = SomeClass
        # creates table it self
        self.Base.metadata.create_all(self.engine)

        # fill with some data
        #Session = scoped_session(sessionmaker(bind=self.engine))
        #session = Session()
        #instance = SomeClass(100, 4.0)
        #instance2 = SomeClass(100, 4.0)
        #session.add_all([instance, instance2])
        #session.commit()

    def executeQuery(self, query):
        if self.engine is None:
            print('engine is none')
            # TODO log
            return False

        Session = scoped_session(sessionmaker(bind=self.engine, autocommit=True))
        session = Session()
        try:
            session.begin()
            session.execute(query)
            session.commit()
            return True
        except OperationalError, error:
            # dispatch transaction
            session.rollback()
            # TODO log
            print(error)
            return False

    def dropDatabase(self, user, password, hostname, databaseName):
        if self.engine is None:
            self.engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeQuery('drop database %s' % databaseName)


    def createDatabase(self, user, password, hostname, databaseName):
        if self.engine is None:
            self.engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeQuery('create database %s' % databaseName)

    def useDatabase(self, user, password, hostname, databaseName):
        if self.engine is None:
            self.engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeQuery('use %s' % databaseName)

    def getDatabaseEngine(self, user, password, hostname, databaseName, createIfNotExists = False):
        connectionString = 'mysql://' + user + ':' + password + '@' + hostname
        engine = create_engine(connectionString, encoding='latin1', echo=True)

        if createIfNotExists:
            self.createDatabase(user, password, hostname, databaseName)
            self.useDatabase(user, password, hostname, databaseName)

        return engine

    # this method creates tables from config file and, if "recreateDatabase" set to True, recreates database
    # this method will return False in any case of problems, also if database doesn't exists
    def createDatabaseTables(self, user, password, hostname, databaseName, recreateDatabase = False):
        self.engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        if recreateDatabase:
            self.dropDatabase(user, password, hostname, databaseName)
            self.createDatabase(user, password, hostname, databaseName)
            self.useDatabase(user, password, hostname, databaseName)
        elif self.useDatabase(user, password, hostname, databaseName) == False:
            # TODO log, database does not exists
            return False

        # html module
        htmlTableColumns = commonFunctions.getAnalyzeFunctionList('analyzeFunctions', 'html.module', True)

        # strip 'get' from the beginning of each method and decapitalize first letter
        columnNames = []
        for item in htmlTableColumns:
            tempString = item[0].lstrip('get')
            columnNames.append(tempString[0].lower() + tempString[1:])

        columnTypes = [item[1] for item in htmlTableColumns]

        # we insufficient number of column names of column types
        if len(columnNames) != len(columnTypes):
            # TODO throw exception & log
            return False


        # check if lists (both, cause we already know that they have same length) are not empty
        if columnNames:
            self.createTable('htmlAnalyzer', columnNames, columnTypes)

        ############################################################################################################
        # script module
        scriptColumns = commonFunctions.getAnalyzeFunctionList('analyzeFunctions', 'script.module', True)

         # strip 'get' from the beginning of each method and decapitalize first letter
        columnNames = []
        for item in scriptColumns:
            tempString = item[0].lstrip('get')
            columnNames.append(tempString[0].lower() + tempString[1:])

        columnTypes = [item[1] for item in scriptColumns]

        # we insufficient number of column names of column types
        if len(columnNames) != len(columnTypes):
            # TODO throw exception & log
            return False


        # check if lists (both, cause we already know that they have same length) are not empty
        if columnNames:
            self.createTable('scriptAnalyzer', columnNames, columnTypes)

        ############################################################################################################
        # url module
        urlColumns = commonFunctions.getAnalyzeFunctionList('analyzeFunctions', 'url.module', True)

         # strip 'get' from the beginning of each method and decapitalize first letter
        columnNames = []
        for item in urlColumns:
            tempString = item[0].lstrip('get')
            columnNames.append(tempString[0].lower() + tempString[1:])

        columnTypes = [item[1] for item in urlColumns]

        # we insufficient number of column names of column types
        if len(columnNames) != len(columnTypes):
            # TODO throw exception & log
            return False

        # check if lists (both, cause we already know that they have same length) are not empty
        if columnNames:
            self.createTable('urlAnalyzer', columnNames, columnTypes)

        return True