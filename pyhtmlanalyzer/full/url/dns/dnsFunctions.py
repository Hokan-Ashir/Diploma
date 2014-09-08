from copy import copy
import logging
import socket
import re

from dns import reversename
import dns.resolver

from pyhtmlanalyzer.full.commonURIAnalysisData import commonURIAnalysisData


__author__ = 'hokan'

class dnsFunctions(commonURIAnalysisData):
    __listOfMXRecords = None
    __listOfARecords = None
    __listOfNSRecords = None

    # constructor
    def __init__(self, uri):
        commonURIAnalysisData.__init__(self, uri)

    # pre analysis method
    def retrieveDNShostInfo(self):
        try:
            self.__listOfMXRecords = dns.resolver.query(self._uri.split("://")[1].split("/")[0], 'MX')
        except dns.resolver.NoAnswer, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no MX records\n\t %s' % error)
            pass

        try:
            self.__listOfARecords = dns.resolver.query(self._uri.split("://")[1].split("/")[0], 'A')
        except dns.resolver.NoAnswer, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no A records\n\t %s' % error)
            pass

        try:
            self.__listOfNSRecords = dns.resolver.query(self._uri.split("://")[1].split("/")[0], 'NS')
        except dns.resolver.NoAnswer, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no NS records\n\t %s' % error)
            pass


    # for each of the A, NS, MX records for this host:
    # first IP address returned,
    # number of corresponding IP addresses,
    # TTL of the first IP address,
    # Autonomous System number of the first IP
    # NOTE: dns lookup always return different hosts with same query, so to manage this we make some limitations (see below)
    # NOTE: moreover in case of wide networks of servers (like google.com dns)
    # python dns.resolver may return values different from, dig-command, for example
    # print record firstIP of TTL common functions
    def printRecordFirstIP(self, recordType, callbackFunction):
        fistIP = callbackFunction()
        if fistIP is not None:
            print("\nFirst IP of %s record is: %s" % (recordType, fistIP))

    #

    def printRecordFirstIPTTL(self, recordType, callbackFunction):
        fistIP = callbackFunction(True)

        if fistIP is not None:
            print("\nFirst IP's TTL of %s record is: %s" % (recordType, fistIP))
            #

    # print AS Number common function
    def printRecordFirstIPASNumber(self, recordType, callbackFunction):
        ASNumber = callbackFunction()

        if ASNumber is not None:
            print("\nFirst IP's AS Number of %s record is: %s" % (recordType, ASNumber))
        else:
            print("\nCant retrieve Autonomous System number")
            #

    # MX record first IP
    # in case of MX 'firstIP' means 'high priority' or last with same high priority
    def getMXRecordFirstIP(self, getTTL=False):
        if not self.__listOfMXRecords:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no MX records')
            return None

        try:
            maximumPreference = 0
            for i in xrange(0, len(self.__listOfMXRecords)):
                if self.__listOfMXRecords[i].preference >= maximumPreference:
                    maximumPreference = self.__listOfMXRecords[i].preference

            if getTTL:
                return dns.resolver.query(self.__listOfMXRecords[i].exchange, 'A').ttl

            return dns.resolver.query(self.__listOfMXRecords[i].exchange, 'A')[0].address
        except(dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("No MX dns record exists for this dns")
            print("\nNo MX dns record exists for this dns")
            return None

    def printMXRecordFirstIP(self):
        self.printRecordFirstIP('MX', self.getMXRecordFirstIP)

    #

    # MX record first IP TTL
    def getMXRecordFirstIPTTL(self):
        return self.getMXRecordFirstIP(True)


    def printMXRecordFirstIPTTL(self):
        self.printRecordFirstIPTTL('MX', self.getMXRecordFirstIP)

    #

    # MX record first IP AS Number
    def getMXRecordFirstIPASNumber(self):
        firstIP = self.getMXRecordFirstIP()

        if firstIP is not None:
            return self.getASNumber(firstIP)

        return firstIP

    def printMXRecordFirstIPASNumber(self):
        self.printRecordFirstIPASNumber('MX', self.getMXRecordFirstIPASNumber)

    #

    # A record first IP
    # in case of A 'firstIP' means 'first in sorted list'
    def getARecordFirstIP(self, getTTL=False):
        if not self.__listOfARecords:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no A records')
            return None

        try:
            #listOfARecords = dns.resolver.query(self.uri.split("://")[1].split("/")[0], 'A')
            listOfARecords = [ipAddress.address for ipAddress in self.__listOfARecords]
            listOfARecords.sort(key=lambda x: [int(y) for y in x.split('.')])

            if getTTL:
                return self.__listOfARecords.ttl

            return listOfARecords[0]
        except(dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("No A dns record exists for this dns")
            print("\nNo A dns record exists for this dns")
            return None


    def printARecordFirstIP(self):
        self.printRecordFirstIP('A', self.getARecordFirstIP)

    #

    # A record first IP TTL
    def getARecordFirstIPTTL(self):
        return self.getARecordFirstIP(True)


    def printARecordFirstIPTTL(self):
        self.printRecordFirstIPTTL('A', self.getARecordFirstIP)

    #

    # A record first IP AS Number
    def getARecordFirstIPASNumber(self):
        firstIP = self.getARecordFirstIP()
        if firstIP is not None:
            return self.getASNumber(firstIP)

        return firstIP

    def printARecordFirstIPASNumber(self):
        self.printRecordFirstIPASNumber('A', self.getARecordFirstIPASNumber)

    #

    # NS record first IP
    # in case of NS 'firstIP' means 'first in sorted list'
    def getNSRecordFirstIP(self, getTTL=False):
        if not self.__listOfNSRecords:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no NS records')
            return None

        try:
            #listOfNSRecords = dns.resolver.query(self.uri.split("://")[1].split("/")[0], 'NS')
            listOfNSRecords = [".".join(record.target).rstrip(".") for record in self.__listOfNSRecords]
            listOfNSRecords.sort(key=lambda x: [y for y in x.split('.')])

            if getTTL:
                return dns.resolver.query(listOfNSRecords[0], 'A').ttl

            return dns.resolver.query(listOfNSRecords[0], 'A')[0].address
        except(dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("No NS dns record exists for this dns")
            print("\nNo NS dns record exists for this dns")
            return None

    def printNSRecordFirstIP(self):
        self.printRecordFirstIP('NS', self.getNSRecordFirstIP)

    #

    # NS record first IP TTL
    def getNSRecordFirstIPTTL(self):
        return self.getNSRecordFirstIP(True)

    def printNSRecordFirstIPTTL(self):
        self.printRecordFirstIPTTL('NS', self.getNSRecordFirstIP)

    #

    # NS record first IP AS Number
    def getNSRecordFirstIPASNumber(self):
        firstIP = self.getNSRecordFirstIP()
        if firstIP is not None:
            return self.getASNumber(firstIP)

        return firstIP

    def printNSRecordFirstIPASNumber(self):
        self.printRecordFirstIPASNumber('NS', self.getNSRecordFirstIPASNumber)

    #

    # Record IPs number common functions
    def getRecordIPsNumber(self, recordType='MX'):
        try:
            # TODO optimize in switch-case style
            return len(dns.resolver.query(self._uri.split("://")[1].split("/")[0], '%s' % recordType))
        except(dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("No %s dns record exists for this dns" % recordType)
            print("\nNo %s dns record exists for this dns" % recordType)
            return None


    def printRecordIPsNumber(self, recordType='MX'):
        IPsNumber = self.getRecordIPsNumber(recordType)
        if IPsNumber is not None:
            print("\n%s record has: %s IPs" % (recordType, IPsNumber))
            #

    # MX record IPs number
    def getMXRecordIPsNumber(self):
        return self.getRecordIPsNumber('MX')

    def printMXRecordIPsNumber(self):
        self.printRecordIPsNumber('MX')

    #

    # A record IPs number
    def getARecordIPsNumber(self):
        return self.getRecordIPsNumber('A')


    def printARecordIPsNumber(self):
        self.printRecordIPsNumber('A')

    #

    # NS record IPs number
    def getNSRecordIPsNumber(self):
        return self.getRecordIPsNumber('NS')

    def printNSRecordIPsNumber(self):
        self.printRecordIPsNumber('NS')

    #

    # resolved PTR record
    # http://stackoverflow.com/questions/19867548/python-reverse-dns-lookup-in-a-shared-hosting
    def getResolvedPTR(self, onlyFirstIP=True):
        if not self.__listOfARecords:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no A records')
            return None

        #ipAddresses = dns.resolver.query(self.uri.split("://")[1].split("/")[0], 'A')
        listOfResolvedPTR = []
        for ipAddress in self.__listOfARecords:#ipAddresses:
            reverseIP = reversename.from_address("%s" % ipAddress.address)
            try:
                resolvedPTR = dns.resolver.query(reverseIP, 'PTR')[0]
                listOfResolvedPTR.append(resolvedPTR)
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer), error:
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning('Page has no MX domain\n\t %s' % error)
                pass
            if onlyFirstIP:
                break
        return listOfResolvedPTR


    def printResolvedPTR(self, onlyFirstIP=True):
        listOfResolvedPTR = self.getResolvedPTR(onlyFirstIP)
        if listOfResolvedPTR is None:
            print("\nNo PTR dns record exists for this dns")
            return

        for resolvedPTR in listOfResolvedPTR:
            print("\nTarget name: %s" % ".".join(resolvedPTR.target).rstrip("."))
            print("RdClass: %s" % str(resolvedPTR.rdclass))
            print("RdType: %s" % str(resolvedPTR.rdtype))

    #

    # whether the PTR record is equal to the A record for this IP
    # dns.resolver.query(".".join(resolvedPTR.target).rstrip("."), "A")[0].address
    # =?=
    # dns.resolver.query(uri.split("://")[1].split("/")[0], 'A')
    # NOTE: in case of using 'onlyFirstIP' flag method typically return False
    # case dns.resolver get firstIP different each time (in case of multi-hosting)
    def getAandPTRIPsEquality(self, onlyFirstIP=True):
        if not self.__listOfARecords:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning('Page has no A records')
            return None

        listOfResolvedPTR = self.getResolvedPTR(onlyFirstIP)
        if listOfResolvedPTR is None or listOfResolvedPTR == []:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning("No PTR dns record exists for this dns")
            print("\nNo PTR dns record exists for this dns")
            return False

        ipAddresses = copy(self.__listOfARecords)#dns.resolver.query(self.uri.split("://")[1].split("/")[0], 'A')
        if onlyFirstIP:
            ipAddresses = [ipAddresses[0]]

        aListRecordLength = len(ipAddresses)
        ptrListRecordLength = len(listOfResolvedPTR)
        if ptrListRecordLength != aListRecordLength:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning("Length of PTR and A record's list unequal")
            logger.warning("PTR record list length is "
                  + ("more" if ptrListRecordLength > aListRecordLength else "less")
                  + " then A record list")
            print("\nLength of PTR and A record's list unequal")
            print("PTR record list length is "
                  + ("more" if ptrListRecordLength > aListRecordLength else "less")
                  + " then A record list")

        # in case of unordered query, we sort both lists, but before get resolved IP address list from PTR records
        ptrAddressList = []
        for resolvedPTR in listOfResolvedPTR:
            try:
                queryResult = dns.resolver.query(".".join(resolvedPTR.target).rstrip("."), "A")[0].address
            except dns.NXDOMAIN, error:
                logger = logging.getLogger(self.__class__.__name__)
                logger.error(error)
                continue

            ptrAddressList.append(queryResult)

        ptrAddressList.sort(key=lambda x: [int(y) for y in x.split('.')])
        ipAddresses = [ipAddress.address for ipAddress in ipAddresses]
        ipAddresses.sort(key=lambda x: [int(y) for y in x.split('.')])
        for i in xrange(0, min(ptrListRecordLength, aListRecordLength)):
            if ptrAddressList[i] != ipAddresses[i]:
                return False
            if onlyFirstIP:
                break

        return True

    def printAandPTRIPsEquality(self, onlyFirstIP=True):
        print("A and PTR records for "
              + ("first IP" if onlyFirstIP else "all IPs")
              + " are "
              + ("equal" if self.getAandPTRIPsEquality(onlyFirstIP) else "unequal"))

    #

    # get IP's Autonomous System number
    # taken from https://github.com/z0mbiehunt3r/pffdetect/blob/master/pffdetect.py
    # it also contains more AS Number revealing techniques
    # http://whois.cymru.com/cgi-bin/whois.cgi
    #
    #
    # you can get latest AS Number table from
    # http://dns.measurement-factory.com/surveys/openresolvers/ASN-reports/latest.html
    # or you can get the others from
    # http://dns.measurement-factory.com/surveys/openresolvers.html
    def getASNumber(self, IP):

        """
        Get Autonomous System number of given IP address using Team Cymru WHOIS service

        @param ipaddress: IP address to get his AS
        @type ipaddress: str

        @return The autonomous system number
        @rtype: int
        """

        try:
            s = socket.socket()
            s.connect(("whois.cymru.com", 43))
            s.send(IP + "\n")
            # Remove trailing line feed
            response = s.recv(1024).rstrip()
            asn = re.search("(\d+).+\|", response)
            # Check if regex was successful
            if asn is not None:
                asn = asn.group(1)
        except Exception, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            print(error)
            return None

        return asn