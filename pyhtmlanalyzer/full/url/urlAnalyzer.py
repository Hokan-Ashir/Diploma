import logging
from multiprocessing import Queue
import timeit
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.processProxy import processProxy
from pyhtmlanalyzer.full.url.commonURL.commonURLFunctions import commonURLFunctions
from pyhtmlanalyzer.full.url.dns.dnsFunctions import dnsFunctions
from pyhtmlanalyzer.full.url.geoip.geoIPFunctions import geoIPFunctions
from pyhtmlanalyzer.full.url.urlvoid.urlVoidFunctions import urlVoidFunctions
from pyhtmlanalyzer.full.url.whoisPackage.whoisFunctions import whoisFunctions

__author__ = 'hokan'


class urlAnalyzer(commonURLFunctions, dnsFunctions, geoIPFunctions, whoisFunctions, urlVoidFunctions):
    __name__ = 'urlAnalyzer'

    __configDict = None
    __isCommonURLModuleActive = True
    __isDNSModuleActive = True
    __isGeoIPModuleActive = True
    __isWhoIsModuleActive = True
    __isURLVoidModuleActive = True
    __listOfAnalyzeFunctions = []

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

        self.__configDict = configDict
        result = commonFunctions.getModuleContent(configNames.configFileName, r'[^\n\s=,]+\s*:\s*[^\n\s=,]+', 'Extractors functions',
                                                  self.__class__.__name__)
        self.__listOfAnalyzeFunctions = [item.split(':')[0].replace(' ', '') for item in result]
    #
    ###################################################################################################################

    def setActiveModules(self, commonURLModule, dnsModule, geoIPModule, whoisModule, urlVoidModule):
        self.__isCommonURLModuleActive = commonURLModule
        self.__isDNSModuleActive = dnsModule
        self.__isGeoIPModuleActive = geoIPModule
        self.__isWhoIsModuleActive = whoisModule
        self.__isURLVoidModuleActive = urlVoidModule
    #
    ###################################################################################################################

    def setURI(self, uri):
        self._uri = uri
        if self.__isURLVoidModuleActive:
            self.retrieveURLData()
        if self.__isDNSModuleActive:
            self.retrieveDNShostInfo()
        if self.__isWhoIsModuleActive:
            self.retrieveWHOIShostInfo()
        if self.__isGeoIPModuleActive:
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
            if className.__name__ == commonURLFunctions.__name__ and not self.__isCommonURLModuleActive:
                continue
            if className.__name__ == dnsFunctions.__name__ and not self.__isDNSModuleActive:
                continue
            if className.__name__ == geoIPFunctions.__name__ and not self.__isGeoIPModuleActive:
                continue
            if className.__name__ == whoisFunctions.__name__ and not self.__isWhoIsModuleActive:
                continue
            if className.__name__ == urlVoidFunctions.__name__ and not self.__isURLVoidModuleActive:
                continue
            for funcName, funcValue in className.__dict__.items():
                if str(funcName).startswith("print") and callable(funcValue):
                    try:
                        getattr(self, funcName)()
                    except Exception, error:
                        logger = logging.getLogger(self.__class__.__name__)
                        logger.exception(error)
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
        self._uri = uri
        resultDict = {}
        for className in urlAnalyzer.__bases__:
            if className.__name__ == commonURLFunctions.__name__ and not self.__isCommonURLModuleActive:
                continue
            if className.__name__ == dnsFunctions.__name__ and not self.__isDNSModuleActive:
                continue
            if className.__name__ == geoIPFunctions.__name__ and not self.__isGeoIPModuleActive:
                continue
            if className.__name__ == whoisFunctions.__name__ and not self.__isWhoIsModuleActive:
                continue
            if className.__name__ == urlVoidFunctions.__name__ and not self.__isURLVoidModuleActive:
                continue
            for funcName, funcValue in className.__dict__.items():
                if str(funcName).startswith("getTotal") and callable(funcValue):
                    try:
                        resultDict[funcName] = getattr(self, funcName)()
                    except Exception, error:
                        logger = logging.getLogger(self.__class__.__name__)
                        logger.exception(error)
                        pass

        return [resultDict, urlAnalyzer.__name__]
    #
    ###################################################################################################################

    def getAllAnalyzeReport(self, **kwargs):
        try:
            kwargs['uri']
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            print("Insufficient number of parameters")
            return

        if kwargs['uri'] is None:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Error in input parameters:\n uri:\t%s' % (kwargs['uri']))
            print("Insufficient number of parameters")
            return
        self._uri = kwargs['uri']
        self.setURI(self._uri)

        numberOfProcesses = 1
        try:
            numberOfProcesses = kwargs['numberOfProcesses']
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            pass

        # in case too less processes
        if numberOfProcesses <= 0:
            numberOfProcesses = 1
        # in case too much process number
        elif numberOfProcesses > len(self.__listOfAnalyzeFunctions):
            numberOfProcesses = len(self.__listOfAnalyzeFunctions)

        resultDict = {}
        if numberOfProcesses > 1:
            numberOfFunctionsByProcess = len(self.__listOfAnalyzeFunctions) / numberOfProcesses
            functionsNotInProcesses = len(self.__listOfAnalyzeFunctions) % numberOfProcesses
            processQueue = Queue()
            proxyProcessesList = []
            resultDict = {}
            # start process for each function
            for i in xrange(0, numberOfFunctionsByProcess):
                for j in xrange(0, numberOfProcesses):
                    proxy = processProxy(None, [self, {},
                                                processQueue,
                                                self.__listOfAnalyzeFunctions[i * numberOfProcesses + j]],
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
                    #if not ((type(functionCallResult[1]) is int and functionCallResult[1] == 0) or (type(
                    #        functionCallResult[1]) is float and functionCallResult[1] == 0.0)):
                    resultDict[functionCallResult[0]] = functionCallResult[1]

                del proxyProcessesList[:]

            # if reminder(number of functions, number of processes) != 0 - not all functions ran in separated processes
            # run other functions in one, current, process
            if functionsNotInProcesses != 0:
                for i in xrange(0, functionsNotInProcesses):
                    try:
                        functionCallResult = getattr(self, self.__listOfAnalyzeFunctions[-1 - i])()
                        # if in result dict value = 0 - do not insert it
                        #if not ((type(functionCallResult) is int and functionCallResult == 0) or (type(
                        #        functionCallResult) is float and functionCallResult == 0.0)):
                        resultDict[self.__listOfAnalyzeFunctions[-1 - i]] = functionCallResult
                    except Exception, error:
                        logger = logging.getLogger(self.__class__.__name__)
                        logger.exception(error)
                        pass

        else:
            for funcName in self.__listOfAnalyzeFunctions:
                try:
                    functionCallResult = getattr(self, funcName)()
                    # if in result dict value = 0 - do not insert it
                    #if not ((type(functionCallResult) is int and functionCallResult == 0) or (type(
                    #        functionCallResult) is float and functionCallResult == 0.0)):
                    resultDict[funcName] = functionCallResult
                except Exception, error:
                    logger = logging.getLogger(self.__class__.__name__)
                    logger.exception(error)
                    pass

        return [[resultDict], urlAnalyzer.__name__]
    #
    ###################################################################################################################

    # optimized from 19 to 1.5 seconds

        # TODO list
        # syntactical features
        # the presence of a suspicious domain name (simply must taken from ours db or from urlVoid request)
        #
        # geoip-based
        # netspeed (see no point in it)