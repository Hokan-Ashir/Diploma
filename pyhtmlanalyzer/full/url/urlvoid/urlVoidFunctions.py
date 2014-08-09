from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.full.commonURIAnalysisData import commonURIAnalysisData
from pyhtmlanalyzer.full.url.urlvoid.old_API.urlVoid import API_KEY

__author__ = 'hokan'

class urlVoidFunctions(commonURIAnalysisData):
    API_KEY = '395dd4d82fe6737fa60192e61ecde31a7774f6d3'
    pageData = None

    def __init__(self, uri = None):
        commonURIAnalysisData.__init__(self, uri)
        if uri is not None:
            self.retrieveURLData()

    def retrieveURLData(self):
        if self.uri is None:
            print("\nURI is not set")
            return

        if self.getRemainedQueries() == 0:
            print("\nNo URLVoid queries remain")
            return

        result = commonConnectionUtils.openPage('http://api.urlvoid.com/api1000/'
                                                       + self.API_KEY
                                                       + '/host/'
                                                       + self.uri.split("://")[1].split("/")[0])[0]

        # if there exists any info about site (details tag exists) - save it
        if len(result.xpath('//details')) != 0:
            self.pageData = result

    def getRemainedQueries(self):
        remainedQueries = commonConnectionUtils.openPage('http://api.urlvoid.com/api1000/'
                                                         + self.API_KEY
                                                         + '/stats/remained/')
        return remainedQueries[0].xpath('//queriesremained/text()')[0]

    def getIsHostMalicious(self):
        if self.uri is None:
            print("\nURI is not set")
            return None

        if self.pageData is None:
            print("\nNo URLVoid info about this URI")
            return None

        return True if self.pageData.xpath('//count/text()')[0] != 0 else False

    def printIsHostMalicious(self):
        isHostMalicious = self.getIsHostMalicious()
        if isHostMalicious is None:
            return

        print("Host is " + ('not' if isHostMalicious is False else '') + 'malicious')

    def getDetectedEnginesList(self):
        if self.uri is None:
            print("\nURI is not set")
            return None

        if self.pageData is None:
            print("\nNo URLVoid info about this URI")
            return None

        return self.pageData.xpath('//engine/text()')

    def printDetectedEngines(self):
        detectedEnginesList = self.getDetectedEnginesList()
        if detectedEnginesList is None:
            return

        print("\nList of engines assuming host malicious:")
        for engine in detectedEnginesList:
            print("\t" + engine)