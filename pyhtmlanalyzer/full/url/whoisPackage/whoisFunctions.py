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
         self.whoisData = whois.whois(self.uri)

    # expiration date
    def getURLExpirationDates(self):
        return None if self.whoisData is None else self.whoisData.expiration_date

    def printURLExpirationDates(self):
        print("\nExpiration dates:")
        for date in self.getURLExpirationDates():
            print(date)
    #

    # registration date
    def getURLRegistrationDates(self):
        return None if self.whoisData is None else self.whoisData.creation_date

    def printURLRegistrationDates(self):
        print("\nRegistration dates:")
        for date in self.getURLRegistrationDates():
            print(date)
    #

    # update date
    def getURLUpdateDate(self):
        return None if self.whoisData is None else self.whoisData.updated_date

    def printURLUpdatedDate(self):
        print("\nUpdate date: %s" % self.getURLUpdateDate())
    #