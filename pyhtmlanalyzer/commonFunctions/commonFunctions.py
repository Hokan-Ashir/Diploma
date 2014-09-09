from copy import copy, deepcopy
from datetime import date, datetime
import logging
import re

__author__ = 'hokan'


class commonFunctions:
    # replace 'old' value with 'new' value from text, WITHOUT replacing 'old' values in single or double quotes
    # taken from: http://bytes.com/topic/python/answers/38845-replace-string-except-inside-quotes
    # NOTE: thus replace commented strings
    @staticmethod
    def replaceUnquoted(text, old, new, quote='"', ignoreCase=True):
        if ignoreCase:
            text = text.upper()
            old = old.upper()
            new = new.upper()

        # suitable for one type of quotes
        #regExp = re.compile(r'%s([^\\%s]|\\[\\%s])*%s' % (quote, quote, quote, quote))
        quote1 = "'"
        # suitable for both types of quotes
        regExp = re.compile(r'(%s|%s)([^\\(%s|%s)]|\\[\\(%s|%s)])*(%s|%s)' % (quote, quote1,
                                                                              quote, quote1,
                                                                              quote, quote1,
                                                                              quote, quote1))

        out = ''
        last_pos = 0
        for m in regExp.finditer(text):
            out += text[last_pos:m.start()].replace(old, new)
            out += m.group()
            last_pos = m.end()

        return out + text[last_pos:].replace(old, new)

    # methods "getModuleContent", "getSectionContent" and "getAllContent"
    # are designed to parse files with structure like this:
    # {Section 0}
    # [module 1]
    # #feature0 : propetry0, -- this is a comment
    # feature1 = propetry1, propetry2, propetry3,
    # feature2 = propetry4, propetry5, propetry6
    # feature3
    #
    # {Section 1}
    # [module 1]
    # feature0 : propetry0,
    # feature1 = propetry1, propetry2, propetry3,
    # feature2 = propetry4, propetry5, propetry6
    # feature3
    #
    # [module 2]
    # feature.4 = propetry7, propetry8, propetry9,
    # feature.5 = propetry10, propetry11, propetry12
    # feature.6
    #
    # {Section 2}
    # [module 3]
    # feature1 : propetry1,
    # feature2 : propetry2
    # feature3
    #
    # [module 4]
    # feature4 : propetry3,
    # feature5 : propetry4
    # feature6

    @staticmethod
    def getModuleContent(fileName, regexp, sectionName, moduleName):
        result = commonFunctions.getAllContent(fileName, regexp, sectionName, moduleName)
        if not result:
            logger = logging.getLogger('commonFunctions')
            logger.warning('No data exists for this module')
            return None
        else:
            try:
                return result[sectionName][moduleName]
            except KeyError, error:
                logger = logging.getLogger('commonFunctions')
                logger.exception(error)
                return None

    @staticmethod
    def getSectionContent(fileName, regexp, sectionName):
        result = commonFunctions.getAllContent(fileName, regexp, sectionName)
        if not result:
            logger = logging.getLogger('commonFunctions')
            logger.warning('No data exists for this section')
        else:
            try:
                return result[sectionName]
            except KeyError, error:
                logger = logging.getLogger('commonFunctions')
                logger.exception(error)
                return None

    @staticmethod
    def getAllContent(fileName, regexp, searchSectionName=None, searchModuleName=None):
        result = {}
        sectionBegin = False
        sectionName = None
        moduleName = None
        moduleBegin = False
        compiledRegExp = re.compile(regexp)

        with open(fileName, 'r') as inFile:
            sectionDictionary = {}
            moduleList = []
            for line in inFile:
                # pass comments
                if line.startswith('#'):
                    continue

                # search specific section
                if searchSectionName is not None \
                    and not sectionBegin and line.lstrip('{').rstrip('}\n') != searchSectionName:
                    continue

                if line.startswith('{') and line.endswith('}\n'):
                    # write what we've got from previous module
                    if moduleBegin:
                        if moduleList and moduleName != '':
                            sectionDictionary[moduleName] = copy(moduleList)
                            del moduleList[:]

                    # write what we've got from previous section
                    if sectionBegin:
                        if sectionDictionary and sectionName != '':
                            result[sectionName] = deepcopy(sectionDictionary)
                            for key in sectionDictionary.keys():
                                del sectionDictionary[key]

                        # if we search for specific section and enter next one, specific section must be already parsed
                        # so we can return result already
                        if searchSectionName is not None:
                            return result

                    sectionName = line.lstrip('{').rstrip('}\n')
                    sectionBegin = True
                    moduleBegin = False
                    continue

                elif sectionBegin and line.startswith('[') and line.endswith(']\n'):
                    # search specific module
                    if searchModuleName is not None \
                        and not moduleBegin and line.lstrip('[').rstrip(']\n') != searchModuleName:
                        continue

                    # write what we've got from previous module
                    if moduleBegin:
                        if moduleList and moduleName != '':
                            sectionDictionary[moduleName] = copy(moduleList)
                            del moduleList[:]

                    moduleName = line.lstrip('[').rstrip(']\n')
                    moduleBegin = True
                    continue
                elif moduleBegin:
                    found = re.findall(compiledRegExp, line)
                    # if list not empty
                    if found:
                        if len(found) == 1:
                            moduleList.append(found[0])
                        else:
                            moduleList.append(found)

            # also write content from last module. If it's exists
            if moduleBegin:
                if moduleList and moduleName != '':
                    sectionDictionary[moduleName] = copy(moduleList)
                    del moduleList[:]

            # also write content from last section. If it's exists
            if sectionBegin:
                if sectionDictionary and sectionName != '':
                    result[sectionName] = deepcopy(sectionDictionary)
                    for key in sectionDictionary.keys():
                        del sectionDictionary[key]

        return result

    # this is wrapper for every function, that wished to be called in separate process via processProxy
    # common usage:
    # class Foo:
    # def bar(self, u):
    #   u += 165
    #   return u
    #
    #
    # q = Queue()
    # u = 72
    # foo = Foo()
    # p1 = processProxy(None, [foo, {'u' : u}, q, 'bar'], commonFunctions.callFunctionByNameQeued)
    # p1.run()
    #
    # l = q.get()
    #
    # output: ['bar', 237]
    #
    @staticmethod
    def callFunctionByNameQeued(classInstance, arguments, queue, methodName):
        result = None
        try:
            result = getattr(classInstance, methodName)(**arguments)
        except Exception, error:
            logger = logging.getLogger('callFunctionByNameQeued')
            logger.error(classInstance)
            logger.error(methodName)
            logger.error(arguments)
            logger.exception(error)
            pass

        return queue.put([methodName, result])



    # inspired by:
    # http://www.pythonexamples.org/2011/01/12/how-to-dynamically-create-a-class-at-runtime-in-python/
    # http://stackoverflow.com/questions/209840/map-two-lists-into-a-dictionary-in-python
    # http://dietbuddha.blogspot.ru/2012/12/python-metaprogramming-dynamically.html

    # classMemberList and classMemberListValues must have same length
    # methodsList and methodNameList also must have same length
    @staticmethod
    def makeClass(className, baseClasses, classMemberList, classMemberListValues=None, methodsList=None,
                  methodNameList=None):
        # TODO check of other input parameters

        # make dict of new class with specific members ...
        dictOfClassFields = {}
        if classMemberListValues is None:
            for item in classMemberList:
                dictOfClassFields[item] = None
        else:
            for i in xrange(0, len(classMemberList)):
                dictOfClassFields[classMemberList[i]] = classMemberListValues[i]
                #dictOfClassFields = dict(zip(classMemberList, classMemberListValues))

        # ... and also attach specific class methods
        # NOTE: all methods/functions you would like to add MUST have method-like signature (first parameter must be 'self')
        # i.e:
        # def f (self, x)
        # 	print('in f function ' + str(x))
        #
        if methodsList is not None:
            for i in xrange(0, len(methodNameList)):
                # also possible to extract methods names from method itself
                # dictOfClassFields[methodsList[i].__name__] = methodsList[i]

                # but methodNameList needed to make possible to change __XXXXX__ methods content
                dictOfClassFields[methodNameList[i]] = methodsList[i]

        # create new class with specific class members ...
        newClass = type(
            className,
            tuple(baseClasses),
            dictOfClassFields
        )

        return newClass

    @staticmethod
    def makeClassByDictionary(className, baseClasses, classMemberDictionary, methodsList=None, methodNameList=None):
        return commonFunctions.makeClass(className, baseClasses,
                                  classMemberDictionary.keys(),
                                  classMemberDictionary.values(),
                                  methodsList, methodNameList)

    @staticmethod
    def getObjectNamesFromFile(fileName):
        try:
            objectList = []
            with open(fileName, 'r') as inputFile:
                for line in inputFile:
                    if not line.startswith('#'):
                        objectList.append(line.rstrip('\n'))
            return objectList
        except IOError, error:
            logger = logging.getLogger("commonFunctions")
            logger.error(error)
            return None

    @staticmethod
    def recursiveFlattenList(listData):
        resultList = []
        for value in listData:
            if isinstance(value, (dict)):
                result = commonFunctions.recursiveFlattenDict(value)
                if result:
                    resultList = resultList + result
            elif isinstance(value, (list)):
                result = commonFunctions.recursiveFlattenList(value)
                if result:
                    resultList = resultList + result
            elif isinstance(value, (str, unicode, datetime, date)):
                continue
                #resultList.append(value)
            else:
                # numbers only or None values, that automatically turns to False
                resultList.append(value if value is not None else False)

        return resultList

    @staticmethod
    def recursiveFlattenDict(dictData):
        resultList = []
        for name, value in dictData.items():
            if isinstance(value, (dict)):
                result = commonFunctions.recursiveFlattenDict(value)
                if result:
                    resultList = resultList + result
            elif isinstance(value, (list)):
                result = commonFunctions.recursiveFlattenList(value)
                if result:
                    resultList = resultList + result
            elif isinstance(value, (str, unicode, datetime, date)):
                continue
                #resultList.append(value)
            else:
                # numbers only or None values, that automatically turns to False
                resultList.append(value if value is not None else False)

        return resultList