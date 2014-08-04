__author__ = 'hokan'

class commonAnalysisData:
    # class members
    xmldata = None
    pageReady = None

    # constructor
    def __init__(self, xmldata = None, pageReady = None):
        self.xmldata = xmldata
        self.pageReady = pageReady
    #
    ###################################################################################################################

    # setter and getter for pageReady
    def getPageReady(self):
        return self.pageReady

    def setPageReady(self, pageReady):
        self.pageReady = pageReady
    #
    ###################################################################################################################

    # setter and getter for xmlPageData
    def getXMLData(self):
        return self.xmldata

    def setXMLData(self, xmldata):
        self.xmldata = xmldata