import logging
from sqlalchemy import Integer, Float, String, Boolean, Column, create_engine, ForeignKey
from sqlalchemy.exc import OperationalError, NoReferencedTableError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister

__author__ = 'hokan'

class databaseConnector(object):
    __instance = None

    # Base class object, will be base class for any ORM class created
    __Base = None
    # database engine object
    __engine = None
    # used as storage to ORM classes dictionary
    __modulesRegister = None

    # predefined section names from config file
    # designed to create additional not-analysing tables, additional columns, and relations between tables
    __extraTables = 'Extra tables'
    __extraColumns = 'Extra columns'
    __tableRelations = 'Table relations'

    # declared as singleton
    # TODO check multi-threading
    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super(databaseConnector, cls).__new__(cls)

        return cls.__instance

    def __init__(self, user = None, password = None, hostname = None, databaseName = None):
        self.__modulesRegister = modulesRegister()

        if user is not None \
            and password is not None \
            and hostname is not None \
            and databaseName is not None:
            self.__engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        self.__Base = declarative_base()

    # columnNames and columnTypes must have same length
    def createTable(self, tableName, columns, tablesRelations, createTablesSeparately):
        # currently support only one FK per column
        # TODO improve that

        # parse relations list for current table
        # column_which_will_be_used_as_FK : tableName_to_which_FK_points : field_of_table_to_which_FK_points
        relations = []
        relationColumns = []
        if tableName in tablesRelations:
            for item in tablesRelations[tableName]:
                relations.append(item.replace(' ', '').split(':'))

        for columnName, columnType in columns.items():
            if columnType == 'Integer':
                typeObject = Integer
            elif columnType == 'Float':
                typeObject = Float
            elif columnType == 'String':
                typeObject = String(255)
            elif columnType == 'Boolean':
                typeObject = Boolean
            else:
                logger = logging.getLogger()
                logger.warning('Unrecognized database type: ' + str(columnType))
                continue

            # if table hasn't any foreign this stub still will work
            foreignKey = None

            # table has foreign keys - create it
            if relations:
                for relation in relations:
                    if columnName == relation[0]:
                        # make foreign key instance with "use_alter=True" in case of ignoring possible errors
                        # with circular dependencies, for example
                        foreignKey = ForeignKey('%s.%s' % (relation[1], relation[2]),
                                                use_alter=True,
                                                name='fk_%s_%s_%s' % (tableName, relation[1], relation[2]))

                        # create relation-object
                        relationColumns.append(['relation_%s' % relation[1],
                                                relationship('%s' % relation[1][0].upper() + relation[1][1:])])
                        break

            columns[columnName] = Column(typeObject, foreignKey)

        # prepare ORM-class methods
        methodsDict = {}

        # create __init__ method
        # prepare code

        # construct __init__ method input parameters without foreign keys
        methodsColumns = []
        for columnName, column in columns.items():
            addColumn = True
            if relations:
                for relation in relations:
                    if columnName == relation[0]:
                        addColumn = False
                        break

            if addColumn:
                methodsColumns.append(columnName)

        initCode = ('''
def __init__ (self, %s):
    %s
        ''' % (
            ', '.join(methodsColumns),
            # DO NOT forget to include 4 whitespaces, we still writing python!
            '\n    '.join(['self.' + str(item) + ' = ' + str(item) for item in methodsColumns])
        ))

        # compile it
        exec initCode in methodsDict

        # create __repr__ method
        reprCode = ('''
def __repr__ (self):
    return '<%s(%s)> %% (%s)'
        ''' % (
            tableName,
            ('%s, ' * len(methodsColumns))[:-2],
            ', '.join(['self.' + str(item) for item in methodsColumns])
        ))

        # compile it
        exec reprCode in methodsDict

        methodsList = [methodsDict['__init__'], methodsDict['__repr__']]
        methodNamesList = ['__init__', '__repr__']

        # at last append id member to class ...
        columns['id'] = Column(Integer, primary_key=True)

        # ... and __tablename__ member to class
        columns['__tablename__'] = tableName

        # ... and also relation-objects
        for item in relationColumns:
            columns[item[0]] = item[1]

        className = tableName[0].upper() + tableName[1:]
        SomeClass = commonFunctions.makeClassByDictionary(className, [self.__Base], columns,
                                                          methodsList, methodNamesList)
        self.__modulesRegister.registerORMClass(SomeClass, className)

        if createTablesSeparately:
            # creates table it self
            self.__Base.metadata.create_all(self.__engine)

        # fill with some data
        #Session = scoped_session(sessionmaker(bind=self.engine))
        #session = Session()
        #instance = SomeClass(100, 4.0)
        #instance2 = SomeClass(100, 4.0)
        #session.add_all([instance, instance2])
        #session.commit()

    def executeRawQuery(self, query):
        if self.__engine is None:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('No engine exists. Query can not be executed\nQuery:\n\t%s' % query)
            print('No engine exists. Query can not be executed\nQuery:\n\t%s' % query)
            return False

        Session = scoped_session(sessionmaker(bind=self.__engine, autocommit=True))
        session = Session()
        try:
            session.begin()
            session.execute(query)
            session.commit()
            return True
        except OperationalError, error:
            # dispatch transaction
            session.rollback()
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            print(error)
            return False

    def dropDatabase(self, user, password, hostname, databaseName):
        if self.__engine is None:
            self.__engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeRawQuery('drop database %s' % databaseName)


    def createDatabase(self, user, password, hostname, databaseName):
        if self.__engine is None:
            self.__engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeRawQuery('create database %s' % databaseName)

    def useDatabase(self, user, password, hostname, databaseName):
        if self.__engine is None:
            self.__engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeRawQuery('use %s' % databaseName)

    def getDatabaseEngine(self, user, password, hostname, databaseName, createIfNotExists = False):
        connectionString = 'mysql://' + user + ':' + password + '@' + hostname
        engine = create_engine(connectionString, encoding='latin1', echo=True)

        if createIfNotExists:
            self.createDatabase(user, password, hostname, databaseName)
            self.useDatabase(user, password, hostname, databaseName)

        return engine

    # this method creates tables from config file and, if "recreateDatabase" set to True, recreates database
    # this method will return False in any case of problems, also if database doesn't exists
    def createDatabaseTables(self, user, password, hostname, databaseName, recreateDatabase = False,
                             createTablesSeparately = True):
        self.__engine = self.getDatabaseEngine(user, password, hostname, databaseName)

        if recreateDatabase:
            self.dropDatabase(user, password, hostname, databaseName)
            self.createDatabase(user, password, hostname, databaseName)
            self.useDatabase(user, password, hostname, databaseName)
        elif self.useDatabase(user, password, hostname, databaseName) == False:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Database %s does not exists' % databaseName)
            return False

        # load analysing tables
        tables = commonFunctions.getSectionContent('config', r'[^\n\s=,]+\s*:\s*[^\n\s=,]+', 'Extractors functions')

        # load extra tables
        extraTables = commonFunctions.getSectionContent('config', r'[^\n\s=,]+\s*:\s*[^\n\s=,]+',
                                                        self.__extraTables)

        # load extra columns
        extraColumns = commonFunctions.getSectionContent('config', r'[^\n\s=,]+\s*:\s*[^\n\s=,]+', self.__extraColumns)

        # load tables relations
        tablesRelations = commonFunctions.getSectionContent('config', r'[^\n\s=,]+\s*:\s*[^\n\s=,]+\s*:\s*[^\n\s=,]+',
                                                            self.__tableRelations)

        # append to analysing tables extra tables
        tables = dict(tables.items() + extraTables.items())

        # append extra columns to all tables
        for key, value in tables.items():
            if key in extraColumns:
                tables[key] = tables[key] + extraColumns[key]

        for key, value in tables.items():
            tableColumns = [item.replace(' ', '').split(':') for item in value]

            # strip 'get' from the beginning of each method and decapitalize first letter
            columnNames = []
            for item in tableColumns:
                tempString = item[0].lstrip('get')
                columnNames.append(tempString[0].lower() + tempString[1:])

            columnTypes = [item[1] for item in tableColumns]

            # we insufficient number of column names of column types
            if len(columnNames) != len(columnTypes):
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning('Unequal number of column names (%s) and column types (%s)' % (str(columnNames),
                                                                                            str(columnTypes)))
                continue

            # check if lists (both, cause we already know that they have same length) are not empty
            if not columnNames or not columnTypes:
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning('Some list is empty: column names (%s); column types (%s)' % (str(not columnNames),
                                                                                             str(not columnTypes)))
                continue

            # combine column names and types in one object, for simplicity
            columns = dict(zip(columnNames, columnTypes))

            try:
                self.createTable(key, columns, tablesRelations, createTablesSeparately)
            except NoReferencedTableError, error:
                # this error will raise if we try to create tables separately,
                # but tables themselves has relations
                # in this case we must run "metadata.create_all(engine)" method after all tables created
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning(error)

        # run metadata commit only if we create tables all at once
        # this technique needed in case we would like to add foreign keys on tables later
        # or, if tables has circular foreign key
        # thus SQLAlchemy doesn't support ALTER-statements over tables, columns, etc.
        # it has "use_alter=True" parameter for "ForeignKey" or "ForeignKeyConstraint" classes
        # i.e:
        # user_id = Column(Integer, ForeignKey('users.id', use_alter=True, name='fk_address_user_id'), nullable=False)
        # NOTE: "name" parameter required
        #
        # so, if we would like to create tables with circular foreign keys, we must first create tables with
        # "ForeignKey"/"ForeignConstraintKey" instance (with use_alter=True), then call "metadata.create_all(engine)"
        # method to create all tables and all foreign keys
        #
        # for more details see
        # http://www.blog.pythonlibrary.org/2010/02/03/another-step-by-step-sqlalchemy-tutorial-part-2-of-2/
        # or
        # http://docs.sqlalchemy.org/en/rel_0_9/core/constraints.html#creating-dropping-foreign-key-constraints-via-alter
        # and http://docs.sqlalchemy.org/en/rel_0_9/orm/relationships.html#one-to-many
        #
        # Also if you would like to get ALTER-statements in SQLAlchemy, you can use SQLAlchemy Migrate tools
        if not createTablesSeparately:
            metadata = self.__Base.metadata
            metadata.create_all(self.__engine)

        return True