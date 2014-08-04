from pyhtmlanalyzer.pyHTMLAnalyzer import pyHTMLAnalyzer

__author__ = 'hokan'

class statistics:
    def __init__(self):
        pass

    def getHTMLCommonStatistics(self, urlList):
        pyHTMLAnalyser = pyHTMLAnalyzer()
        resultList = []
        for url in urlList:
            resultList.append(pyHTMLAnalyser.getNumberOfAnalyzedPageFeaturesByFunction(url))

