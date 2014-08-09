import timeit
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
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
                        pass

        return [resultDict, urlAnalyzer.__name__]
    #
    ###################################################################################################################

    def getAllAnalyzeReport(self, uri):
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
                if funcName in self.listOfAnalyzeFunctions and callable(funcValue):
                    try:
                        functionCallResult = getattr(self, funcName)()
                        # if in result dict value = 0 - do not insert it
                        if not ((type(functionCallResult) is int and functionCallResult == 0) or (type(
                                functionCallResult) is float and functionCallResult == 0.0)):
                            resultDict[funcName] = functionCallResult
                    except TypeError:
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