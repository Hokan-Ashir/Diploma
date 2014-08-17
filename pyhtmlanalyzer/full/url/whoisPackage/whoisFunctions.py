import whois
from pyhtmlanalyzer.full.commonURIAnalysisData import commonURIAnalysisData

__author__ = 'hokan'


class whoisFunctions(commonURIAnalysisData):
    whoisData = None

    # constructor
    def __init__(self, uri):
        commonURIAnalysisData.__init__(self, uri)

    # pre analysis method
    def retrieveWHOIShostInfo(self):
         self.whoisData = whois.whois(self._uri)

    # expiration date
    def getURLExpirationDates(self):
        try:
            return None if self.whoisData is None else self.whoisData.expiration_date
        except KeyError, error:
            # TODO log that page has no updated date
            pass

    def printURLExpirationDates(self):
        print("\nExpiration dates:")
        for date in self.getURLExpirationDates():
            print(date)
    #

    # registration date
    def getURLRegistrationDates(self):
        try:
            return None if self.whoisData is None else self.whoisData.creation_date
        except KeyError, error:
            # TODO log that page has no updated date
            pass

    def printURLRegistrationDates(self):
        print("\nRegistration dates:")
        for date in self.getURLRegistrationDates():
            print(date)
    #

    # update date
    def getURLUpdateDate(self):
        try:
            return None if self.whoisData is None else self.whoisData.updated_date
        except KeyError, error:
            # TODO log that page has no updated date
            pass


    def printURLUpdatedDate(self):
        print("\nUpdate date: %s" % self.getURLUpdateDate())
    #