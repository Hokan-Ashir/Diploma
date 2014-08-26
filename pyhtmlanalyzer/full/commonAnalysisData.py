__author__ = 'hokan'

class commonAnalysisData(object):
    # class members
    _xmldata = None
    _pageReady = None

    # constructor
    def __init__(self, xmldata = None, pageReady = None):
        self._xmldata = xmldata
        self._pageReady = pageReady
    #
    ###################################################################################################################

    # setter and getter for pageReady
    def getPageReady(self):
        return self._pageReady

    def setPageReady(self, pageReady):
        self._pageReady = pageReady
    #
    ###################################################################################################################

    # setter and getter for xmlPageData
    def getXMLData(self):
        return self._xmldata

    def setXMLData(self, xmldata):
        self._xmldata = xmldata