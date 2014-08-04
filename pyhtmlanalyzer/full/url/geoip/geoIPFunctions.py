import _mysql
import dns.resolver
from pyhtmlanalyzer.full.commonURIAnalysisData import commonURIAnalysisData

__author__ = 'hokan'

class geoIPFunctions(commonURIAnalysisData):
    ip2locationDBhostName = 'localhost'
    ip2locationDBuserName = 'root'
    ip2locationDBpasswordName = 'root'
    ip2locationDBname = 'ip2location'
    hostGeoIpInfo = None

    # constructor
    def __init__(self, uri):
        commonURIAnalysisData.__init__(self, uri)

    def setIPLocationDatabaseInfo(self, hostName, dbUser, dbPassword, dbName):
        self.ip2locationDBhostName = hostName
        self.ip2locationDBuserName = dbUser
        self.ip2locationDBpasswordName = dbPassword
        self.ip2locationDBname = dbName

    # pre analysis method
    # taken from http://zetcode.com/db/mysqlpython/
    def retrieveGeoIPhostInfo(self):
        try:
            connection = _mysql.connect(self.ip2locationDBhostName,
                                 self.ip2locationDBuserName,
                                 self.ip2locationDBpasswordName,
                                 self.ip2locationDBname)

            ipAddressValuesList = dns.resolver.query(self.uri.split("://")[1].split("/")[0], 'A')[0].address.split('.')
            ipAddressNumber = 16777216 * int(ipAddressValuesList[0]) \
                              + 65536 * int(ipAddressValuesList[1]) \
                              + 256 * int(ipAddressValuesList[2]) \
                              + int(ipAddressValuesList[3])

            connection.query("SELECT country_name, country_code, region_name, city_name, time_zone FROM ip2location_db11 WHERE (ip_from <= %s) AND (ip_to >= %s)" % (ipAddressNumber, ipAddressNumber))
            self.hostGeoIpInfo = connection.use_result().fetch_row()[0]
        except _mysql.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
        finally:
            if connection:
                connection.close()

    # frist alternative way, has nothing except country, country code, city, state, location and IP (no region or timezone)
    #countryInfo = urllib.urlopen('http://api.hostip.info/get_html.php?ip=%s' % response[0].address).read()
    #
    # second alternative way, using this: http://www.geobytes.com/IpLocator.htm?GetLocation
    # thus it has only 20 queries per day, you can use this code
    #   response = dns.resolver.query(self.uri.split("://")[1].split("/")[0], 'A')
    #   xmldata = commonConnectionUtils.openPage(
    #   'http://www.geobytes.com/IpLocator.htm?GetLocation&IpAddress=%s' % response[0].address)[0]
    #   return xmldata.xpath('//input[@name = \'ro-no_bots_pls12\']/@value')[0]
    #
    # third alternative way, using http://www.ip2location.com/developers/python
    # not *.cvs, but *.bin databases files (with ip address from 0.0.0.0 to 99.255.255.255 restriction)
    #
    # country code
    def getCountryCode(self):
        return self.hostGeoIpInfo[1]

    def printCountryCode(self):
        print("\nCountry code: %s" % self.getCountryCode())
    #

    # alternative way via www.geobytes.com (see higher) with
    #   return xmldata.xpath('//input[@name = \'ro-no_bots_pls15\']/@value')[0]
    # code as region value
    #
    # region
    def getRegion(self):
        return self.hostGeoIpInfo[2]

    def printRegion(self):
        print("\nRegion: %s" % self.getRegion())
    #

    # alternative way via www.geobytes.com (see higher) with
    #   return xmldata.xpath('//input[@name = \'ro-no_bots_pls9\']/@value')[0]
    # code as time zone value
    #
    # time zone
    def getTimeZone(self):
        return self.hostGeoIpInfo[4]

    def printTimeZone(self):
        print("\nTime zone: %s" % self.getTimeZone())
    #