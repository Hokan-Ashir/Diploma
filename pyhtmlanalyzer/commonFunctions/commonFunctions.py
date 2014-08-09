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
    def getAnalyzeFunctionList(configFileName, moduleName):
        if moduleName is None or moduleName == '':
            return None

        configFile = open(configFileName, 'r')
        moduleFound = False
        regExp = re.compile(r'[^\n\s=,]+')
        for line in configFile:
            # decide which functions belongs to which module
            if line.startswith(moduleName):
                parseResult = re.findall(regExp, line)
                if parseResult == []:
                    return []
                else:
                    return parseResult[1:]

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
    # p1 = processProxy(None, [foo, [u], q, 'bar'], commonFunctions.callFunctionByName)
    # p1.run()
    #
    # l = q.get()
    #
    @staticmethod
    def callFunctionByNameQeued(classInstance, arguments, queue, methodName):
        result = None
        try:
            result = getattr(classInstance, methodName)(*arguments)
        except TypeError:
            # TODO write to log "No such function exists"
            pass

        return queue.put([methodName, result])