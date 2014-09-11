import logging
from pyhtmlanalyzer.full.url.urlvoid.old_API.urlVoid import submit

__author__ = 'hokan'

# urlvoid functions
def getURLVoidScanResults(listOfScanDomains):
    if listOfScanDomains == None or listOfScanDomains == []:
        logger = logging.getLogger("getURLVoidScanResults")
        logger.error("\nNo domain list, can't perform analysis")
        return None

    return submit(listOfScanDomains)

# get all available results
def printURLVoidScanResults(listOfScanDomains, onlyMalicious=False):
    logger = logging.getLogger("printURLVoidScanResults")
    results = getURLVoidScanResults(listOfScanDomains)
    if results.result_dict == None or results.result_dict == {}:
        logger.error("\nNo url void results")
        return

    for domain, domainInfo in results.result_dict.items():
        if not onlyMalicious or domainInfo['detections']:
            logger.info(domain + ": ")
            logger.info("\tLast scan: " + str(domainInfo['last_scan']))
            logger.info("\tDetections: " + str(domainInfo['detections']))
            if domainInfo['detections']:
                for detectedEngine in domainInfo['lists_detected']:
                    logger.info("\t\t" + str(detectedEngine))

# also you can get str-list of only malicious domains
# also you can use results.get_detected_domains() method to retrieve only detected domain list
def getURLVoidMaliciousDomains(listOfScanDomains):
    logger = logging.getLogger("getURLVoidMaliciousDomains")
    results = getURLVoidScanResults(listOfScanDomains)
    if results.result_dict is None or results.result_dict == {}:
        logger.error("\nNo url void results")
        return None

    listOfMaliciousDomains = []
    for domain, domainInfo in results.result_dict.items():
        if domainInfo['detections']:
            listOfMaliciousDomains.append(domain)

    return listOfMaliciousDomains


def printURLVoidMaliciousDomains(listOfScanDomains):
    logger = logging.getLogger("printURLVoidMaliciousDomains")
    listOfMaliciousDomains = getURLVoidMaliciousDomains(listOfScanDomains)
    if listOfMaliciousDomains is None or listOfMaliciousDomains == []:
        logger.error("\nNone malicious domains")
        return

    logger.info("\nList of malicious domains:")
    for domain in listOfMaliciousDomains:
        logger.info("\t" + str(domain))