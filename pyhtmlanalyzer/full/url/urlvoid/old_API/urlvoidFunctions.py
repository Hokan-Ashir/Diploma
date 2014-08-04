from pyhtmlanalyzer.full.url.urlvoid.old_API.urlVoid import submit

__author__ = 'hokan'

# urlvoid functions
def getURLVoidScanResults(listOfScanDomains):
    if listOfScanDomains == None or listOfScanDomains == []:
        print("\nNo domain list, can't perform analysis")
        return None

    return submit(listOfScanDomains)

# get all available results
def printURLVoidScanResults(listOfScanDomains, onlyMalicious=False):
    results = getURLVoidScanResults(listOfScanDomains)
    if results.result_dict == None or results.result_dict == {}:
        print("\nNo url void results")
        return

    for domain, domainInfo in results.result_dict.items():
        if not onlyMalicious or domainInfo['detections']:
            print(domain + ": ")
            print("\tLast scan: " + str(domainInfo['last_scan']))
            print("\tDetections: " + str(domainInfo['detections']))
            if domainInfo['detections']:
                for detectedEngine in domainInfo['lists_detected']:
                    print("\t\t" + str(detectedEngine))

# also you can get str-list of only malicious domains
# also you can use results.get_detected_domains() method to retrieve only detected domain list
def getURLVoidMaliciousDomains(listOfScanDomains):
    results = getURLVoidScanResults(listOfScanDomains)
    if results.result_dict is None or results.result_dict == {}:
        print("\nNo url void results")
        return None

    listOfMaliciousDomains = []
    for domain, domainInfo in results.result_dict.items():
        if domainInfo['detections']:
            listOfMaliciousDomains.append(domain)

    return listOfMaliciousDomains


def printURLVoidMaliciousDomains(listOfScanDomains):
    listOfMaliciousDomains = getURLVoidMaliciousDomains(listOfScanDomains)
    if listOfMaliciousDomains is None or listOfMaliciousDomains == []:
        print("\nNone malicious domains")
        return

    print("\nList of malicious domains:")
    for domain in listOfMaliciousDomains:
        print("\t" + str(domain))