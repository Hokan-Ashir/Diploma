import re

__author__ = 'hokan'

class commonFunctions:
    # replace 'old' value with 'new' value from text, WITHOUT replacing 'old' values in single or double quotes
    # taken from: http://bytes.com/topic/python/answers/38845-replace-string-except-inside-quotes
    # NOTE: thus replace commented strings
    @staticmethod
    def replaceUnquoted(text, old, new, quote = '"', ignoreCase = True):
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

    @staticmethod
    def getAnalyzeFunctionList(configFileName, moduleName, includeFunctionReturnValueTypes = False):
        if moduleName is None or moduleName == '':
            return None

        configFile = open(configFileName, 'r')
        moduleFound = False

        # search for pair look like "functionName : functionReturnValueType"
        regExp = re.compile(r'[^\n\s=,]+\s*:\s*[^\n\s=,]+')
        for line in configFile:
            # decide which functions belongs to which module
            if line.startswith(moduleName):
                parseResult = re.findall(regExp, line)
                if parseResult == []:
                        return []

                # also strip front and back spaces
                if includeFunctionReturnValueTypes:
                    return [item.replace(' ', '').split(':') for item in parseResult]
                else:
                    return [item.replace(' ', '').split(':')[0] for item in parseResult]

            # comments or not module that we are looking for
            if line.startswith("#") or moduleFound == False:
                continue

        configFile.close()
        return []

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
        except TypeError, error:
            # TODO write to log "No such function exists"
            print(error)
            pass

        return queue.put([methodName, result])

    @staticmethod
    # inspired by:
    # http://www.pythonexamples.org/2011/01/12/how-to-dynamically-create-a-class-at-runtime-in-python/
    # http://stackoverflow.com/questions/209840/map-two-lists-into-a-dictionary-in-python
    # http://dietbuddha.blogspot.ru/2012/12/python-metaprogramming-dynamically.html

    # classMemberList and classMemberListValues must have same length
    # methodsList and methodNameList also must have same length
    def makeClass(className, baseClasses, classMemberList, classMemberListValues = None, methodsList = None,
                  methodNameList = None):
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