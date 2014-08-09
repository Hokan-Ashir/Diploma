from multiprocessing import Queue
import timeit
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.processProxy import processProxy
from pyhtmlanalyzer.full.url.commonURL.commonURLFunctions import commonURLFunctions
from pyhtmlanalyzer.full.url.dns.dnsFunctions import dnsFunctions
from pyhtmlanalyzer.full.url.geoip.geoIPFunctions import geoIPFunctions
from pyhtmlanalyzer.full.url.urlvoid.urlVoidFunctions import urlVoidFunctions
from pyhtmlanalyzer.full.url.whoisPackage.whoisFunctions import whoisFunctions

__author__ = 'hokan'


class urlAnalyzer(commonURLFunctions, dnsFunctions, geoIPFunctions, whoisFunctions, urlVoidFunctions):
    configDict = None
    isCommonURLModuleActive = True
    isDNSModuleActive = True
    isGeoIPModuleActive = True
    isWhoIsModuleActive = True
    isURLVoidModuleActive = True
    listOfAnalyzeFunctions = []

    # constructor
    def __init__(self, configDict, uri=None):
        commonURLFunctions.__init__(self, configDict, uri)
        dnsFunctions.__init__(self, uri)
        geoIPFunctions.__init__(self, uri)
        whoisFunctions.__init__(self, uri)
        urlVoidFunctions.__init__(self, uri)
        if configDict is None:
            print("\nInvalid parameters")
            return

        self.configDict = configDict
        self.listOfAnalyzeFunctions = commonFunctions.getAnalyzeFunctionList('analyzeFunctions', 'url.module')
    #
    ###################################################################################################################

    def setActiveModules(self, commonURLModule, dnsModule, geoIPModule, whoisModule, urlVoidModule):
        self.isCommonURLModuleActive = commonURLModule
        self.isDNSModuleActive = dnsModule
        self.isGeoIPModuleActive = geoIPModule
        self.isWhoIsModuleActive = whoisModule
        self.isURLVoidModuleActive = urlVoidModule
    #
    ###################################################################################################################

    def setURI(self, uri):
        self.uri = uri
        if self.isURLVoidModuleActive:
            self.retrieveURLData()
        if self.isDNSModuleActive:
            self.retrieveDNShostInfo()
        if self.isWhoIsModuleActive:
            self.retrieveWHOIShostInfo()
        if self.isGeoIPModuleActive:
            self.retrieveGeoIPhostInfo()
    #
    ###################################################################################################################

    # public functions for outer packages
    # print result of all functions via reflection with default values
    # NOTE: no order in function calls
    def printAll(self, uri):
        if uri is None:
            print("Insufficient number of parameters")
            return
        # TODO (un)comment
        self.setActiveModules(True, True, True, True, False)
        self.setURI(uri)
        #list_of_domains = ['diagsv3.com', 'google.com', 'abc.com', 'xxxtoolbar.com']
        #printURLVoidScanResults(list_of_domains)
        #printURLVoidScanResults(list_of_domains, True)
        #printURLVoidMaliciousDomains(list_of_domains)
        #self.printIsHostMalicious()
        # TODO remove in production
        #if (True):
        #    return
        print("\n\nurl Analyser ----------------------")
        begin = timeit.default_timer()
        for className in urlAnalyzer.__bases__:
            if className.__name__ == commonURLFunctions.__name__ and not self.isCommonURLModuleActive:
                continue
            if className.__name__ == dnsFunctions.__name__ and not self.isDNSModuleActive:
                continue
            if className.__name__ == geoIPFunctions.__name__ and not self.isGeoIPModuleActive:
                continue
            if className.__name__ == whoisFunctions.__name__ and not self.isWhoIsModuleActive:
                continue
            if className.__name__ == urlVoidFunctions.__name__ and not self.isURLVoidModuleActive:
                continue
            for funcName, funcValue in className.__dict__.items():
                if str(funcName).startswith("print") and callable(funcValue):
                    try:
                        getattr(self, funcName)()
                    except TypeError:
                        # TODO write to log "No such function exists"
                        pass
        end = timeit.default_timer()
        print("\nElapsed time: " + str(end - begin) + " seconds")
        print("---------------------------------------")
    #
    ###################################################################################################################

    def getTotalAll(self, uri):
        if uri is None:
            print("Insufficient number of parameters")
            return
        self.uri = uri
        resultDict = {}
        for className in urlAnalyzer.__bases__:
            if className.__name__ == commonURLFunctions.__name__ and not self.isCommonURLModuleActive:
                continue
            if className.__name__ == dnsFunctions.__name__ and not self.isDNSModuleActive:
                continue
            if className.__name__ == geoIPFunctions.__name__ and not self.isGeoIPModuleActive:
                continue
            if className.__name__ == whoisFunctions.__name__ and not self.isWhoIsModuleActive:
                continue
            if className.__name__ == urlVoidFunctions.__name__ and not self.isURLVoidModuleActive:
                continue
            for funcName, funcValue in className.__dict__.items():
                if str(funcName).startswith("getTotal") and callable(funcValue):
                    try:
                        resultDict[funcName] = getattr(self, funcName)()
                    except TypeError:
                        # TODO write to log "No such function exists"
                        pass

        return [resultDict, urlAnalyzer.__name__]
    #
    ###################################################################################################################

    def getAllAnalyzeReport(self, uri, numberOfProcesses = 1):
        if uri is None:
            print("Insufficient number of parameters")
            return
        self.uri = uri

        # in case too much process number
        if numberOfProcesses > len(self.listOfAnalyzeFunctions):
            numberOfProcesses = len(self.listOfAnalyzeFunctions)

        resultDict = {}
        if numberOfProcesses > 1:
            numberOfFunctionsByProcess = len(self.listOfAnalyzeFunctions) / numberOfProcesses
            functionsNotInProcesses = len(self.listOfAnalyzeFunctions) % numberOfProcesses
            processQueue = Queue()
            proxyProcessesList = []
            resultDict = {}
            # start process for each function
            for i in xrange(0, numberOfFunctionsByProcess):
                for j in xrange(0, numberOfProcesses):
                    proxy = processProxy(None, [self, [], processQueue, self.listOfAnalyzeFunctions[i * numberOfProcesses + j]],
                                        commonFunctions.callFunctionByNameQeued)
                    proxyProcessesList.append(proxy)
                    proxy.start()

                # wait for process joining
                for j in xrange(0, len(proxyProcessesList)):
                    proxyProcessesList[j].join()

                # gather all data
                for j in xrange(0, len(proxyProcessesList)):
                    functionCallResult = processQueue.get()
                    # if in result dict value = 0 - do not insert it
                    if not ((type(functionCallResult[1]) is int and functionCallResult[1] == 0) or (type(
                            functionCallResult[1]) is float and functionCallResult[1] == 0.0)):
                        resultDict[functionCallResult[0]] = functionCallResult[1]

                del proxyProcessesList[:]

            # if reminder(number of functions, number of processes) != 0 - not all functions ran in separated processes
            # run other functions in one, current, process
            if functionsNotInProcesses != 0:
                for i in xrange(0, functionsNotInProcesses):
                    try:
                        functionCallResult = getattr(self, self.listOfAnalyzeFunctions[-i])()
                        # if in result dict value = 0 - do not insert it
                        if not ((type(functionCallResult) is int and functionCallResult == 0) or (type(
                                functionCallResult) is float and functionCallResult == 0.0)):
                            resultDict[self.listOfAnalyzeFunctions[-i]] = functionCallResult
                    except TypeError:
                        # TODO write to log "No such function exists"
                        pass

        else:
            for funcName in self.listOfAnalyzeFunctions:
                try:
                    functionCallResult = getattr(self, funcName)()
                    # if in result dict value = 0 - do not insert it
                    if not ((type(functionCallResult) is int and functionCallResult == 0) or (type(
                            functionCallResult) is float and functionCallResult == 0.0)):
                        resultDict[funcName] = functionCallResult
                except TypeError:
                    # TODO write to log "No such function exists"
                    pass

        return [resultDict, urlAnalyzer.__name__]
    #
    ###################################################################################################################

    # optimized from 19 to 1.5 seconds

        # TODO list
        # syntactical features
        # the presence of a suspicious domain name (simply must taken from ours db or from urlVoid request)
        #
        # geoip-based
        # netspeed (see no point in it)