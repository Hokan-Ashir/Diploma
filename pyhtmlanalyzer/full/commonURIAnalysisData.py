__author__ = 'hokan'

class commonURIAnalysisData:
    __uri = None

    # constructor
    def __init__(self, uri = None):
        self.__uri = uri
    #
    ###################################################################################################################

    # setter and getter for uri
    def getURI(self):
        return self.__uri

    def setURI(self, uri):
        self.__uri = uri
    #
    ###################################################################################################################