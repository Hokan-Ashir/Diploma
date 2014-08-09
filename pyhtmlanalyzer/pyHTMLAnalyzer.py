from multiprocessing import Queue
import re
from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.commonFunctions.processProxy import processProxy
from pyhtmlanalyzer.full.html.htmlAnalyzer import htmlAnalyzer
from pyhtmlanalyzer.full.script.scriptAnalyzer import scriptAnalyzer
from pyhtmlanalyzer.full.url.urlAnalyzer import urlAnalyzer

__author__ = 'hokan'

class pyHTMLAnalyzer:
    htmlAnalyzerModule = None
    scriptAnalyzerModule = None
    urlAnalyzerModule = None

    isHTMLModuleActive = True
    isScriptMiduleActive = True
    isURLModuleActive = True

    def __init__(self, configFileName):
        configList = self.getConfigList(configFileName)
        self.htmlAnalyzerModule = htmlAnalyzer(configList[0])
        self.scriptAnalyzerModule = scriptAnalyzer(configList[1])
        self.urlAnalyzerModule = urlAnalyzer(configList[2])

    # returns active module list, order - html module, script module, url module
    def getActiveModuleList(self):
        return [self.isHTMLModuleActive, self.isScriptMiduleActive, self.isURLModuleActive]

    def setIsHTMLModuleActive(self, isActive):
        self.isHTMLModuleActive = isActive

    def setIsScriptModuleActive(self, isActive):
        self.isScriptMiduleActive = isActive

    def setIsURLModuleActive(self, isActive):
        self.isURLModuleActive = isActive

    # get config list for various analyzer modules
    def getConfigList(self, configFileName):
        configFile = open(configFileName, 'r')
        htmlConfigDict = {}
        scriptConfigDict = {}
        urlConfigDict = {}
        currentModule = ""
        regExp = re.compile(r'[^\n\s=,]+')
        for line in configFile:
            # comments
            if line.startswith("#"):
                continue

            # decide which functions belongs to which module
            if line == '[html analyzer features]\n':
                currentModule = 'html'
                continue
            elif line == '[script analyzer features]\n':
                currentModule = 'script'
                continue
            elif line == '[url.analyzer.features]\n':
                currentModule = "url"
                continue

            parseResult = re.findall(regExp, line)
            if parseResult == []:
                continue

            # html features
            if currentModule == 'html':
                htmlConfigDict[parseResult[0]] = parseResult[1:]

            # script features
            elif currentModule == 'script':
                scriptConfigDict[parseResult[0]] = parseResult[1:]

            # url features
            elif currentModule == 'url':
                urlConfigDict[parseResult[0]] = parseResult[1:]

        configFile.close()

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
        processesNumber = 0

        htmlAnalyzerProcess = None
        jsAnalyzerProcess = None
        urlAnalyzerProcess = None
        if self.isHTMLModuleActive:
            htmlAnalyzerProcess = processProxy(self, [self.htmlAnalyzerModule, [xmldata, pageReady, uri],
                                                      processQueue, functionName], 'callFunctionByName')
            htmlAnalyzerProcess.start()
            processesNumber += 1

        if self.isURLModuleActive:
            jsAnalyzerProcess = processProxy(self, [self.scriptAnalyzerModule, [xmldata, pageReady, uri],
                                                    processQueue, functionName], 'callFunctionByName')
            jsAnalyzerProcess.start()
            processesNumber += 1

        if self.isScriptMiduleActive:
            urlAnalyzerProcess = processProxy(self, [self.urlAnalyzerModule, [uri], processQueue, functionName], 'callFunctionByName')
            urlAnalyzerProcess.start()
            processesNumber += 1

        if htmlAnalyzerProcess is not None:
            htmlAnalyzerProcess.join()
        if jsAnalyzerProcess is not None:
            jsAnalyzerProcess.join()
        if urlAnalyzerProcess is not None:
            urlAnalyzerProcess.join()

        for i in xrange(0, processesNumber):
            resultList = processQueue.get()
            # if function returns nothing (like print function, for example)
            if resultList is None:
                resultDict = resultList
            else:
                resultDict[resultList[1]] = resultList[0]

        return resultDict

    # to run specific function in specific module, just
    def getNumberOfAnalyzedHTMLFileFeaturesByFunction(self, filePath, functionName = 'getAllAnalyzeReport'):
        openedFile = commonConnectionUtils.openFile(filePath)
        if openedFile == []:
            print("Cannot analyze file")
            return

        xmldata = openedFile[0]
        pageReady = openedFile[1]
        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(xmldata, pageReady, filePath, functionName)

    def getNumberOfAnalyzedPageFeaturesByFunction(self, url, functionName = 'getAllAnalyzeReport'):
        openedPage = commonConnectionUtils.openPage(url)
        if openedPage == []:
            print("Cannot analyze page")
            return

        xmldata = openedPage[0]
        pageReady = openedPage[1]
        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(xmldata, pageReady, url, functionName)
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
            proxy = processProxy(self, [self, [object], processQueue, functionName], 'callFunctionByName')
            proxyProcessesList.append(proxy)
            proxy.start()

        # wait for process joining
        for i in xrange(0, len(proxyProcessesList)):
            proxyProcessesList[i].join()

        # gather all data
        for i in xrange(0, len(proxyProcessesList)):
            resultDict[listOfObjects[i]] = processQueue.get()

        return resultDict

    def getTotalNumberOfAnalyzedPagesFeatures(self, listOfPages):
        return self.getTotalNumberOfAnalyzedObjectsFeatures(listOfPages)

    def getTotalNumberOfAnalyzedFilesFeatures(self, listOfFiles):
        return self.getTotalNumberOfAnalyzedObjectsFeatures(listOfFiles, False)
    #
    ###################################################################################################################

    def callFunctionByName(self, classInstance, arguments, queue, methodName):
        result = None
        if len(classInstance.__class__.__bases__) != 0:
            for className in classInstance.__class__.__bases__:
                for funcName, funcValue in className.__dict__.items():
                    if str(funcName) == methodName and callable(funcValue):
                        try:
                            result = getattr(classInstance, funcName)(*arguments)
                        except TypeError:
                            pass

                        return queue.put(result)

        for funcName, funcValue in classInstance.__class__.__dict__.items():
                if str(funcName) == methodName and callable(funcValue):
                    try:
                        result = getattr(classInstance, funcName)(*arguments)
                    except TypeError:
                        pass

                    return queue.put(result)

        return queue.put(result)