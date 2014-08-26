import logging
from sqlalchemy import Integer, Float, String, Boolean, Column, create_engine, ForeignKey
from sqlalchemy.exc import OperationalError, NoReferencedTableError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, load_only
from pyhtmlanalyzer.commonFunctions import configNames
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

    # stores relations between tables in one place, fills ONLY when database creates itself
    # with corresponding getter this allows analyzer to fill foreign keys after all modules have proceeded
    # i.e.:
    # analyzer begins analysis of page, creates row in page-table
    # then all analyzer-modules make their computations and (possibly) return foreign keys
    # after that analyzer insert all foreign keys and completes page analysis
    __tableRelationsDictionary = None

    # declared as singleton
    # TODO check multi-threading
    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super(databaseConnector, cls).__new__(cls)

        return cls.__instance

    def __init__(self, user=None, password=None, hostname=None, databaseName=None):
        self.__modulesRegister = modulesRegister()

        if user is not None \
            and password is not None \
            and hostname is not None \
            and databaseName is not None:
            self.getDatabaseEngine(user, password, hostname, databaseName)

        self.__Base = declarative_base()

    #
    def getTablesRelationDictionary(self):
        return self.__tableRelationsDictionary

    def detachObject(self, classInstance):
        Session = scoped_session(sessionmaker(self.__engine))
        session = Session()
        session.expunge(classInstance)

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
                                                relationship('%s' % relation[1])])
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
        columns[configNames.id] = Column(Integer, primary_key=True)

        # ... and __tablename__ member to class
        columns['__tablename__'] = tableName

        # ... and also relation-objects
        for item in relationColumns:
            columns[item[0]] = item[1]

        SomeClass = commonFunctions.makeClassByDictionary(tableName, [self.__Base], columns,
                                                          methodsList, methodNamesList)
        self.__modulesRegister.registerORMClass(SomeClass, tableName)

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
            return False

        Session = scoped_session(sessionmaker(self.__engine))
        session = Session()
        try:
            session.execute(query)
            session.commit()
            session.close()
            return True
        except OperationalError, error:
            # dispatch transaction
            session.rollback()
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            return False

    def __operatorNameToMethodName(self, operatorName):
        if operatorName == '==':
            operatorMethodName = '__eq__'
        elif operatorName == '!=':
            operatorMethodName = '__ne__'
        elif operatorName == '>':
            operatorMethodName = '__gt__'
        elif operatorName == '>=':
            operatorMethodName = '__ge__'
        elif operatorName == '<':
            operatorMethodName = '__lt__'
        elif operatorName == '<=':
            operatorMethodName = '__le__'
        else:
            operatorMethodName = '__eq__'

        return operatorMethodName

    # classInstances must be list
    def insertObjectList(self, classInstances):
        if self.__engine is None:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('No engine exists. insertObjectList can not been proceeds')
            return False

        Session = scoped_session(sessionmaker(self.__engine))
        session = Session()
        try:
            session.add_all(classInstances)
            session.commit()
            result = [classInstance.id for classInstance in classInstances]
            session.close()
            return result
        except OperationalError, error:
            # dispatch transaction
            session.rollback()
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            return None

    def insertObject(self, classInstance):
        if self.__engine is None:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('No engine exists. insertObject can not been proceeds')
            return False

        Session = scoped_session(sessionmaker(self.__engine))
        session = Session()
        try:
            session.add(classInstance)
            session.commit()
            result = classInstance.id
            session.close()
            return result
        except OperationalError, error:
            # dispatch transaction
            session.rollback()
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            return None


    def deleteObject(self, classInstance, filterColumn=None, filterValue=None, operatorName='=='):
        Session = scoped_session(sessionmaker(self.__engine))
        session = Session()
        operatorMethodName = self.__operatorNameToMethodName(operatorName)
        try:
            if filterColumn is None \
                or filterValue is None:
                session.delete(classInstance)
            else:
                # get classObject for delete-with-where query
                session.query(classInstance.__class__).filter(
                    getattr(getattr(classInstance.__class__, filterColumn), operatorMethodName)(filterValue)
                ).delete(synchronize_session=False)

            session.commit()
            session.close()
        except Exception, error:
            session.rollback()
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)

    def update(self, classObject, idValue, columnUpdateName, columnUpdateValue, operatorName='=='):
        Session = scoped_session(sessionmaker(self.__engine))
        session = Session()
        operatorMethodName = self.__operatorNameToMethodName(operatorName)
        try:
            session\
                .query(classObject)\
                .filter(getattr(getattr(classObject, configNames.id), operatorMethodName)(idValue))\
                .update({columnUpdateName : columnUpdateValue})
            session.commit()
            session.close()
        except Exception, error:
            session.rollback()
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)

    # columnNames must be list
    # TODO currently supports only one filter per column
    def select(self, classObject, columnNames=None, filterColumn=None, filterValue=None, operatorName='=='):
        if self.__engine is None:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('No engine exists. select can not been proceeds')
            return False

        Session = scoped_session(sessionmaker(self.__engine))
        session = Session()
        operatorMethodName = self.__operatorNameToMethodName(operatorName)
        try:
            if columnNames is None:
                if filterColumn is None \
                    or filterValue is None:
                    result = session.query(classObject).all()
                else:
                    result = session.query(classObject)\
                        .filter(getattr(getattr(classObject, filterColumn), operatorMethodName)(filterValue)).all()

            else:
                if filterColumn is None \
                    or filterValue is None:
                    # we can use such syntax, but we possible do not know which exactly columns need to select,
                    # and also this solution take additional resources to build field-objects
                    #return session.query(classObject.field1, classObject.field2)

                    # woks with SQLAlchemy >= 0.9.0
                    result = session.query(classObject).options(load_only(*columnNames)).all()
                else:
                    result = session.query(classObject).options(load_only(*columnNames))\
                        .filter(getattr(getattr(classObject, filterColumn), operatorMethodName)(filterValue)).all()
            session.close()
            return result

        except OperationalError, error:
            # dispatch transaction
            session.rollback()
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            return None


    def dropDatabase(self, user, password, hostname, databaseName):
        if self.__engine is None:
            self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeRawQuery('drop database %s' % databaseName)


    def createDatabase(self, user, password, hostname, databaseName):
        if self.__engine is None:
            self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeRawQuery('create database %s' % databaseName)


    def useDatabase(self, user, password, hostname, databaseName):
        if self.__engine is None:
            self.getDatabaseEngine(user, password, hostname, databaseName)

        return self.executeRawQuery('use %s' % databaseName)


    def getDatabaseEngine(self, user, password, hostname, databaseName, createIfNotExists=False):
        connectionString = 'mysql://' + user + ':' + password + '@' + hostname
        self.__engine = create_engine(connectionString, encoding='latin1', echo=True)
        self.useDatabase(user, password, hostname, databaseName)

        if createIfNotExists:
            self.createDatabase(user, password, hostname, databaseName)
            self.useDatabase(user, password, hostname, databaseName)

    # this method creates tables from config file and, if "recreateDatabase" set to True, recreates database
    # this method will return False in any case of problems, also if database doesn't exists
    def createDatabaseTables(self, user, password, hostname, databaseName, recreateDatabase=False,
                             createTablesSeparately=True):
        self.getDatabaseEngine(user, password, hostname, databaseName)

        if recreateDatabase:
            self.dropDatabase(user, password, hostname, databaseName)
            self.createDatabase(user, password, hostname, databaseName)
            self.useDatabase(user, password, hostname, databaseName)
        elif self.useDatabase(user, password, hostname, databaseName) == False:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Database %s does not exists' % databaseName)
            return False

        # load analysing tables
        tables = commonFunctions.getSectionContent(configNames.configFileName, r'[^\n\s=,]+\s*:\s*[^\n\s=,]+', 'Extractors functions')

        # load extra tables
        extraTables = commonFunctions.getSectionContent(configNames.configFileName, r'[^\n\s=,]+\s*:\s*[^\n\s=,]+',
                                                        self.__extraTables)

        # load extra columns
        extraColumns = commonFunctions.getSectionContent(configNames.configFileName, r'[^\n\s=,]+\s*:\s*[^\n\s=,]+', self.__extraColumns)

        # load tables relations
        self.__tableRelationsDictionary = commonFunctions.getSectionContent(configNames.configFileName, r'[^\n\s=,]+\s*:\s*[^\n\s=,]+\s*:\s*[^\n\s=,]+',
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
                self.createTable(key, columns, self.__tableRelationsDictionary, createTablesSeparately)
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