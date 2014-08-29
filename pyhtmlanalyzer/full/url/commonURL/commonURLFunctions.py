from collections import defaultdict
import logging
import re
from urlparse import urlparse
from pyhtmlanalyzer.full.commonURIAnalysisData import commonURIAnalysisData

__author__ = 'hokan'


class commonURLFunctions(commonURIAnalysisData):
    __configDict = None

    # constructor
    def __init__(self, configDict, uri):
        if configDict is None:
            print("\nInvalid parameters")
            return

        commonURIAnalysisData.__init__(self, uri)
        self.__configDict = configDict

    # the domain name length
    def getDomainNameLength(self):
        if urlparse(self._uri).port == None:
            return len(urlparse(self._uri).netloc)
        else:
            return len(urlparse(self._uri).netloc.split(':')[0])

    def printDomainNameLength(self):
        print("\nDomain name is " + str(self.getDomainNameLength()) + " characters length")
    #

    # the TLD of this URL
    def getURLTLD(self):
        TLD = self._uri.split('://')[1].split('/')[0].split('.')[-1]
        return None if TLD.isdigit() is True else TLD

    def printURLTDL(self):
        TLD = self.getURLTLD()
        if TLD is None:
            print("\nNo TLD, or IP-address")
            return

        print("\nTLD: " + str(TLD))
    #

    # the length of the file name appearing in the URL
    def getURLFileNameLength(self):
        uri = self._uri.split('://')[1]

        # in case of no file name in URL
        if uri.count('/') == 0:
            return 0

        return len(uri.split('/')[-1])

    def printURLFileNameLength(self):
        print("\nURL file name length is " + str(self.getURLFileNameLength()) + " characters")
    #

    # some regexps for IP4 & IP6
    # http://home.deds.nl/~aeron/regex/

    # the presence of an IP address in the URL
    # presence of IPv4 in url
    # taken from http://stackoverflow.com/questions/5865817/regex-to-match-an-ip-address
    def getIPv4PresenceInURL(self):
        regExp = re.compile(
            r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')
        return True if re.findall(regExp, self._uri) != None and re.findall(regExp, self._uri) != [] else False


    def printIPv4PresenceInURL(self):
        print("\nIPv4 " + ("exists" if self.getIPv4PresenceInURL() else "do not exists") + " in url")
    #

    # presence Ipv6 in URL
    # first from http://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python
    # second from http://stackoverflow.com/questions/53497/regular-expression-that-matches-valid-ipv6-addresses
    def getIPv6PresenceInURL(self):
        regExp = re.compile(r"""
        #^
        #\s*                         # Leading whitespace
        (?!.*::.*::)                # Only a single whildcard allowed
        (?:(?!:)|:(?=:))            # Colon iff it would be part of a wildcard
        (?:                         # Repeat 6 times:
            [0-9a-f]{0,4}           #   A group of at most four hexadecimal digits
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
        ){6}                        #
        (?:                         # Either
            [0-9a-f]{0,4}           #   Another group
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
            [0-9a-f]{0,4}           #   Last group
            (?: (?<=::)             #   Colon iff preceeded by exacly one colon
             |  (?<!:)              #
             |  (?<=:) (?<!::) :    #
             )                      # OR
         |                          #   A v4 address with NO leading zeros
            (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            (?: \.
                (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            ){3}
        )
        #\s*                         # Trailing whitespace
       # $
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL)

        regExp = re.compile("""(
([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|          # 1:2:3:4:5:6:7:8
([0-9a-fA-F]{1,4}:){1,7}:|                         # 1::                              1:2:3:4:5:6:7::
([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|         # 1::8             1:2:3:4:5:6::8  1:2:3:4:5:6::8
([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|  # 1::7:8           1:2:3:4:5::7:8  1:2:3:4:5::8
([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|  # 1::6:7:8         1:2:3:4::6:7:8  1:2:3:4::8
([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|  # 1::5:6:7:8       1:2:3::5:6:7:8  1:2:3::8
([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|  # 1::4:5:6:7:8     1:2::4:5:6:7:8  1:2::8
[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|       # 1::3:4:5:6:7:8   1::3:4:5:6:7:8  1::8
:((:[0-9a-fA-F]{1,4}){1,7}|:)|                     # ::2:3:4:5:6:7:8  ::2:3:4:5:6:7:8 ::8       ::
fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|     # fe80::7:8%eth0   fe80::7:8%1     (link-local IPv6 addresses with zone index)
::(ffff(:0{1,4}){0,1}:){0,1}
((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]).){3,3}
(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|          # ::255.255.255.255   ::ffff:255.255.255.255  ::ffff:0:255.255.255.255  (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
([0-9a-fA-F]{1,4}:){1,4}:
((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]).){3,3}
(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])           # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
)""", re.VERBOSE | re.IGNORECASE | re.DOTALL)
        return True if re.findall(regExp, self._uri) != None and re.findall(regExp, self._uri) != [] else False


    def printIPv6PresenceInURL(self):
        print("\nIPv6 " + ("exists" if self.getIPv6PresenceInURL() else "do not exists") + " in url")
        #

    # the absence of sub-domain
    def getSubdomainPresecnceInURL(self):
        return True if self._uri.split('://')[1].split('/')[0].split('.')[0] == 'www' else False

    def printSubdomainPresenceInURL(self):
        print("\nSubdomain " + ("exists" if self.getSubdomainPresecnceInURL() else "do not exists") + " in url")
    #

    # port presence in url
    def getPortPresenceInURL(self):
        return True if urlparse(self._uri).port is not None else False

    def printPortPresenceInURL(self):
        print("\nPort " + ("exists" if self.getPortPresenceInURL() else "do not exists") + " in url")
    #

    # absolute and relative length of this URL
    def getAbsoluteAndRelativeURLLength(self):
        return [len(self._uri), len(urlparse(self._uri).path)]

    def getAbsoluteURLLength(self):
        return len(self._uri)

    def getRelativeURLLength(self):
        return len(urlparse(self._uri).path)

    def printAbsoluteAndRelativeURLLength(self):
        resultList = self.getAbsoluteAndRelativeURLLength()
        print("\nAbsolute URL path length: %s characters" % resultList[0])
        print("Relative URL path length: %s characters" % resultList[1])
    #

    # whether the original URL is relative
    def getRelativePathPresenceInURL(self):
        return not bool(urlparse(self._uri).netloc)


    def printRelativePathPresenceInURL(self):
        print("\nURL path is " + ("relative" if self.getRelativePathPresenceInURL() else "absolute"))
    #

    # the presence of suspicious patterns
    def getSuspiciousPatternsPresence(self):
        try:
            listOfSuspiciousPatterns = self.__configDict['url.suspicious.patterns']
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            print("\nNone list of url suspicious patterns, can't perform analysis")
            return

        dictOfSuspiciousPatterns = defaultdict(bool)
        for pattern in listOfSuspiciousPatterns:
            if self._uri.rfind(pattern) != -1:
                dictOfSuspiciousPatterns[pattern] = True

        return dictOfSuspiciousPatterns

    def printSuspiciousPatternsPresence(self):
        dictOfSuspiciousPatterns = self.getSuspiciousPatternsPresence()
        if dictOfSuspiciousPatterns == None or sum(dictOfSuspiciousPatterns.values()) == 0:
            print("\nNone url suspicious patterns")
            return

        print("\nTotal number of detected url suspicious patterns: " + str(sum(dictOfSuspiciousPatterns.values())))
        print("Number of suspicious patterns:")
        for key, value in dictOfSuspiciousPatterns.items():
            if value:
                print(str(key))

    # the presence of a suspicious file name
    def getSuspiciousFileNamesPresence(self):
        try:
            listOfSuspiciousFileNames = self.__configDict['url.suspicious.file.names']
        except KeyError, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(error)
            print("\nNone list of url suspicious file names, can't perform analysis")
            return

        dictOfSuspiciousFileNames = defaultdict(bool)
        for pattern in listOfSuspiciousFileNames:
            if self._uri.rfind(pattern) != -1:
                dictOfSuspiciousFileNames[pattern] = True

        return dictOfSuspiciousFileNames

    def printSuspiciousFileNamesPresence(self):
        dictOfSuspiciousFileNames = self.getSuspiciousFileNamesPresence()
        if dictOfSuspiciousFileNames == None or sum(dictOfSuspiciousFileNames.values()) == 0:
            print("\nNone url suspicious file names")
            return

        print("\nTotal number of detected url suspicious file names: " + str(sum(dictOfSuspiciousFileNames.values())))
        print("Number of suspicious file names:")
        for key, value in dictOfSuspiciousFileNames.items():
            if value:
                print(str(key))
