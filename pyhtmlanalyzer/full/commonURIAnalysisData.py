__author__ = 'hokan'

class commonURIAnalysisData:
    _uri = None

    # constructor
    def __init__(self, uri = None):
        self._uri = uri
    #
    ###################################################################################################################

    # setter and getter for uri
    def getURI(self):
        return self._uri

    def setURI(self, uri):
        self._uri = uri
    #
    ###################################################################################################################