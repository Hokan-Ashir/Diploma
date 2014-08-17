__author__ = 'hokan'

class commonAnalysisData:
    # class members
    __xmldata = None
    __pageReady = None

    # constructor
    def __init__(self, xmldata = None, pageReady = None):
        self.__xmldata = xmldata
        self.__pageReady = pageReady
    #
    ###################################################################################################################

    # setter and getter for pageReady
    def getPageReady(self):
        return self.__pageReady

    def setPageReady(self, pageReady):
        self.__pageReady = pageReady
    #
    ###################################################################################################################

    # setter and getter for xmlPageData
    def getXMLData(self):
        return self.__xmldata

    def setXMLData(self, xmldata):
        self.__xmldata = xmldata