#!/usr/bin/env/ python
# -*- coding: utf-8 -*-
# solution for non-unicode symbols
# taken from: http://godovdm.blogspot.ru/2012/02/python-27-unicode.html
#from __future__ import unicode_literals
from multiprocessing import Queue
from collections import defaultdict
from copy import copy, deepcopy
import hashlib
from math import log
import re
import timeit
import libemu
from pyhtmlanalyzer import CLSID
from pyhtmlanalyzer.commonFunctions import jsVariableRegExp
from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.processProxy import processProxy
from pyhtmlanalyzer.full.commonAnalysisData import commonAnalysisData

__author__ = 'hokan'

class scriptAnalyzer(commonAnalysisData):
    configDict = None
    uri = None
    listOfScriptTagsText = None
    currentlyAnalyzingScriptCode = None

    # this list contain string like "X:Y", where X is real source line in script, and Y is order number in parser list
    # this complication is for cases when site consists of created several very long lines of html-code
    listOfScriptTagsTextSourcelines = None
    listOfIncludedScriptFiles = None
    listOfIncludedScriptFilesContent = None
    commentsRegExp = None
    quotedStringsRegExp = None
    dictOfSymbolsProbability = None

    listOfAnalyzeFunctions = []

    # constructor
    def __init__(self, configDict, xmldata = None, pageReady = None):
        commonAnalysisData.__init__(self, xmldata, pageReady)
        if configDict is not None:
            self.configDict = configDict
        else:
            print("\nInvalid parameters")
            return

        self.listOfAnalyzeFunctions = commonFunctions.getAnalyzeFunctionList('analyzeFunctions', 'script.module')
    #
    ###################################################################################################################

    # number of eval() function calls in pure js inline-code
    def getNumberOfEvalFunctionCalls(self):
        def callbackFunction(text, arguments):
            arguments += text.count('eval(')
            return arguments

        arguments = 0
        return self.analyzeFunction(callbackFunction, arguments, True, True)

    #def getTotalNumberOfEvalFunctionCalls(self):
    #    return sum(self.getNumberOfEvalFunctionCalls())

    def printNumberOfEvalFunctionCalls(self):
        numberOfEvalFunctionCalls = self.getNumberOfEvalFunctionCalls()
        if numberOfEvalFunctionCalls == 0:
            print("\nNone eval() functions calls")
            return

        print("\nTotal number of eval() calls: " + str(numberOfEvalFunctionCalls))
    #
    ###################################################################################################################

    # number of setTimeout(), setInterval() function calls
    def getNumberOfSetTimeoutIntervalCalls(self):
        try:
            listOfFunctions = self.configDict['script.set.timeout.functions']
        except:
            print("\nNone list of set timeout-like functions, can't perform analysis")
            return

        def callbackFunction(text, arguments):
            for i in xrange(len(listOfFunctions)):
                arguments[i] += text.count('%s(' % listOfFunctions[i])
            return arguments

        arguments = [0, 0]
        return self.analyzeFunction(callbackFunction, arguments, True, True)

    def getTotalNumberOfSetTimeoutIntervalCalls(self):
        return sum(self.getNumberOfSetTimeoutIntervalCalls())

    def printNumberOfSetTimeoutIntervalCalls(self):
        listOfSetTimeoutIntervalCalls = self.getNumberOfSetTimeoutIntervalCalls()
        if sum(listOfSetTimeoutIntervalCalls) == 0:
            print("\nNone setTimeout() or setInterval() function calls")
            return

        print("\nTotal number of setTimeout(), setInterval() calls: "
              + str(sum(listOfSetTimeoutIntervalCalls)))
        print("Number of setTimeout() calls: " + str(listOfSetTimeoutIntervalCalls[0]))
        print("Number of setInterval() calls: " + str(listOfSetTimeoutIntervalCalls[1]))
    #
    ###################################################################################################################

    # ratio between words and keywords (numberOfKeyWordsCharacters / totalNumberOfCharacters)
    # list of reserved words is taken
    # from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Reserved_Words
    # function replace keywords from copies of text() node content
    # then calculates number of keyWordCharacters as (totalNumberOfCharacters - numberOfCharactersWithoutKeyWords)
    def getKeywordsToWordsRatio(self):
        try:
            commonListOfKeyWords = self.configDict['script.keywords']
        except:
            print("\nNone keywords list - can't perform analysis")
            return

        def callbackFunction(text, arguments):
            # totalLengthOfScriptContent
            arguments[0] += len(str(text.encode('utf-8')))
            for keyword in commonListOfKeyWords:
                text = commonFunctions.replaceUnquoted(text, keyword, "")
            # totalLengthOfScriptContentWithoutKeywords
            arguments[1] += len(text)
            return arguments

        totalLengthOfScriptContent = 0
        totalLengthOfScriptContentWithoutKeywords = 0
        arguments = [totalLengthOfScriptContent, totalLengthOfScriptContentWithoutKeywords]
        arguments = self.analyzeFunction(callbackFunction, arguments, True, False)

        # division by zero exception
        if arguments[0] == 0:
            return float(0)

        return float(arguments[0] - arguments[1]) / arguments[0]

    def printKeywordsToWordsRatio(self):
        print("\nKeywords-to-words ratio is: " + str(self.getKeywordsToWordsRatio()))
    #
    ###################################################################################################################

    # TODO ask if it's necessary to remove leading and back whitespaces
    # number of long strings
    def getListOfLongStrings(self, stringLength = 40, separatorList = ['\n', ';']):
        separator = '|'.join(separatorList)
        def callbackFunction(text, arguments):
            stringsList = re.split(separator, str(text.encode('utf-8')))
            for string in stringsList:
                if len(string) > stringLength:
                    arguments.append(string)
            return arguments

        return self.analyzeFunction(callbackFunction, [], True, False)

    def getNumberOfLongStrings(self, stringLength = 40, separatorList = ['\n', ';']):
        return len(self.getListOfLongStrings(stringLength, separatorList))

    def printNumberOfLongStrings(self, stringLength = 40, separatorList = ['\n', ';']):
        listOfLongStrings = self.getListOfLongStrings(stringLength, separatorList)
        if len(listOfLongStrings) == 0:
            print("\nNone long strings")
            return

        print("\nTotal number of long strings: " + str(len(listOfLongStrings)))
        print("List of long strings:")
        for string in listOfLongStrings:
            print("length: " + str(len(string)) + "\n\t" + str(string))
    #
    ###################################################################################################################

    # number of built-in functions
    # list is taken from: http://www.w3schools.com/jsref/jsref_obj_global.asp
    # another list presented here: http://www.tutorialspoint.com/javascript/javascript_builtin_functions.htm
    # a lot more functions, but are all these functions built-in?
    # TODO ask this ^
    def getNumberOfBuiltInFunctions(self):
        try:
            listOfBuiltInFunctions = self.configDict["script.built.in.functions"]
        except:
            print("\nNone list of built-in functions - can't perform analysis")
            return


        def callbackFunction(text, arguments):
            for function in listOfBuiltInFunctions:
                arguments[function] += text.count('%s(' % function)
            return arguments

        arguments = defaultdict(int)
        return self.analyzeFunction(callbackFunction, arguments, True, True)

    def getTotalNumberOfBuiltInFunctions(self):
        return sum(self.getNumberOfBuiltInFunctions().values())

    def printNumberOfBuiltInFunctions(self):
        dictNumberOfBuiltInFunctions = self.getNumberOfBuiltInFunctions()
        if dictNumberOfBuiltInFunctions == None or sum(dictNumberOfBuiltInFunctions.values()) == 0:
            print("\nNone built-in functions")
            return

        print("\nTotal number of built-in functions: " + str(sum(dictNumberOfBuiltInFunctions.values())))
        print("Number of built-in functions:")
        for key, value in dictNumberOfBuiltInFunctions.items():
            if value > 0:
                print(str(key) + " : " + str(value))
    #
    ###################################################################################################################

    # script's whitespace percentage
    def getScriptWhitespacePercentage(self):
        def callbackFunction(text, arguments):
            # totalScriptLength
            arguments[0] += len(str(text.encode('utf-8')))
            # whitespaceLength
            arguments[1] += str(text.encode('utf-8')).count(" ")
            return arguments

        totalScriptLength = 0
        whitespaceLength = 0
        arguments = [totalScriptLength, whitespaceLength]
        arguments = self.analyzeFunction(callbackFunction, arguments, True, False)

        # division by zero exception
        if arguments[0] == 0:
            return float(0)

        return float(arguments[1]) / arguments[0]

    def printScriptWhitespacePercentage(self):
        print("\nScript whitespace percentage: " + str(self.getScriptWhitespacePercentage() * 100) + "%")
    #
    ###################################################################################################################

    # average script line length
    def getAverageScriptLength(self):
        def callbackFunction(text, arguments):
            arguments += len(text)
            return arguments

        totalScriptLineLength = 0
        numberOfScriptLines = len(self.listOfScriptTagsText) + len(self.listOfIncludedScriptFiles)
        totalScriptLineLength = self.analyzeFunction(callbackFunction, totalScriptLineLength, True, False)

        # division by zero exception
        if numberOfScriptLines == 0:
            return float(0)

        return float(totalScriptLineLength) / numberOfScriptLines

    def printAverageScriptLineLength(self):
        averageScriptLineLength = self.getAverageScriptLength()
        if averageScriptLineLength == 0:
            print("\nNone script elements - average script length equals 0")
            return

        print("\nAverage script length: " + str(averageScriptLineLength))
    #
    ###################################################################################################################

    # average length of the strings used in the script
    def getAverageLengthOfStringsUsedInScript(self, separatorList = ['\n', ';']):
        separator = '|'.join(separatorList)
        def callbackFunction(text, arguments):
            stringsList = re.split(separator, str(text.encode('utf-8')))
            # totalNumberOfLines
            arguments[0] += len(stringsList)
            for string in stringsList:
                # totalNumberOfCharactersInLines
                arguments[1] += len(string)
            return arguments

        totalNumberOfLines = 0
        totalNumberOfCharactersInLines = 0
        arguments = [totalNumberOfLines, totalNumberOfCharactersInLines]
        arguments = self.analyzeFunction(callbackFunction, arguments, True, False)

        # division by zero exception
        if arguments[0] == 0:
            return float(0)

        return arguments[1] / arguments[0]

    def printAverageLengthOfStringsUsedInScript(self, separatorList = ['\n', ';']):
        averageLineLengthUsedInScript = self.getAverageLengthOfStringsUsedInScript(separatorList)
        if averageLineLengthUsedInScript == 0:
            print("\nNone script elements - average line length used in script equals 0")
            return

        print("\nAverage script line length: " + str(averageLineLengthUsedInScript))
    #
    ###################################################################################################################

    # number of characters in script content
    def getNumberCharactersInScriptContent(self):
        def callbackFunction(text, arguments):
            arguments += len(text)
            return arguments

        numberOfCharactersInPage = 0
        return self.analyzeFunction(callbackFunction, numberOfCharactersInPage, False, False)

    def printNumberCharactersInScriptContent(self):
        print("\nNumber of characters in script: " + str(self.getNumberCharactersInScriptContent()))
    #
    ###################################################################################################################

    #  probability of the script to contain shellcode
    def getShellcodeExistenceProbability(self, stringLength = 40, separatorList = ['\n', ';']):
        listOfLongStrings = self.getListOfLongStrings(stringLength, separatorList)
        listOfQuotedStrings = []
        # get all quoted strings via regExp (see initialize method)
        for string in listOfLongStrings:
            listOfQuotedStrings += re.findall(self.quotedStringsRegExp, string)

        numberOfQuotedStrings = len(listOfQuotedStrings)

        # no quoted string - no PURE shellcode
        if (numberOfQuotedStrings == 0):
            return float(0)

        numberOfShellcodedStrings = 0
        for item in listOfQuotedStrings:
            # method 1: get number of non-printable ASCII characters
            # see http://donsnotes.com/tech/charsets/ascii.html
            regEx = re.compile(r'[\x00-\x1f]+')
            numberOfShellcodedStrings += 1 if re.match(regEx, item) != None else 0

            # method 2: if the string is a consecutive block of characters in the ranges a-f, A-F, 0-9
            regEx = re.compile(r'"([%\\]?[ux][a-fA-f0-9]+)+"')
            numberOfShellcodedStrings += 1 if re.match(regEx, item) != None else 0

            # TODO maybe implement, difficult to get this via RegExp
            # method 3: if certain characters are repeated at regular intervals in the string

        return (float(numberOfShellcodedStrings) / numberOfQuotedStrings) * 100

    def printShellcodeExistenceProbability(self, stringLength = 40, separatorList = ['\n', ';']):
        percentageOfShellcodedQuotedStrings = self.getShellcodeExistenceProbability(stringLength, separatorList)
        print("\nPercentage of shellcoded quoted strings: " + str(percentageOfShellcodedQuotedStrings) + "%")
    #
    ###################################################################################################################

    # probability of the script to contain shellcode (advanced version based on libemu library)
    # see http://nuald.blogspot.ru/2010/10/shellcode-detection-using-libemu.html

    def getShellcodeExistenceProbabilityAdvanced(self, stringLength = 40, separatorList = ['\n', ';']):
        listOfLongStrings = self.getListOfLongStrings(stringLength, separatorList)
        listOfQuotedStrings = []
        # get all quoted strings via regExp (see initialize method)
        for string in listOfLongStrings:
            listOfQuotedStrings += re.findall(self.quotedStringsRegExp, string)

        numberOfQuotedStrings = len(listOfQuotedStrings)

        # no quoted strings - no PURE shellcode
        if numberOfQuotedStrings == 0:
            return float(0)

        numberOfShellcodedStrings = 0
        emulator = libemu.Emulator()
        for item in listOfQuotedStrings:
            numberOfShellcodedStrings += 1 if emulator.test(item) != None else 0

        # NOTE: this library cant recognize shellcode if it has "%u023423" format, that's why we first test strings manually
        # and then replace "%u" with "\\x" if nothing is found
        # Also this library cant recognize "long" characters as \x0099
        if numberOfShellcodedStrings == 0:
            for item in listOfQuotedStrings:
                numberOfShellcodedStrings += 1 if emulator.test(str(item).replace("%u", "\\x")) != None else 0

        return (float(numberOfShellcodedStrings) / numberOfQuotedStrings) * 100

    def printShellcodeExistenceProbabilityAdvanced(self, stringLength = 40, separatorList = ['\n', ';']):
        percentageOfShellcodedQuotedStrings = self.getShellcodeExistenceProbabilityAdvanced(stringLength, separatorList)
        print("\nPercentage of shellcoded quoted strings: " + str(percentageOfShellcodedQuotedStrings) + "%")
    #
    ###################################################################################################################

    # the number of strings containing "iframe"
    def getNumberOfIFrameStrings(self, stringLength = -1, separatorList = ['\n', ';']):
        listOfStrings = self.getListOfLongStrings(stringLength, separatorList)
        listOfStringsWithIFrame = []
        for item in listOfStrings:
            if len(item) > len(commonFunctions.replaceUnquoted(item, '<iframe', '')):
                listOfStringsWithIFrame.append(item)
        return listOfStringsWithIFrame

    def getTotalNumberOfIFrameStrings(self, stringLength = -1, separatorList = ['\n', ';']):
        return len(self.getNumberOfIFrameStrings(stringLength, separatorList))

    def printNumberOfIFrameStrings(self, stringLength = -1, separatorList = ['\n', ';']):
        listOfStringsWithIFrame = self.getNumberOfIFrameStrings(stringLength, separatorList)
        if len(listOfStringsWithIFrame) == 0:
            print("\nNone strings with \'iframe\' tag")
            return

        print("\nTotal number of strings with \'iframe\': " + str(len(listOfStringsWithIFrame)))
        print("Number of strings with \'iframe\':")
        for item in listOfStringsWithIFrame:
            print("length: " + str(len(item)) + "\n\t" + str(item))
    #
    ###################################################################################################################

    # number of suspicious strings
    def getNumberOfSuspiciousStrings(self, stringLength = -1, separatorList = ['\n', ';']):
        try:
            listOfSuspiciousTags = self.configDict["script.suspicious.tags"]
        except:
            print("\nNone list of suspicious tags, can't perform analysis")
            return
        listOfStrings = self.getListOfLongStrings(stringLength, separatorList)
        dictOfSuspiciousStrings = {}
        for item in listOfStrings:
            for item2 in listOfSuspiciousTags:
                if len(item) > len(commonFunctions.replaceUnquoted(item, '<' + item2, '')):
                    dictOfSuspiciousStrings[item2] = item
                    break
        return dictOfSuspiciousStrings

    def getTotalNumberOfSuspiciousStrings(self, stringLength = -1, separatorList = ['\n', ';']):
        return len(self.getNumberOfSuspiciousStrings(stringLength, separatorList))

    def printNumberOfSuspiciousStrings(self, stringLength = -1, separatorList = ['\n', ';']):
        dictOfSuspiciousStrings = self.getNumberOfSuspiciousStrings(stringLength, separatorList)
        if dictOfSuspiciousStrings == None or sum(dictOfSuspiciousStrings.values()) == 0:
            print("\nNone strings with suspicious tags")
            return

        print("\nTotal number of strings with suspicious tags: " + str(sum(dictOfSuspiciousStrings.values())))
        print("Number of strings with suspicious tags:")
        for key, value in dictOfSuspiciousStrings.items():
            print("length: " + str(len(value)) + "\n<" + str(key) + ">:\n\t" + str(value))
    #
    ###################################################################################################################

    # maximum length of the script's strings
    def getMaximumLengthOfScriptStrings(self, separatorList = ['\n', ';']):
        separator = '|'.join(separatorList)
        def callbackFunction(text, arguments):
            stringsList = re.split(separator, str(text.encode('utf-8')))
            for string in stringsList:
                if len(string) > arguments:
                    arguments = len(string)
            return arguments

        maximumLengthOfScripts = 0
        return self.analyzeFunction(callbackFunction, maximumLengthOfScripts, True, False)

    def printMaximumLengthOfScriptStrings(self, separatorList = ['\n', ';']):
        print("\nMaximum length of script strings: " + str(self.getMaximumLengthOfScriptStrings(separatorList)))
    #
    ###################################################################################################################

    # number of suspicious objects used in the script
    def getObjectsWithSuspiciousContent(self):
        # suitable for content (like in 2575.html)
        def callbackFunction(text, arguments):
            for key in CLSID.clsidlist.keys():
                # here and after we upper case regexps, cause in initialization() method we made
                # all script content upper-cased
                regExp = re.compile(r'OBJECT.+CLASSID\s*=\s*[\'"]CLSID:%s' % key)
                numberOfKeyObjects = len(re.findall(regExp, text))
                if numberOfKeyObjects > 0:
                    arguments[key] += numberOfKeyObjects

            for key in CLSID.clsnamelist.keys():
                regExp = re.compile(r'OBJECT.+PROGID\s*=\s*[\'"]%s' % key)
                numberOfKeyObjects = len(re.findall(regExp, text))
                if numberOfKeyObjects > 0:
                    arguments[key] += numberOfKeyObjects
            return arguments

        dictOfSuspiciousObjects = defaultdict(int)

        return self.analyzeFunction(callbackFunction, dictOfSuspiciousObjects, True, False)

    def getTotalNumberOfObjectsWithSuspiciousContent(self):
        return sum(self.getObjectsWithSuspiciousContent().values())

    def printNumberOfObjectsWithSuspiciousContent(self):
        dictOfSuspiciousObjects = self.getObjectsWithSuspiciousContent()
        if sum(dictOfSuspiciousObjects.values()) == 0:
            print("\nNone suspicious objects")
            return

        print("\nTotal number of suspicious objects: " + str(sum(dictOfSuspiciousObjects.values())))
        #sys.stdout.write("Number of suspicious objects:")
        print("Number of suspicious objects:")
        for key, value in dictOfSuspiciousObjects.items():
            if value > 0:
                print(str(key) + ": " + str(value))
    #
    ###################################################################################################################

    # number of long variable or function names used in the code
    def getNumberOfLongVariableOrFunction(self, variableNameLength = 20, functionNameLength = 20):
        # count only variable declarations; they can be only unique
        variableRegExp = re.compile(ur'var[\s\t]+%s{%d,}'
                                    % (jsVariableRegExp.jsVariableNameRegExp, variableNameLength))

        # count all functions;
        # NOTE: can be duplications
        # TODO ask (left or refactor?)
        # we can make set of found functions
        # but need to cut off ending '(' element and leading spaces, tabs, '=' and '.'
        functionRegExp = re.compile(ur'[\s\t=\.\n]+%s{%d,}[\s\t]*\('
                                    % (jsVariableRegExp.jsVariableNameRegExp, functionNameLength))
        def callbackFunction(text, arguments):
            arguments[0] += len(re.findall(variableRegExp, unicode(text).encode('utf8')))
            arguments[1] += len(re.findall(functionRegExp, unicode(text).encode('utf8')))
            return arguments

        numberOfLongVariablesNames = 0
        numberOfLongFunctionsNames = 0
        arguments = [numberOfLongVariablesNames, numberOfLongFunctionsNames]
        return self.analyzeFunction(callbackFunction, arguments, True, False)

    def getTotalNumberOfLongVariableOrFunction(self, variableNameLength = 20, functionNameLength = 20):
        return sum(self.getNumberOfLongVariableOrFunction(variableNameLength, functionNameLength))

    def printNumberOfLongVariableOrFunction(self, variableNameLength = 20, functionNameLength = 20):
        listOfLongVariableOfFunction = self.getNumberOfLongVariableOrFunction(variableNameLength, functionNameLength)
        if sum(listOfLongVariableOfFunction) == 0:
            if listOfLongVariableOfFunction[0] == 0:
                print("\nNone variable names longer than %d chars" % variableNameLength)
            if listOfLongVariableOfFunction[1] == 0:
                print("\nNone function names longer than %d chars" % functionNameLength)
            return

        print("\nTotal number of variable names longer than %d chars and function names longer than %d chars: "
              % (variableNameLength, functionNameLength) + str(sum(listOfLongVariableOfFunction)))
        print("Number of variable names longer than %d chars: " % variableNameLength + str(listOfLongVariableOfFunction[0]))
        print("Number of function names longer than %d chars: " % functionNameLength + str(listOfLongVariableOfFunction[1]))
    #
    ###################################################################################################################

    # get whole script letter-entropy statistics
    def getWholeScriptEntropyStatistics(self):
        def callbackFunction(text, arguments):
            arguments[0] += len(text)
            for letter in text:
                arguments[1][letter] += 1
            return arguments

        # get probability statistics
        totalNumberOfLettersInScript = 0
        dictOfSymbolsProbability = defaultdict(float)
        arguments = [totalNumberOfLettersInScript, dictOfSymbolsProbability]
        arguments = self.analyzeFunction(callbackFunction, arguments, True, False)

        for key, value in arguments[1].items():
            arguments[1][key] /= arguments[0]

        return arguments[1]
    #
    ###################################################################################################################

    # entropy of the script as a whole
    def getScriptWholeEntropy(self):
        def callbackFunction(text, arguments):
            for letter in text:
                if arguments[1][letter] <= 0:
                    continue

                arguments[0] += (arguments[1][letter] * log(arguments[1][letter], 2))
            return arguments

        # in case we're running getScriptEntropy for each script separately, we must recalculate entropy dictionary
        # for every script piece
        if (self.dictOfSymbolsProbability is None or self.currentlyAnalyzingScriptCode is not None):
            # in case we're calculating entropy for each piece of code
            # so dictionary must be removed and recreated
            if self.dictOfSymbolsProbability is not None:
                del self.dictOfSymbolsProbability

            self.dictOfSymbolsProbability = self.getWholeScriptEntropyStatistics()

        # calculate entropy
        entropy = 0.0
        arguments = [entropy, self.dictOfSymbolsProbability]
        arguments = self.analyzeFunction(callbackFunction, arguments, True, False)
        arguments[0] *= -1
        return arguments[0]

    def printScriptWholeEntropy(self):
        print("\nWhole script entropy: " + str(self.getScriptWholeEntropy()))
    #
    ###################################################################################################################

    # entropy of the script nodes
    def getScriptNodesEntropy(self):
        dictOfEntropy = defaultdict(float)

        def callbackFunction(text, arguments, i, inlineTagContent):
            dictOfSymbolsProbability = defaultdict(float)
            totalNumberOfLettersInScript = len(text)
            # get probability statistics
            for letter in text:
                dictOfSymbolsProbability[letter] += 1

            for key, value in dictOfSymbolsProbability.items():
                dictOfSymbolsProbability[key] /= totalNumberOfLettersInScript

            # calculating entropy
            for letter in text:
                if dictOfSymbolsProbability[letter] <= 0:
                    continue

                if inlineTagContent:
                    arguments[self.listOfScriptTagsTextSourcelines[i]] += (dictOfSymbolsProbability[letter] * log(dictOfSymbolsProbability[letter], 2))
                else:
                    arguments[self.listOfIncludedScriptFiles[i]] += (dictOfSymbolsProbability[letter] * log(dictOfSymbolsProbability[letter], 2))

            if inlineTagContent:
                arguments[self.listOfScriptTagsTextSourcelines[i]] *= -1
            else:
                arguments[self.listOfIncludedScriptFiles[i]] *= -1

            return arguments

        for i in xrange(len(self.listOfScriptTagsText)):
            # deleting comments
            text = re.sub(self.commentsRegExp, '', self.listOfScriptTagsText[i])
            dictOfEntropy = callbackFunction(text, dictOfEntropy, i, True)

        for i in xrange(len(self.listOfIncludedScriptFilesContent)):
            # deleting comments
            scriptContent = re.sub(self.commentsRegExp, '', self.listOfIncludedScriptFilesContent[i])
            dictOfEntropy = callbackFunction(scriptContent, dictOfEntropy, i, False)

        return dictOfEntropy


    def printScriptNodesEntropy(self):
        dictOfEntropy = self.getScriptNodesEntropy()
        if sum(dictOfEntropy.values()) == 0:
            print("\nNone script nodes - can't calculate entropy of nodes")
            return

        print("\nEntropy of nodes:")
        for key, value in dictOfEntropy.items():
            print("source line: " + str(key) + "\nentropy: " + str(value))
    #
    ###################################################################################################################

    # maximum entropy of all the script's strings (as whole script)
    def getMaximumEntropyOfWholeScriptStrings(self, separatorList = ['\n', ';']):
        separator = '|'.join(separatorList)
        def callbackFunction(text, arguments):
            entropy = 0.0
            listOfStrings = re.split(separator, text)
            for string in listOfStrings:
                for letter in string:
                    if arguments[2][letter] <= 0:
                        continue

                    entropy += (arguments[2][letter] * log(arguments[2][letter], 2))
                entropy *= -1
                if entropy > arguments[0]:
                    arguments[0] = entropy
                    arguments[1] = string
            return arguments

        # calculate entropy
        maximumEntropy = 0.0
        stringWithMaximumEntropy = ""

         # in case we're running getScriptEntropy for each script separately, we must recalculate entropy dictionary
        # for every script piece
        if (self.dictOfSymbolsProbability is None or self.currentlyAnalyzingScriptCode is not None):
            # in case we're calculating entropy for each piece of code
            # so dictionary must be removed and recreated
            if self.dictOfSymbolsProbability is not None:
                del self.dictOfSymbolsProbability

            self.dictOfSymbolsProbability = self.getWholeScriptEntropyStatistics()

        arguments = [maximumEntropy, stringWithMaximumEntropy, self.dictOfSymbolsProbability]
        arguments = self.analyzeFunction(callbackFunction, arguments, True, False)
        return [arguments[0], arguments[1]]

    def printMaximumEntropyOfWholeScriptStrings(self, separatorList = ['\n', ';']):
        listOfMaximumStringEntropy = self.getMaximumEntropyOfWholeScriptStrings(separatorList)
        if listOfMaximumStringEntropy[0] == 0.0:
            print("\nNone script nodes - can't calculate string maximum entropy (whole script)")
            return

        print("\nMaximum string entropy (whole script): " + str(listOfMaximumStringEntropy[0]))
        print("of string: " + str(listOfMaximumStringEntropy[1]))
    #
    ###################################################################################################################

    # maximum entropy of all the script's strings (as script node)
    def getMaximumEntropyOfScriptStrings(self, separatorList = ['\n', ';']):
        dictOfTagsEntropy = {}
        separator = '|'.join(separatorList)

        def callbackFunction(text, arguments, i, inlineTagContent):
            dictOfSymbolsProbability = defaultdict(float)
            for letter in text:
                dictOfSymbolsProbability[letter] += 1
            for key, value in dictOfSymbolsProbability.items():
                dictOfSymbolsProbability[key] /= len(text)

            # calculate entropy
            maximumEntropy = 0.0
            stringWithMaximumEntropy = ""
            listOfStrings = re.split(separator, text)
            for string in listOfStrings:
                entropy = 0.0
                for letter in string:
                    if dictOfSymbolsProbability[letter] <= 0:
                        continue

                    entropy += (dictOfSymbolsProbability[letter] * log(dictOfSymbolsProbability[letter], 2))
                entropy *= -1
                if entropy > maximumEntropy:
                    maximumEntropy = entropy
                    stringWithMaximumEntropy = string

            if inlineTagContent:
                dictOfTagsEntropy[self.listOfScriptTagsTextSourcelines[i]] = [maximumEntropy, stringWithMaximumEntropy]
            else:
                dictOfTagsEntropy[self.listOfIncludedScriptFiles[i]] = [maximumEntropy, stringWithMaximumEntropy]

            return arguments

        for i in xrange(len(self.listOfScriptTagsText)):
            # deleting comments
            text = re.sub(self.commentsRegExp, '', self.listOfScriptTagsText[i])
            dictOfTagsEntropy = callbackFunction(text, dictOfTagsEntropy, i, True)

        for i in xrange(len(self.listOfIncludedScriptFilesContent)):
            # deleting comments
            scriptContent = re.sub(self.commentsRegExp, '', self.listOfIncludedScriptFilesContent[i])
            dictOfTagsEntropy = callbackFunction(scriptContent, dictOfTagsEntropy, i, False)

        return dictOfTagsEntropy

    def printMaximumEntropyOfScriptStrings(self, separatorList = ['\n', ';']):
        dictOfTagsEntropy = self.getMaximumEntropyOfScriptStrings(separatorList)
        if len(dictOfTagsEntropy) == 0:
            print("\nNone script nodes - can't calculate string maximum entropy (by nodes)")
            return

        print("\nMaximum string entropy (by nodes)")
        for key, value in dictOfTagsEntropy.items():
            print("source line: " + str(key))
            print("maximum string entropy of this node: " + str(value[0]))
            print("of string: " + str(value[1].encode('utf-8')))
    #
    ###################################################################################################################

    # the entropy of the strings declared in the script (probability from all script)
    def getEntropyOfStringsDeclaredInScriptByWholeScript(self):
        def callbackFunction(text, arguments):
            listOfStrings = re.findall(self.quotedStringsRegExp, text)
            for string in listOfStrings:
                entropy = 0.0
                for letter in string:
                    if arguments[1][letter] <= 0:
                        continue

                    entropy += (arguments[1][letter] * log(arguments[1][letter], 2))
                entropy *= -1
                arguments[0][string] = entropy
            return arguments

        if (self.dictOfSymbolsProbability is None):
            self.dictOfSymbolsProbability = self.getWholeScriptEntropyStatistics()

        dictOfStringsEntropy = {}
        arguments = [dictOfStringsEntropy, self.dictOfSymbolsProbability]
        arguments = self.analyzeFunction(callbackFunction, arguments, True, False)
        return arguments[0]

    def printEntropyOfStringsDeclaredInScriptByWholeScript(self):
        dictOfStringsEntropy = self.getEntropyOfStringsDeclaredInScriptByWholeScript()
        if len(dictOfStringsEntropy) == 0:
            print("\nNone script nodes - can't calculate entropy of strings declared in script (by whole script)")
            return

        print("\nEntropy of strings declared in script (by whole script)")
        for key, value in dictOfStringsEntropy.items():
            print("string: " + str(key.encode('utf-8')) + "\nentropy: " + str(value))
    #
    ###################################################################################################################

    # the entropy of the strings declared in the script (probability from nodes)
    def getEntropyOfStringsDeclaredInScriptByNodes(self):
        dictOfStringsEntropy = {}

        def callbackFunction(text, arguments):
            dictOfSymbolsProbability = defaultdict(float)
            # calculate probability statistics
            for letter in text:
                dictOfSymbolsProbability[letter] += 1
            for key, value in dictOfSymbolsProbability.items():
                dictOfSymbolsProbability[key] /= len(text)

            # get all quoted strings via regExp
            listOfStrings = re.findall(self.quotedStringsRegExp, text)
            for string in listOfStrings:
                entropy = 0.0
                for letter in string:
                    if dictOfSymbolsProbability[letter] <= 0:
                        continue

                    entropy += (dictOfSymbolsProbability[letter] * log(dictOfSymbolsProbability[letter], 2))
                entropy *= -1
                arguments[string] = entropy

            return arguments

        return self.analyzeFunction(callbackFunction, dictOfStringsEntropy, True, False)

    def printEntropyOfStringsDeclaredInScriptByNodes(self):
        dictOfStringsEntropy = self.getEntropyOfStringsDeclaredInScriptByNodes()
        if len(dictOfStringsEntropy) == 0:
            print("\nNone script nodes - can't calculate entropy of strings declared in script (by nodes)")
            return

        print("\nEntropy of strings declared in script (by nodes)")
        for key, value in dictOfStringsEntropy.items():
            print("string: " + str(key.encode('utf-8')) + "\nentropy: " + str(value))
    #
    ###################################################################################################################

    # script content hashing
    # NOTE: we remove comments by default
    def getScriptContentHashingAll(self, includeComments = False):
        dictOfScriptTagsHashed = {}
        def callbackFunction(text, arguments, i, inlineTagContent):
            if inlineTagContent:
                arguments[self.listOfScriptTagsTextSourcelines[i]] = [hashlib.sha256(text.encode('utf-8')).hexdigest(),
                                                                      hashlib.sha512(text.encode('utf-8')).hexdigest()]
            else:
                arguments[self.listOfIncludedScriptFiles[i]] = [hashlib.sha256(text.encode('utf-8')).hexdigest(),
                                                                hashlib.sha512(text.encode('utf-8')).hexdigest()]

            return arguments

        for i in xrange(len(self.listOfScriptTagsText)):
            text = copy(self.listOfScriptTagsText[i])
            if not includeComments:
                # deleting comments
                text = re.sub(self.commentsRegExp, '', self.listOfScriptTagsText[i])
            dictOfScriptTagsHashed = callbackFunction(text, dictOfScriptTagsHashed, i, True)

        for i in xrange(len(self.listOfIncludedScriptFilesContent)):
            scriptContent = copy(self.listOfIncludedScriptFilesContent[i])
            if not includeComments:
                # deleting comments
                scriptContent = re.sub(self.commentsRegExp, '', self.listOfIncludedScriptFilesContent[i])
            dictOfScriptTagsHashed = callbackFunction(scriptContent, dictOfScriptTagsHashed, i, False)

        return dictOfScriptTagsHashed

    def getScriptContentHashing(self, includeComments = False):
        if self.currentlyAnalyzingScriptCode >= len(self.listOfScriptTagsText):
            text = copy(self.listOfIncludedScriptFilesContent[self.currentlyAnalyzingScriptCode - len(self
            .listOfScriptTagsText)])
        else:
            text = copy(self.listOfScriptTagsText[self.currentlyAnalyzingScriptCode])

        if not includeComments:
            # deleting comments
            text = re.sub(self.commentsRegExp, '', text)

        return [hashlib.sha256(text.encode('utf-8')).hexdigest(), hashlib.sha512(text.encode('utf-8')).hexdigest()]

    def printScriptContentHashing(self):
        dictOfScriptTagsHashed = self.getScriptContentHashingAll()
        if len(dictOfScriptTagsHashed) == 0:
            print("\nNone script content to hash")
            return

        print("\nScript content hashing")
        for key, value in dictOfScriptTagsHashed.items():
            print("line: " + str(key) + "\n\tsha256: " + str(value[0]) + "\n\tsha512: " + str(value[1]))
    #
    ###################################################################################################################

    # number of event attachments
    def getNumberOfEventAttachments(self):
        try:
            listOfEvents = self.configDict["script.events"]
        except:
            print("\nNone list of events, can't perform analysis")
            return

        try:
            listOfAttachmentFunctionsEvents = self.configDict["script.event.functions"]
        except:
            print("\nNone list of event attachment functions, can't perform analysis")
            return

        def callbackFunction(text, arguments):
            for eventFunction in listOfAttachmentFunctionsEvents:
                for event in listOfEvents:
                    # addEventListener and initEvent get event _without_ 'on' characters at the beginning
                    if str(eventFunction).startswith("add") or str(eventFunction).startswith("init"):
                        # regexp, for both single & double quoted strings
                        regEx = re.compile(r'%s\s*\(\s*"%s"|%s\s*\(\s*\'%s\''
                                           % (eventFunction,
                                              str(event).lstrip("on"),
                                              eventFunction,
                                              str(event).lstrip("on")))
                    else:
                        regEx = re.compile(r'%s\s*\(\s*"%s"|%s\s*\(\s*\'%s\''
                                           % (eventFunction,
                                              event,
                                              eventFunction,
                                              event))
                    arguments[eventFunction][event] += len(re.findall(regEx, text))
            return arguments

        dictOfEventAttachments = {}
        for eventFunction in listOfAttachmentFunctionsEvents:
            dictOfEventAttachments[eventFunction] = {}
            for event in listOfEvents:
                dictOfEventAttachments[eventFunction][event] = 0
        return self.analyzeFunction(callbackFunction, dictOfEventAttachments, True, True)

    def printNumberOfEventAttachments(self):
        dictOfEventAttachments = self.getNumberOfEventAttachments()
        if dictOfEventAttachments == None:
            print("\nNone event attachments")
            return

        # split conditions due to slow speed of sum equation
        numberOfEventAttachments = 0
        for item in dictOfEventAttachments.values():
            numberOfEventAttachments += sum(dict(item).values())

        if numberOfEventAttachments == 0:
            print("\nNone event attachments")
            return

        print("\nTotal number of event attachments: " + str(numberOfEventAttachments))
        print("Number of event attachments:")
        for key, value in dictOfEventAttachments.items():
            print(str(key) + ": ")
            for key2, value2 in value.items():
                print("\t " + str(key2) + ": " + str(value2))
    #
    ###################################################################################################################

    # number of direct string assignments
    def getNumberOfDirectStringAssignments(self):
        # get all quoted strings via regExp (see initialize method)
        def callbackFunction(text, arguments):
            arguments += len(re.findall(self.quotedStringsRegExp, text))
            return arguments

        numberOfDirectStringAssignments = 0
        return self.analyzeFunction(callbackFunction, numberOfDirectStringAssignments, True, False)

    def printNumberOfDirectStringAssignments(self):
        numberOfDirectStringAssignments = self.getNumberOfDirectStringAssignments()
        if numberOfDirectStringAssignments == 0:
            print("\n None string assignments")
            return

        print("\nTotal number of string assignments: " + str(numberOfDirectStringAssignments))
    #
    ###################################################################################################################

    # number of string modification functions
    def getNumberOfStringModificationFunctions(self):
        try:
            listOfStringModificationFunctions = self.configDict["script.string.modification.functions"]
        except:
            print("\nNone list of string modification functions, can't perform analysis")
            return

        def callbackFunction(text, arguments):
            for functionName in listOfStringModificationFunctions:
                regEx = re.compile(r'\.%s\s*\(\s*' % functionName)
                arguments[functionName] += len(re.findall(regEx, text))
            return arguments

        dictOfStringModificationFunctions = defaultdict(int)
        return self.analyzeFunction(callbackFunction, dictOfStringModificationFunctions, True, True)

    def printNumberOfStringModificationFunctions(self):
        dictOfStringModificationFunctions = self.getNumberOfStringModificationFunctions()
        if dictOfStringModificationFunctions == None or sum(dictOfStringModificationFunctions.values()) == 0:
            print("\nNone string modification functions")
            return

        print("\nTotal number of string modification functions: " + str(sum(dictOfStringModificationFunctions.values())))
        for key, value in dictOfStringModificationFunctions.items():
            if value > 0:
                print(str(key) + ": " + str(value))
    #
    ###################################################################################################################

    # number of built-in functions commonly used for deobfuscation
    def getNumberBuiltInDeobfuscationFunctions(self):
        try:
            listOfDeobfuscationFunctions = self.configDict["script.deobfuscation.functions"]
        except:
            print("\nNone list of deobfuscation functions, can't perform analysis")
            return

        def callbackFunction(text, arguments):
            for functionName in listOfDeobfuscationFunctions:
                regEx = re.compile(r'%s\s*\(\s*' % functionName)
                arguments[functionName] += len(re.findall(regEx, text))
            return arguments

        dictOfBuiltInDeobfuscationFunctions = defaultdict(int)
        return self.analyzeFunction(callbackFunction, dictOfBuiltInDeobfuscationFunctions, True, True)

    def printNumberBuiltInDeobfuscationFunctions(self):
        dictOfBuiltInDeobfuscationFunctions = self.getNumberBuiltInDeobfuscationFunctions()
        if dictOfBuiltInDeobfuscationFunctions == None or sum(dictOfBuiltInDeobfuscationFunctions.values()) == 0:
            print("\nNone deobfuscation functions")
            return

        print("\nTotal number of deobfuscation functions: " + str(sum(dictOfBuiltInDeobfuscationFunctions.values())))
        for key, value in dictOfBuiltInDeobfuscationFunctions.items():
            if value > 0:
                print(str(key) + ": " + str(value))
    #
    ###################################################################################################################

    # number of DOM modification functions
    def getNumberOfDOMModificationFunctions(self):
        try:
            listOfDOMModifyingMethods = self.configDict["script.DOM.modifying.methods"]
        except:
            print("\nNone list of DOM-modifying functions, can't perform analysis")
            return

        def callbackFunction(text, arguments):
            for method in listOfDOMModifyingMethods:
                regEx = re.compile(r'.%s\s*\(\s*' % method)
                arguments[method] += len(re.findall(regEx, text))
            return arguments

        dictOfDOMModyfingFunctions = defaultdict(int)
        return self.analyzeFunction(callbackFunction, dictOfDOMModyfingFunctions, True, True)

    def printNumberOfDOMModificationFunctions(self):
        dictOfDOMModyfingFunctions = self.getNumberOfDOMModificationFunctions()
        if dictOfDOMModyfingFunctions == None or sum(dictOfDOMModyfingFunctions.values()) == 0:
            print("\nNone DOM-modifying functions")
            return

        print("\nTotal number of DOM-modifying functions: " + str(sum(dictOfDOMModyfingFunctions.values())))
        for key, value in dictOfDOMModyfingFunctions.items():
            if value > 0:
                print(str(key) + ": " + str(value))
    #
    ###################################################################################################################

    # number of fingerprinting functions
    def getNumberOfFingerPrintingFunctions(self):
        try:
            listOfFingerprintingFunctions = self.configDict["script.fingerprinting.functions"]
        except:
            print("\nNone list of fingerprinting functions, can't perform analysis")
            return

        def callbackFunction(text, arguments):
            for function in listOfFingerprintingFunctions:
                arguments[function] += text.count(function)
            return arguments

        dictOfFingerprintingFunctions = defaultdict(int)
        return self.analyzeFunction(callbackFunction, dictOfFingerprintingFunctions, True, True)

    def printNumberOfFingerPrintingFunctions(self):
        dictOfFingerprintingFunctions = self.getNumberOfFingerPrintingFunctions()
        if dictOfFingerprintingFunctions == None or sum(dictOfFingerprintingFunctions.values()) == 0:
            print("\nNone fingerprinting functions")
            return

        print("\nTotal number of fingerprinting functions: " + str(sum(dictOfFingerprintingFunctions.values())))
        for key, value in dictOfFingerprintingFunctions.items():
            if value > 0:
                print(str(key) + ": " + str(value))
    #
    ###################################################################################################################

    # initialization
    def initialization(self, xmldata, pageReady, uri):
        self.setXMLData(xmldata)
        self.setPageReady(pageReady)
        self.uri = uri
        listOfInlineScriptTags = self.xmldata.xpath('//script[not(@src)]')

        # we turn all text to upper register to speed up analysis in getObjectsWithSuspiciousContent() method
        # in which we can not to use re.I (case insensitive) flag
        self.listOfScriptTagsText = [item.xpath('text()')[0].upper() for item in listOfInlineScriptTags]
        self.listOfScriptTagsTextSourcelines = [str(item.sourceline) + ":" + str(listOfInlineScriptTags.index(item)) for item in listOfInlineScriptTags]

        # NOTE: we do not make dict of files of file content, cause it's too redundant; instead we use hashing
        # but here we get only unique files
        listOfFileScriptTags = self.xmldata.xpath('//script[@src]')
        self.listOfIncludedScriptFiles = []
        for tag in listOfFileScriptTags:
            fileName = tag.xpath('@src')[0]
            if fileName not in self.listOfIncludedScriptFiles:
                self.listOfIncludedScriptFiles.append(fileName)

        self.listOfIncludedScriptFilesContent = []
        for filePath in self.listOfIncludedScriptFiles:
            openedFile = commonConnectionUtils.openRelativeScriptObject(self.uri, filePath)
            if openedFile == []:
                continue

            # we turn all text to upper register to speed up analysis in getObjectsWithSuspiciousContent() method
            # in which we can not to use re.I (case insensitive) flag
            self.listOfIncludedScriptFilesContent.append(openedFile[1].upper())

        # NOTE: only JS-comments
        # regexp for C/C++-like comments, also suitable for js-comments
        # ( /\* - begin C-like comment
        # [^\*/]* - everything except closing C-like comment 0+ times
        # \*/ - closing C-like comment
        # | - another part of regExp
        # // - begin of C++-like comment
        # .* - any symbol 0+ times
        # \n?) - until end of line, which can be off
        self.commentsRegExp = re.compile(r'(/\*[^\*/]*\*/|//.*\n?)')

        # get all quoted strings via regExp
        # (?:" - begin on quoted via "-symbol string and passive regExp group
        # [^"\n]* - any symbol 0+ times except closing quote symbol (") and \n
        # ["\n]) - end of quoted via "-symbol string, end-of-line can be also match end of quoted string
        # TODO maybe delete end-of-line from list of ending symbols ^ (also lower)
        # | - same part for string quoted via '-symbol (with escaping '-symbol)
        # (?:\'[^'\n]*[\'\n])
        # this double-part regexp needed in case when
        # one type of quotes appears in quoted string via other type of quotes
        self.quotedStringsRegExp = re.compile(r'(?:"[^"\n]*["\n])|(?:\'[^\'\n]*[\'\n])')
    #
    ###################################################################################################################

    def analyzeFunction(self, callbackFunction, callbackArgument, removeComments = True, removeQuotedStrings = True):
        # in case we would like to analyze one, specific piece of script
        if self.currentlyAnalyzingScriptCode != None:
            if self.currentlyAnalyzingScriptCode > (len(self.listOfScriptTagsText)
                                                        + len(self.listOfIncludedScriptFiles)):
                # TODO log that
                return None

            #print(self.currentlyAnalyzingScriptCode)
            if self.currentlyAnalyzingScriptCode >= len(self.listOfScriptTagsText):
                text = self.listOfIncludedScriptFilesContent[self.currentlyAnalyzingScriptCode - len(self.listOfScriptTagsText)]
            else:
                text = self.listOfScriptTagsText[self.currentlyAnalyzingScriptCode]

            if removeComments:
                # deleting comments
                text = re.sub(self.commentsRegExp, '', text)

            if removeQuotedStrings:
                # remove all quoted strings via regExp
                text = re.sub(self.quotedStringsRegExp, '', text)

            callbackArgument = callbackFunction(text, callbackArgument)
            return callbackArgument
        else:
            # in case we would like to analyze every script in page/file
            #begin = timeit.default_timer()
            for text in self.listOfScriptTagsText:
                if removeComments:
                    # deleting comments
                    text = re.sub(self.commentsRegExp, '', text)

                if removeQuotedStrings:
                    # remove all quoted strings via regExp
                    text = re.sub(self.quotedStringsRegExp, '', text)

                callbackArgument = callbackFunction(text, callbackArgument)

            for scriptContent in self.listOfIncludedScriptFilesContent:
                if removeComments:
                    # deleting comments
                    scriptContent = re.sub(self.commentsRegExp, '', scriptContent)

                if removeQuotedStrings:
                    # remove all quoted strings via regExp
                    scriptContent = re.sub(self.quotedStringsRegExp, '', scriptContent)

                # for future: in case callbackFunction can be list, so we check that before functions using
                # so as in inline js-code
                #if type(callbackFunctions) is list:
                #    callbackArgument = callbackFunctions[1](scriptContent, callbackArgument)
                #else:
                #    callbackArgument = callbackFunctions(scriptContent, callbackArgument)
                callbackArgument = callbackFunction(scriptContent, callbackArgument)

            #end = timeit.default_timer()
            #print("\nElapsed time: " + str(end - begin) + " seconds")

            return callbackArgument
    #
    ###################################################################################################################

    # public functions for outer packages
    # print result of all functions via reflection with default values
    # NOTE: no order in function calls
    def printAll(self, xmldata, pageReady, uri):
        if xmldata is None or pageReady is None:
                print("Insufficient number of parameters")
                return
        self.initialization(xmldata, pageReady, uri)
        # TODO remove in production
        #if (True):
        #    return
        print("\n\njs Analyser ----------------------")
        begin = timeit.default_timer()
        for funcName, funcValue in scriptAnalyzer.__dict__.items():
            if str(funcName).startswith("print") and callable(funcValue):
                try:
                    getattr(self, funcName)()
                except TypeError, error:
                    # TODO write to log "No such function exists"
                    pass
        end = timeit.default_timer()
        print("\nElapsed time: " + str(end - begin) + " seconds")
        print("--------------------------------------")
    #
    ###################################################################################################################

    def getTotalAll(self, xmldata, pageReady, uri):
        if xmldata is None or pageReady is None:
                print("Insufficient number of parameters")
                return
        self.initialization(xmldata, pageReady, uri)
        resultDict = {}
        for funcName, funcValue in scriptAnalyzer.__dict__.items():
            if str(funcName).startswith("getTotal") and callable(funcValue):
                try:
                    resultDict[funcName] = getattr(self, funcName)()
                except TypeError, error:
                    # TODO write to log "No such function exists"
                    pass

        return [resultDict, scriptAnalyzer.__name__]
    #
    ###################################################################################################################

    def parallelViaScriptCodePieces(self, numberOfProcesses):
        totalNumberOfScriptCodes = len(self.listOfScriptTagsText) + len(self.listOfIncludedScriptFiles)
        # adapt function for script nodes - for every script piece of code make own process
        #if numberOfProcesses == 0:
        #    numberOfProcesses = len(self.listOfScriptTagsText) + len(self.listOfIncludedScriptFiles)

        # in case too much process number
        if numberOfProcesses > totalNumberOfScriptCodes:
            numberOfProcesses = totalNumberOfScriptCodes

        numberOfScriptCodePiecesByProcess = totalNumberOfScriptCodes / numberOfProcesses
        scriptCodesNotInProcesses = totalNumberOfScriptCodes % numberOfProcesses
        processQueue = Queue()
        proxyProcessesList = []
        resultDict = {}
        # start process for each function
        for i in xrange(0, numberOfScriptCodePiecesByProcess):
            for j in xrange(0, numberOfProcesses):
                self.currentlyAnalyzingScriptCode = i * numberOfProcesses + j
                proxy = processProxy(None, [self, [], processQueue, 'analyzeAllFunctions'],
                                            commonFunctions.callFunctionByNameQeued)
                proxyProcessesList.append(proxy)
                proxy.start()

            # wait for process joining
            for j in xrange(0, len(proxyProcessesList)):
                proxyProcessesList[j].join()

            # gather all data
            for j in xrange(0, len(proxyProcessesList)):
                functionCallResult = processQueue.get()[1]
                # get hash values of current piece of code, remove them from result and set into dictionary
                hashValues = (functionCallResult['getScriptContentHashing'][0],
                            functionCallResult['getScriptContentHashing'][1])
                del functionCallResult['getScriptContentHashing']
                resultDict[hashValues] = functionCallResult

            del proxyProcessesList[:]

        # if reminder(number of script codes, number of processes) != 0 - not all functions ran in separated processes
        # run other script codes in one, current, process
        if scriptCodesNotInProcesses != 0:
            for i in xrange(0, scriptCodesNotInProcesses):
                try:
                    self.currentlyAnalyzingScriptCode = totalNumberOfScriptCodes - 1 - i
                    functionCallResult = self.analyzeAllFunctions(oneProcess=True)
                    # get hash values of current piece of code, remove them from result and set into dictionary
                    hashValues = (functionCallResult['getScriptContentHashing'][0],
                                functionCallResult['getScriptContentHashing'][1])
                    del functionCallResult['getScriptContentHashing']
                    resultDict[hashValues] = functionCallResult
                except TypeError, error:
                    # TODO write to log "No such function exists"
                    pass

        return resultDict

    # analyze all list of analyze functions in one process
    def analyzeAllFunctions(self, oneProcess = False):
        # in case we analyze all functions of one script code piece in one separate process
        # designed to fulfill "parallelViaScriptCodePieces" method
        if oneProcess:
            resultDict = {}
            for funcName in self.listOfAnalyzeFunctions:
                try:
                    functionCallResult = getattr(self, funcName)()
                    # if in result dict value = 0 - do not insert it
                    if not ((type(functionCallResult) is int and functionCallResult == 0) or (type(
                            functionCallResult) is float and functionCallResult == 0.0)):
                        resultDict[funcName] = functionCallResult
                except TypeError, error:
                    # TODO write to log "No such function exists"
                    pass
        # in case we analyze all script from whole script in one process
        else:
            resultDict = {}
            resultInnerDict = {}
            for i in xrange(0, len(self.listOfScriptTagsText) + len(self.listOfIncludedScriptFiles)):
                self.currentlyAnalyzingScriptCode = i
                for funcName in self.listOfAnalyzeFunctions:
                    try:
                        functionCallResult = getattr(self, funcName)()
                        # if in result dict value = 0 - do not insert it
                        if not ((type(functionCallResult) is int and functionCallResult == 0) or (type(
                                functionCallResult) is float and functionCallResult == 0.0)):
                            resultInnerDict[funcName] = functionCallResult
                    except TypeError, error:
                        # TODO write to log "No such function exists"
                        pass

                hashValues = (resultInnerDict['getScriptContentHashing'][0],
                                resultInnerDict['getScriptContentHashing'][1])
                del resultInnerDict['getScriptContentHashing']
                resultDict[hashValues] = deepcopy(resultInnerDict)
                for key in resultInnerDict.keys():
                    del resultInnerDict[key]

        return resultDict

    def getAllAnalyzeReport(self, xmldata, pageReady, uri, numberOfProcesses = 1):
        if xmldata is None or pageReady is None:
                print("Insufficient number of parameters")
                return
        self.initialization(xmldata, pageReady, uri)

        # in case too less processes
        if numberOfProcesses <= 0:
            numberOfProcesses = 1
        # in case too much process number
        elif numberOfProcesses > len(self.listOfAnalyzeFunctions):
            numberOfProcesses = len(self.listOfAnalyzeFunctions)

        resultDict = {}
        # parallel by script codes - in limiting case one process per script piece
        if numberOfProcesses > 1:
            resultDict = self.parallelViaScriptCodePieces(numberOfProcesses)
        else:
            resultDict = self.analyzeAllFunctions()

        return [resultDict, scriptAnalyzer.__name__]
    #
    ###################################################################################################################

    # TODO list
    # - the number of pieces of code resembling a deobfuscation routine
    # - AST structure comparing
    # - uri in more common class; or get uri & open file/page by js-Analyzer itself

    # TODO ask
    # is it possible to write redirection from folder where scripts lie to somewhere else?
    # I.e user loads page (in browser; then render it) & has access to scripts,
    # other way, analyzer open path-where-script-lie and sees nothing

    # TODO optimization (right now from 168 sec. to 5.5 sec.; from 1692 lines to 1166 lines)
    # - callback or anonymous functions in for-each loops calls in printXXXX methods
    # - merge regexps