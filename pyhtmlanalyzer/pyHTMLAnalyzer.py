from collections import defaultdict
import logging
from multiprocessing import Queue
from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.commonFunctions.processProxy import processProxy
from pyhtmlanalyzer.full.html.htmlAnalyzer import htmlAnalyzer
from pyhtmlanalyzer.full.script.scriptAnalyzer import scriptAnalyzer
from pyhtmlanalyzer.full.url.urlAnalyzer import urlAnalyzer

__author__ = 'hokan'

class pyHTMLAnalyzer:
    __modulesRegister = None
    __activeModulesDictionary = defaultdict(bool)

    def __init__(self, configFileName):
        self.__modulesRegister = modulesRegister()
        configList = self.getConfigList(configFileName)
        self.setModule(htmlAnalyzer(configList[0]))
        self.setModule(scriptAnalyzer(configList[1]))
        self.setModule(urlAnalyzer(configList[2]))

    # module section
    def getModules(self):
        return self.__modulesRegister.getClassInstanceDictionary()

    def getModuleByName(self, moduleName):
        return self.__modulesRegister.getClassInstance(moduleName)

    def setModule(self, moduleInstance, moduleInstanceName = None):
        self.__modulesRegister.registerClassInstance(moduleInstance, moduleInstanceName)
        if moduleInstanceName is not None:
            self.setIsActiveModule(moduleInstanceName)
        else:
            self.setIsActiveModule(moduleInstance.__name__)

    def removeModule(self, moduleName):
        self.__modulesRegister.unregisterClassInstance(moduleName)
        del self.__activeModulesDictionary[moduleName]

    # isActive section
    def setIsActiveModule(self, moduleName, isActive = True):
        self.__activeModulesDictionary[moduleName] = isActive

    def getIsActiveModule(self, moduleName):
        return self.__activeModulesDictionary[moduleName]

    # get config list for various analyzer modules
    def getConfigList(self, configFileName):
        result = commonFunctions.getSectionContent(configFileName, r'[^\n\s=,]+',
                                                    'Extractors features')

        # html features
        htmlConfigDict = {}
        try:
            for item in result['htmlAnalyzer']:
                htmlConfigDict[item[0]] = item[1:]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            pass

        # script features
        scriptConfigDict = {}
        try:
            for item in result['scriptAnalyzer']:
                scriptConfigDict[item[0]] = item[1:]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            pass

        # uri features
        urlConfigDict = {}
        try:
            for item in result['urlAnalyzer']:
                urlConfigDict[item[0]] = item[1:]
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            pass

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
        proxyProcessesList = []

        # start process for each module
        for moduleName, module in self.getModules().items():
            if self.getIsActiveModule(moduleName):
                # {'numberOfProcesses' : 1}
                process = processProxy(None, [module, {'xmldata' : xmldata, 'pageReady' : pageReady, 'uri' : uri},
                                              processQueue, functionName], commonFunctions.callFunctionByNameQeued)
                proxyProcessesList.append(process)
                process.start()

        # wait for process joining
        for process in proxyProcessesList:
            process.join()

        # gather all data
        for i in xrange(0, len(proxyProcessesList)):
            resultList = processQueue.get()[1]
            # if function returns nothing (like print function, for example)
            if resultList is None or not resultList:
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
            proxy = processProxy(None, [self, [object], processQueue, functionName], commonFunctions
            .callFunctionByNameQeued)
            proxyProcessesList.append(proxy)
            proxy.start()

        # wait for process joining
        for process in proxyProcessesList:
            process.join()

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