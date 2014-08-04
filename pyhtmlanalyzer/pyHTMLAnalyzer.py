from multiprocessing import Queue
import re
import timeit
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

    def __init__(self, configFileName):
        configList = self.getConfigList(configFileName)
        self.htmlAnalyzerModule = htmlAnalyzer(configList[0])
        self.scriptAnalyzerModule = scriptAnalyzer(configList[1])
        self.urlAnalyzerModule = urlAnalyzer(configList[2])

    # get config list for various analyzer modules
    def getConfigList(self, configFileName):
        configFile = open(configFileName, 'r')
        listOfHTMLFeatures = ["html.elements.with.small.area",
                              "html.non.dulpicated.elemets",
                              "html.void.elements",
                              "html.included.urls.elements",
                              "html.under.head.elements",
                              "html.out.of.root.elements",
                              "html.block.level.elements",
                              "html.non.block.elements",
                              "html.no.block.content.inline.elements",
                              "html.all.tag.names"]
        listOfScriptFeatures = ["script.set.timeout.functions",
                                "script.keywords",
                                "script.built.in.functions",
                                "script.suspicious.tags",
                                "script.events",
                                "script.event.functions",
                                "script.string.modification.functions",
                                "script.deobfuscation.functions",
                                "script.DOM.modifying.methods",
                                "script.fingerprinting.functions"]
        listOfURLFeatures = ["url.suspicious.file.names",
                             "url.suspicious.patterns"]
        htmlConfigDict = {}
        scriptConfigDict = {}
        urlConfigDict = {}
        regExp = re.compile(r'[^\n\s=,]+')
        for line in configFile:
            # comments
            if line.startswith("#"):
                continue
            parseResult = re.findall(regExp, line)
            if parseResult == []:
                continue

            # html features
            if parseResult[0] in listOfHTMLFeatures:
                htmlConfigDict[parseResult[0]] = parseResult
                htmlConfigDict[parseResult[0]].pop(0)

            # script features
            if parseResult[0] in listOfScriptFeatures:
                scriptConfigDict[parseResult[0]] = parseResult
                scriptConfigDict[parseResult[0]].pop(0)

            # url features
            if parseResult[0] in listOfURLFeatures:
                urlConfigDict[parseResult[0]] = parseResult
                urlConfigDict[parseResult[0]].pop(0)

        return [htmlConfigDict, scriptConfigDict, urlConfigDict]

    # print-function group
    def printAnalyzedAbstractObjectFeatures(self, xmldata, pageReady, htmlAnalysis, scriptAnalysis, urlAnalysis, uri):
        if xmldata is None or pageReady is None:
            print("Insufficient number of parameters")
            return

        htmlAnalyzerProcess = None
        jsAnalyzerProcess = None
        urlAnalyzerProcess = None
        if htmlAnalysis:
            #self.htmlAnalyzerModule.printAll(xmldata, pageReady, uri)
            htmlAnalyzerProcess = processProxy(self.htmlAnalyzerModule, [xmldata, pageReady, uri], 'printAll')
            htmlAnalyzerProcess.start()

        if scriptAnalysis:
            #self.scriptAnalyzerModule.printAll(xmldata, pageReady, uri)
            jsAnalyzerProcess = processProxy(self.scriptAnalyzerModule, [xmldata, pageReady, uri], 'printAll')
            jsAnalyzerProcess.start()

        if urlAnalysis:
            #self.urlAnalyzerModule.printAll(uri)
            urlAnalyzerProcess = processProxy(self.urlAnalyzerModule, [uri], 'printAll')
            urlAnalyzerProcess.start()

        if htmlAnalyzerProcess is not None:
            htmlAnalyzerProcess.join()
        if jsAnalyzerProcess is not None:
            jsAnalyzerProcess.join()
        if urlAnalyzerProcess is not None:
            urlAnalyzerProcess.join()

    def printAnalyzedHTMLFileFeatures(self, filePath, htmlAnalysis = True, scriptAnalysis = True, urlAnalysis = True):
        openedFile = commonConnectionUtils.openFile(filePath)
        if openedFile == []:
            print("Cannot analyze file")
            return

        xmldata = openedFile[0]
        pageReady = openedFile[1]
        self.printAnalyzedAbstractObjectFeatures(xmldata, pageReady, htmlAnalysis, scriptAnalysis, urlAnalysis, filePath)

    def printAnalyzedPageFeatures(self, url, htmlAnalysis = True, scriptAnalysis = True, urlAnalysis = True):
        openedPage = commonConnectionUtils.openPage(url)
        if openedPage == []:
            print("Cannot analyze page")
            return

        xmldata = openedPage[0]
        pageReady = openedPage[1]
        begin = timeit.default_timer()
        self.printAnalyzedAbstractObjectFeatures(xmldata, pageReady, htmlAnalysis, scriptAnalysis, urlAnalysis, url)
        end = timeit.default_timer()
        print("\nprintAnalyzedPageFeatures elapsed time: " + str(end - begin) + " seconds")
    #
    ###################################################################################################################

    # getTotal-functions group
    def getNumberOfAnalyzedAbstractObjectFeaturesByFunction(self, xmldata, pageReady, htmlAnalysis, scriptAnalysis, urlAnalysis, uri, functionName = 'getTotalAll'):
        if xmldata is None or pageReady is None:
            print("Insufficient number of parameters")
            return
        resultDict = {}
        processQueue = Queue()
        processesNumber = 0

        htmlAnalyzerProcess = None
        jsAnalyzerProcess = None
        urlAnalyzerProcess = None
        if htmlAnalysis:
            htmlAnalyzerProcess = processProxy(self.htmlAnalyzerModule, [xmldata, pageReady, uri, processQueue], functionName)
            htmlAnalyzerProcess.start()
            processesNumber += 1

        if scriptAnalysis:
            jsAnalyzerProcess = processProxy(self.scriptAnalyzerModule, [xmldata, pageReady, uri, processQueue], functionName)
            jsAnalyzerProcess.start()
            processesNumber += 1

        if urlAnalysis:
            urlAnalyzerProcess = processProxy(self.urlAnalyzerModule, [uri, processQueue], functionName)
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
            resultDict[resultList[1]] = resultList[0]
        return resultDict

    def getNumberOfFileFeaturesWrapper(self, filePath, queue, functionName = 'getAllAnalyzeReport', htmlAnalysis = True, scriptAnalysis = True, urlAnalysis = True):
        queue.put(self.getNumberOfAnalyzedHTMLFileFeaturesByFunction(filePath, functionName, htmlAnalysis, scriptAnalysis, urlAnalysis))

    def getNumberOfAnalyzedHTMLFileFeaturesByFunction(self, filePath, functionName = 'getAllAnalyzeReport', htmlAnalysis = True, scriptAnalysis = True, urlAnalysis = True):
        openedFile = commonConnectionUtils.openFile(filePath)
        if openedFile == []:
            print("Cannot analyze file")
            return

        xmldata = openedFile[0]
        pageReady = openedFile[1]
        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(xmldata, pageReady, htmlAnalysis, scriptAnalysis, urlAnalysis, filePath, functionName)

    def getNumberOfPageFeaturesWrapper(self, url, queue, functionName = 'getAllAnalyzeReport', htmlAnalysis = True, scriptAnalysis = True, urlAnalysis = True):
        queue.put(self.getNumberOfAnalyzedPageFeaturesByFunction(url, functionName, htmlAnalysis, scriptAnalysis, urlAnalysis))

    def getNumberOfAnalyzedPageFeaturesByFunction(self, url, functionName = 'getAllAnalyzeReport', htmlAnalysis = True, scriptAnalysis = True, urlAnalysis = True):
        openedPage = commonConnectionUtils.openPage(url)
        if openedPage == []:
            print("Cannot analyze page")
            return

        xmldata = openedPage[0]
        pageReady = openedPage[1]
        return self.getNumberOfAnalyzedAbstractObjectFeaturesByFunction(xmldata, pageReady, htmlAnalysis, scriptAnalysis, urlAnalysis, url, functionName)
    #
    ###################################################################################################################

    def getTotalNumberOfAnalyzedObjectsFeatures(self, listOfObjects, isPages = True):
        if len(listOfObjects) == 0:
            return None

        functionName = 'getNumberOfPageFeaturesWrapper' \
            if isPages else 'getNumberOfFileFeaturesWrapper'
        processQueue = Queue()
        proxyProcessesList = []
        resultDict = {}
        # start process for each page
        for page in listOfObjects:
            proxy = processProxy(self, [page, processQueue], functionName)
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