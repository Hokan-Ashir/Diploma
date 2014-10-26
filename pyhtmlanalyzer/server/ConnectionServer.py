import logging
from multiprocessing import Manager

from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.commonFunctions.multiprocessing.processProxy import processProxy
from pyhtmlanalyzer.databaseUtils.databaseConnector import databaseConnector


__author__ = 'hokan'

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

class URLReceiver(LineReceiver):
    __analyzer = None

    def __init__(self, analyzer, currentlyAnalyzingURLs):
        self.__analyzer = analyzer
        self.currentlyAnalyzingURLs = currentlyAnalyzingURLs
        self.url = None

    def connectionMade(self):
        self.sendLine("Connection established. What URL you would like to analyze?")

    def connectionLost(self, reason):
        if self.url in self.currentlyAnalyzingURLs:
            del self.currentlyAnalyzingURLs

    def lineReceived(self, line):
        self.handle_GETURL(line)

    def handle_GETURL(self, url):
        self.sendLine(str(self.currentlyAnalyzingURLs))
        self.sendLine(str(self.url))
        if url in self.currentlyAnalyzingURLs:
            status = self.getURLCurrentStatus(url)
            self.sendLine("URL currently analyzing, please choose another.")
            self.sendLine("Current state of URL(%s) is %s" % (url, status))
            return
        self.sendLine("URL %s has taken to analysis!" % (url,))
        status = self.getURLCurrentStatus(url)
        self.sendLine("Current state of URL(%s) is %s" % (url, status))
        self.url = url
        self.currentlyAnalyzingURLs.append(url)
        self.analyzePageInSeparateProcess(url)
        self.sendLine("What URL you would like to analyze?")

    def runAnalysisInAnotherProcess(self, url, urls):
        try:
            self.__analyzer.analyzePages([url])
        except Exception, e:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(e)

        urls.remove(url)

    def analyzePageInSeparateProcess(self, url):
        proxy = processProxy(self, {'url': url, 'urls': self.currentlyAnalyzingURLs}, 'runAnalysisInAnotherProcess')
        proxy.start()

    def getURLCurrentStatus(self, url):
         connector = databaseConnector()
         register = modulesRegister()
         status = "unknown"
         isValidResponse = connector.select(register.getORMClass(configNames.page), ['isValid'], 'url', url)
         if isValidResponse:
             status = "valid" if isValidResponse[0].isValid else "invalid"

         return status

class URLReceiverFactory(Factory):

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.manager = Manager()
        self.currentlyAnalyzingURLs = self.manager.list()

    def buildProtocol(self, addr):
        return URLReceiver(self.analyzer, self.currentlyAnalyzingURLs)

class ConnectionServer:
    __portNumber = 8123
    __analyzer = None

    def __init__(self, analyzer, portNumber = None):
        self.__analyzer = analyzer

        if portNumber is not None:
            self.__portNumber = portNumber

    def run(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.info("Server have initiated on port: " + str(self.__portNumber))
        reactor.listenTCP(self.__portNumber, URLReceiverFactory(self.__analyzer))
        reactor.run()