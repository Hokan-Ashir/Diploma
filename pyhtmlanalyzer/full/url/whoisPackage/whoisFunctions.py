import logging
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
        try:
            self.whoisData = whois.whois(self._uri)
        except Exception, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error(error)
            pass

    # expiration date
    def getURLExpirationDates(self):
        try:
            return [] if self.whoisData is None else self.whoisData.expiration_date
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no expiration dates\n\t %s' % error)
            return []

    def printURLExpirationDates(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.info("\nExpiration dates:")
        for date in self.getURLExpirationDates():
            logger.info(date)
    #

    # registration date
    def getURLRegistrationDates(self):
        try:
            return [] if self.whoisData is None else self.whoisData.creation_date
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no registration dates\n\t %s' % error)
            return []

    def printURLRegistrationDates(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.info("\nRegistration dates:")
        for date in self.getURLRegistrationDates():
            logger.info(date)
    #

    # update date
    def getURLUpdateDate(self):
        try:
            return [] if self.whoisData is None else self.whoisData.updated_date
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no update dates\n\t %s' % error)
            return []


    def printURLUpdatedDate(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.info("\nUpdate date: %s" % self.getURLUpdateDate())
    #