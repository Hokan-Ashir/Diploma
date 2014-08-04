__author__ = 'hokan'

class commonURIAnalysisData:
    uri = None

    # constructor
    def __init__(self, uri = None):
        self.uri = uri
    #
    ###################################################################################################################

    # setter and getter for uri
    def getURI(self):
        return self.uri

    def setURI(self, uri):
        self.uri = uri
    #
    ###################################################################################################################