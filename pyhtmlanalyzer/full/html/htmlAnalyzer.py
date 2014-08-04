from collections import defaultdict
import hashlib
import operator
import timeit
import re
from pyhtmlanalyzer import CLSID
from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.commonFunctions.commonXPATHUtils import commonXPATHUtils
from pyhtmlanalyzer.full.commonAnalysisData import commonAnalysisData
from pyhtmlanalyzer.full.commonURIAnalysisData import commonURIAnalysisData

__author__ = 'hokan'

class htmlAnalyzer(commonAnalysisData, commonURIAnalysisData):
    configDict = None
    openedAsXML = None
    listOfAnalyzeFunctions = []

    # constructor
    def __init__(self, configDict, xmldata = None, pageReady = None, uri = None):
        commonAnalysisData.__init__(self, xmldata, pageReady)
        commonURIAnalysisData.__init__(self, uri)
        if configDict is not None:
           self.configDict = configDict
        else:
            print("\nInvalid parameters")
            return

        self.listOfAnalyzeFunctions = commonFunctions.getAnalyzeFunctionList('analyzeFunctions', 'html.module')
    #
    ###################################################################################################################

    # elements with small area functions
    def getNumberOfElementsWithSmallArea(self, widthLimit, heightLimit, squarePixelsLimit):
        try:
            listOfTags = self.configDict["html.elements.with.small.area"]
        except:
            print("\nNone list of elements with small area, can't perform analysis")
            return

        dictOfElementsWithSmallArea = {}
        for item in listOfTags:
            dictOfElementsWithSmallArea[item] = len(self.xmldata.xpath(
            '//%s[@width <= %f or @height <= %f or (number(@width) * number(@height)) <= %f]'
            % (item, widthLimit, heightLimit, squarePixelsLimit)))
        return dictOfElementsWithSmallArea


    def getTotalNumberOfElementsWithSmallArea(self, widthLimit = 2.0, heightLimit = 2.0, squarePixelsLimit = 30.0):
        return sum(self.getNumberOfElementsWithSmallArea(widthLimit, heightLimit, squarePixelsLimit).values())


    def getTotalNumberOfElementsWithSmallAreaByDict(self, dictOfNumberOfElements):
        return sum(dictOfNumberOfElements.values())

    def printNumberOfElementsWithSmallArea(self, widthLimit = 2.0, heightLimit = 2.0, squarePixelsLimit = 30.0):
        numberOfElementsWithSmallAreaDict = self.getNumberOfElementsWithSmallArea(widthLimit, heightLimit, squarePixelsLimit)
        if numberOfElementsWithSmallAreaDict == None or sum(numberOfElementsWithSmallAreaDict.values()) == 0:
            print("\nNone elements with small area (width less than %f, height less than %f, square less than %f"
                  % (widthLimit, heightLimit, squarePixelsLimit))
            return

        print("\nTotal number of elements with small area (width less than %f, height less than %f, square less than %f: "
              % (widthLimit, heightLimit, squarePixelsLimit) + str(sum(numberOfElementsWithSmallAreaDict.values())))
        print("Number of elements with small area (width less than %f, height less than %f, square less than %f:"
              % (widthLimit, heightLimit, squarePixelsLimit))
        for key, value in numberOfElementsWithSmallAreaDict.items():
            if value > 0:
                print("<" + str(key) + ">: " + str(value))
    #
    ###################################################################################################################

    # duplicated elements functions
    def getNumberOfDuplicatedElements(self):
        # TODO cause xPath sees out-of-root html-tag tags as children of another html-tag, manage this; or left assuming
        # suspicious page
        try:
            listOfDuplicatedTags = self.configDict["html.non.dulpicated.elemets"]
        except:
            print("\nNone list of non-duplicated elements, can't perform analysis")
            return

        dictOfDuplicatedElementsCount = {}
        for item in listOfDuplicatedTags:
            dictOfDuplicatedElementsCount[item] = self.xmldata.xpath('count(//%s)' % item)
        return dictOfDuplicatedElementsCount


    def getTotalNumberOfDuplicatedElements(self):
        return sum(self.getNumberOfDuplicatedElements().values())


    def isElementsDuplicated(self):
        return True if self.getTotalNumberOfDuplicatedElements() > 4 else False

    def printNumberOfDuplicatedElements(self):
        duplicatedElementsDict = self.getNumberOfDuplicatedElements()
        if duplicatedElementsDict == None or sum(duplicatedElementsDict.values()) == 0:
            print("\nNone duplicated elements")
            return

        print("\nTotal number of core html elements: " + str(sum(duplicatedElementsDict.values())))
        print("Number of core html elements:")
        for key, value in duplicatedElementsDict.items():
            if value > 0:
                print("<" + str(key) + ">: " + str(value))
    #
    ###################################################################################################################

    # elements with suspicious content functions
    #//*[not(self::script or self::style)]/text()[string-length()
    def getNumberOfElementsWithSuspiciousContent(self, characterLength, whitespacePercentage):
        # first count length of content,
        # then check string with whitespaces has %whitespacePercentage% spaces;
        # furthermore we do not add strings without spaces at all ("and .." part of condition)
        tooLongCharacterStringsCount = self.xmldata.xpath('count(//text()[string-length() > %d])' % characterLength)
        tooLessWhitespacesStringsCount = self.xmldata.xpath(
            'count(//text()[(1 - (string-length(translate(., \' \', \'\')) div string-length())) < %f '
            'and (string-length(translate(., \' \', \'\')) != string-length())])'
            % whitespacePercentage)
        return [tooLongCharacterStringsCount, tooLessWhitespacesStringsCount]


    def getTotalNumberOfElementsWithSuspiciousContent(self, characterLength = 128, whitespacePercentage = 5.0):
        return sum(self.getNumberOfElementsWithSuspiciousContent(characterLength, whitespacePercentage))


    def getTotalNumberOfElementsWithSuspiciousContentByList(self, listOfNumberOfElements):
        return sum(listOfNumberOfElements)

    def printNumberOfElementsWithSuspiciousContent(self, characterLength = 128, whitespacePercentage = 5.0):
        suspiciousElements = self.getNumberOfElementsWithSuspiciousContent(characterLength, whitespacePercentage)
        if sum(suspiciousElements) == 0:
            print("\nNone elements with suspicious content")
            return

        print("\nNumber of suspicious elements:")
        print("with length more than %d: " % characterLength + str(suspiciousElements[0]))
        print("with less than %f percent of whitespaces: " % whitespacePercentage + str(suspiciousElements[1]))
    #
    ###################################################################################################################

    # it's impossible to get content of non-closing tag via lxml
    # but we can get content of void-tags parsing file in XML format and get @.tail@ node field instead of @text@
    # number of void-elements with content
    def getNumberOfVoidElementsWithContent(self):
        if self.openedAsXML == False:
            print("\nObject not opened as XML, impossible to count of void elements with content")
            return

        try:
            listOfVoidTagNames = self.configDict["html.void.elements"]
        except:
            print("\nNone list of void tags, can't perform analysis")
            return
        dictOfVoidElementsWithContent = defaultdict(int)
        for tag in listOfVoidTagNames:
            listOfTags = self.xmldata.xpath('//%s' % tag)
            for item in listOfTags:
                if item.tail != None and len(item.tail) > 0:
                    dictOfVoidElementsWithContent[tag] += 1
                    #self.xmldata.xpath('count(//%s[string-length(text()) > 0])' % tag)

        return dictOfVoidElementsWithContent

    def getTotalNumberOfVoidElementsWithContent(self):
        return sum(self.getNumberOfVoidElementsWithContent().values())

    def printNumberOfVoidElementsWithContent(self):
        dictOfVoidElementsWithContent = self.getNumberOfVoidElementsWithContent()
        if dictOfVoidElementsWithContent == None or sum(dictOfVoidElementsWithContent.values()) == 0:
            print("\nNone void elements with content")
            return

        print("\nTotal number of void elements with content: " + str(sum(dictOfVoidElementsWithContent.values())))
        print("Number of void elements with content:")
        for key, value in dictOfVoidElementsWithContent.items():
            if value > 0:
                print("<" + str(key) + ">: " + str(value))
    #
    ###################################################################################################################

    # objects with suspicious content
    def getObjectsWithSuspiciousContent(self):
        dictOfSuspiciousObjects = {}
        for key in CLSID.clsidlist.keys():
            # we use value-of-classid-attribute.upper() cause we unsure that authors of malicious pages will
            # follow the rules
            itemsCount = self.xmldata.xpath('count(//object[%s = \'CLSID:%s\'])'
                                            % (commonXPATHUtils.toUpperCase('@classid', False), key))
            if itemsCount > 0:
                dictOfSuspiciousObjects[key] = itemsCount

        for key in CLSID.clsnamelist.keys():
            # here we use key.upper() cause not all CLSNames in upper case
            # we also use value-of-progid-attribute.upper() cause we unsure that authors of malicious pages will
            # follow the rules
            itemsCount = self.xmldata.xpath("count(//object[%s = '%s'])"
                                            % (commonXPATHUtils.toUpperCase('@progid', False), str(key).upper()))
            if itemsCount > 0:
                dictOfSuspiciousObjects[key] = itemsCount

        return dictOfSuspiciousObjects

    def getTotalNumberOfObjectsWithSuspiciousContent(self):
        return sum(self.getObjectsWithSuspiciousContent().values())

    def printNumberOfObjectsWithSuspiciousContent(self):
        dictOfSuspiciousObjects = self.getObjectsWithSuspiciousContent()
        if sum(dictOfSuspiciousObjects.values()) == 0:
            print("\nNone suspicious objects")
            return

        print("\nTotal number of suspicious objects: " + str(sum(dictOfSuspiciousObjects.values())))
        #sys.stdout.write("Number of suspicious objects:")
        print("Number of suspicious objects:")
        for key, value in dictOfSuspiciousObjects.items():
            if value > 0:
                print(str(key) + ": " + str(value))
    #
    ###################################################################################################################

    # number of included URLs
    def getIncludedURLs(self):
        try:
            listOfTags = self.configDict["html.included.urls.elements"]
        except:
            print("\nNone list of tags with included URLs, can't perform analysis")
            return
        dictOfIncludedURLsOjects = {}
        for item in listOfTags:
            dictOfIncludedURLsOjects[item] = self.xmldata.xpath('count(//%s[@src])' % item)

        return dictOfIncludedURLsOjects

    def getTotalNumberOfIncludedURLs(self):
        return sum(self.getIncludedURLs().values())

    def printNumberOfIncludedURLs(self):
        dictElementsWithIncludedURLs = self.getIncludedURLs()
        if dictElementsWithIncludedURLs == None or sum(dictElementsWithIncludedURLs.values()) == 0:
            print("\nNone elements with included URLs")
            return

        print("\nTotal number of elements with included URLs: " + str(sum(dictElementsWithIncludedURLs.values())))
        print("Number of elements with included URLs:")
        for key, value in dictElementsWithIncludedURLs.items():
            if value > 0:
                print("<" + str(key) + ">: " + str(value))
    #
    ###################################################################################################################

    # number of known malicious patterns
    def getNumberOfKnownMaliciousPatternObjects(self):
        # TODO add additional patterns
        listOfMaliciousPatterns = ['metaTagRedirection']
        dictOfMaliciousPatternObjects = {}
        for item in listOfMaliciousPatterns:
            if item == 'metaTagRedirection':
                # the presence of a meta tag that causes the refresh of the
                # page, pointing it to index.php?spl=, as this is very common in
                # pages redirecting to exploit servers.
                # also includes https:// case
                dictOfMaliciousPatternObjects[item]\
                    = self.xmldata.xpath('count(//meta[contains(%s, URL)'
                                         ' and (contains(%s, \'http://index.php?spl=\')'
                                         ' or contains(%s, \'https://index.php?spl=\'))])'
                                         % (commonXPATHUtils.toUpperCase('@content', False),
                                            commonXPATHUtils.toLowerCase('@content', False),
                                            commonXPATHUtils.toLowerCase('@content', False)))
        return dictOfMaliciousPatternObjects

    def getTotalNumberOfKnownMaliciousPatternObjects(self):
        return sum(self.getNumberOfKnownMaliciousPatternObjects().values())

    def printNumberOfKnownMaliciousPatternObjects(self):
        dictElementsWithMaliciousPatterns = self.getNumberOfKnownMaliciousPatternObjects()
        if sum(dictElementsWithMaliciousPatterns.values()) == 0:
            print("\nNone elements with malicious patterns")
            return

        print("\nTotal number of elements with malicious patterns:"
              + str(sum(dictElementsWithMaliciousPatterns.values())))
        print("Number of elements with malicious patterns:")
        for key, value in dictElementsWithMaliciousPatterns.items():
            if value > 0:
                print("pattern: " + str(key) + " - " + str(value))
    #
    ###################################################################################################################

    # number of out-of-place tags
    def getNumberOutOfPlaceTags(self):
        # NOTE for future work there is more common list of restrictions for <head> tag:
        # http://www.w3schools.com/tags/tag_head.asp link
        # I've deleted <embed> and <script> tags cause they can be under <head> tag
        try:
            listOfUnderHeadTags = self.configDict["html.under.head.elements"]
        except:
            print("\nNone list of under-head-tag elements, can't perform analysis")
            return

        try:
            listOfOutOfRootTags = self.configDict["html.out.of.root.elements"]
        except:
            print("\nNone list of out-of-root-tag elements, can't perform analysis")
            return

        try:
            listOfBlockLevelTags = self.configDict["html.block.level.elements"]
        except:
            print("\nNone list of block level elements, can't perform analysis")
            return

        try:
            listOfNonBlockTags = self.configDict["html.non.block.elements"]
        except:
            print("\nNone list of non block level elements, can't perform analysis")
            return

        try:
            listOfBlockContentInlineTags = self.configDict["html.no.block.content.inline.elements"]
        except:
            print("\nNone list of no-block-content inline elements, can't perform analysis")
            return

        # result dictionary initialization
        # we don't use defaultdict() because of total statistics and opportunity getting KeyError exceptions
        dictElementsOutOfPlace = {}
        for item in listOfUnderHeadTags:
            dictElementsOutOfPlace[item] = 0
        for item in listOfOutOfRootTags:
            dictElementsOutOfPlace[item] = 0
        for item in listOfBlockLevelTags:
            dictElementsOutOfPlace[item] = 0
        for item in listOfNonBlockTags:
            dictElementsOutOfPlace[item] = 0
        for item in listOfBlockContentInlineTags:
            dictElementsOutOfPlace[item] = 0

        listOfUnderRootElements = self.xmldata.xpath('/*')[0].xpath('./*')
        for item in listOfUnderRootElements:
            # count number of tags outside root html-tag or in head or title
            if item.xpath('name(.)') == 'head':
                # cause <title> is child of <head> we removed it from comparison above
                for tag in listOfUnderHeadTags:
                    dictElementsOutOfPlace[tag] += item.xpath('count(.//%s)' % tag)
            elif item.xpath('name(.)') == 'html':
                # cause lxml sees out-of-root tag elements as children of another <html> tag,
                # in comparison above it mentioned
                # it is NOT root-html tag!
                for tag in listOfOutOfRootTags:
                    dictElementsOutOfPlace[tag] += item.xpath('count(.//%s)' % tag)

        # NOTE: deprecated tags like 'frame'-tag duplicated by 'p' tags
        # i.e. in VLC.htm tag <frame> in <html> will be empty text field (source line 65)
        # furthermore tag <p> presents at source line 65 with filled text field
        # count number of tags directly in root html-tag
        for item in listOfUnderRootElements:
            # if-statement faster then catch KeyError exception
            if item.tag in dictElementsOutOfPlace.keys():
                dictElementsOutOfPlace[item.tag] += 1

        # http://www.w3.org/TR/html401/sgml/dtd.html
        # http://www.w3.org/TR/html401/struct/text.html#edef-P
        # https://developer.mozilla.org/en-US/docs/HTML/Block-level_elements
        # https://developer.mozilla.org/en-US/docs/HTML/Inline_elements
        # http://dev.w3.org/html5/markup/syntax.html#void-element
        # count number of all block elements in block elements
        for tag in listOfNonBlockTags:
            # get all elements of type 'tag' from body (cause we already count out-of-body-tag elements)
            listOfTagElements = self.xmldata.xpath('/html/body//%s' % tag)
            for element in listOfTagElements:
                for tag2 in listOfBlockLevelTags:
                    # check that parent of this tag has name from list of block-type tags
                    if element.xpath('name(..) = \'%s\'' % tag2):
                        dictElementsOutOfPlace[tag2] += 1
                        break

        # check number of special inline elements with block content
        for tag in listOfBlockContentInlineTags:
            # get all elements of type 'tag' from body (cause we already count out-of-body-tag elements)
            listOfTagElements = self.xmldata.xpath('/html/body//%s' % tag)
            for element in listOfTagElements:
                # check that their parent has no text content
                if (element.xpath('..')[0].text == '\n' or element.xpath('..')[0].text == None):
                    # check if this tags have block content children
                    for tag2 in listOfBlockLevelTags:
                        if (element.xpath('count(.//%s)' % tag2) != 0):
                            dictElementsOutOfPlace[tag] += 1
                            break

        # check out existence of <title> tag in <head> tag or its duplication
        # this rule is taken from: http://www.w3schools.com/tags/tag_head.asp
        # and http://www.w3schools.com/tags/tag_title.asp
        # count <title> tags in valid <head> (under root <html>)
        # here we can make fast check of duplication of <title> tag like this:
        # if len(titleTagList) > 1:
        #    # more than one <title> tag - wrong
        #    dictElementsOutOfPlace['title'] += len(titleTagList) - 1
        #
        # but EVERY <title> tag may be misplaced, so we count <title> tags in valid <head>
        numberOfTitleTagsUnderValidHead = self.xmldata.xpath('count(/html/head//title)')
        if numberOfTitleTagsUnderValidHead >= 1:
            # here is at least one in-place <title>
            # subtract from all invalid <title> tags one valid
            dictElementsOutOfPlace['title'] = self.xmldata.xpath('count(//title)') - 1
        else:
            # otherwise all <title> tags are invalid
            dictElementsOutOfPlace['title'] = self.xmldata.xpath('count(//title)')

        return dictElementsOutOfPlace

    def getTotalNumberOutOfPlaceTags(self):
        return sum(self.getNumberOutOfPlaceTags().values())

    def printNumberOutOfPlaceTags(self):
        dictOutOfPlaceTags = self.getNumberOutOfPlaceTags()
        if dictOutOfPlaceTags == None or sum(dictOutOfPlaceTags.values()) == 0:
            print("\nNone out of place elements")
            return

        print("\nTotal number of elements out of place: " + str(sum(dictOutOfPlaceTags.values())))
        print("Number of elements out of place:")
        for key, value in dictOutOfPlaceTags.items():
            if value > 0:
                print("<" + str(key) + ">: " + str(value))
    #
    ###################################################################################################################

    # pages comparing via recursively subtrees comparing
    # NOTE: this function just compare subtrees by level of depth
    # so pages like:
    # <tag1>
    #   <tag2>
    #       <tag3>
    #          <sub_tree> ... </subtree>
    #       </tag3>
    #   </tag2>
    # <tag1>
    #
    # <tag1>
    #   <tag2>
    #       <tag4>
    #           <subtree> ... </subtree>
    #       </tag4>
    #   </tag2>
    # </tag1>
    #
    # will be different, even if subtrees are equal
    @staticmethod
    def getPagesPercentageMismatch(xmldataFirstPage, xmldataSecondPage):
        probablyNotMatch = (xmldataFirstPage.xpath('count(//*)') != xmldataSecondPage.xpath('count(//*)'))
        if probablyNotMatch:
            print("\nThis pages probably not match")
        numberOfMismatchedTags = htmlAnalyzer.getNumberOfMismatchedTagNames(xmldataFirstPage.xpath('/*')[0],
                                                                            xmldataSecondPage.xpath('/*')[0])
        return numberOfMismatchedTags / xmldataFirstPage.xpath('count(//*)')

    @staticmethod
    def getNumberOfMismatchedTagNames(nodeFirstPage, nodeSecondPage):
        numberOfDifferentNodes = 0
        listChildElementsFirstPage = nodeFirstPage.xpath('./*')
        listChildElementsSecondPage = nodeSecondPage.xpath('./*')

        # TODO ask if this is necessary; sure it does
        # create pair lists that will be sorted by tag-name
        listPairChildFirstPage = []
        for item in listChildElementsFirstPage:
            listPairChildFirstPage.append((item.xpath('name(.)'), item))
        listPairChildFirstPage.sort(key=operator.itemgetter(0))

        listPairChildSecondPage = []
        for item in listChildElementsSecondPage:
            listPairChildSecondPage.append((item.xpath('name(.)'), item))
        listPairChildSecondPage.sort(key=operator.itemgetter(0))

        # always comparing fist element from first page child list, no index needed
        while True:
            if listPairChildFirstPage == []:
                break

            # get first element from first tag-list, search for its name in second list
            nodeNameFirstPage = listPairChildFirstPage[0][0]
            nodeNameSecondPage = None
            secondPageListIndex = -1
            for j in range(0, len(listPairChildSecondPage)):
                nodeNameSecondPage = listPairChildSecondPage[j][0]
                if nodeNameSecondPage == nodeNameFirstPage:
                    secondPageListIndex = j
                    break

            # can't find this tag, get number of all tags in subtree
            if nodeNameSecondPage is None:
                # get number of all childes ANY depth plus this tag name mismatch
                numberOfDifferentNodes += listPairChildFirstPage[0][1].xpath('count(.//*)') + 1
            # find one, recursively search other mismatches and delete match tag in second list
            else:
                # TODO here can be add attributes lists comparing
                numberOfDifferentNodes += \
                    htmlAnalyzer.getNumberOfMismatchedTagNames(listPairChildFirstPage[0][1],
                                                               listPairChildSecondPage[secondPageListIndex][1])
                listPairChildSecondPage.pop(secondPageListIndex)

            # delete first node
            listPairChildFirstPage.pop(0)

        # in case lists have different length (first page has less tags than second)
        # get number of all childes ANY depth plus this tag name mismatch
        for item in listPairChildSecondPage:
            numberOfDifferentNodes += item[1].xpath('count(.//*)') + 1

        return numberOfDifferentNodes

    # NOTE according to XML standard there can be ONLY ONE root node
    # so at first we selects all children of root (can be only one) and select first (can be only html)
    # then if there is other root-nodes they will appear in children of selected html-node
    # i.e:
    # <html>
    #   <head> ... </head>
    #   <body> ... </body>
    # <html>
    # <body>
    # </body>
    #
    # xmldata.xpath('/*')  - selects list with one html-node
    # xmldata,xpath('/*')[0].xpath('./*') - selects list with head, body and html node (!) (even there is body-tag)
    # xmldata,xpath('/*')[0].xpath('./*')[2].xpath('./*') - selects list with body-tag which is after html tag
    # we do not mention this in trees comparison, cause we search only mismatching
    # but this will help search out-of-place tags; not in place according DTD
    @staticmethod
    def printPagesPercentageMismatch(xmldataFirstPage, xmldataSecondPage):
        if xmldataFirstPage is None or xmldataSecondPage is None:
                print("Insufficient number of parameters")
                return
        pagesPercentageMismatch = htmlAnalyzer.getPagesPercentageMismatch(xmldataFirstPage, xmldataSecondPage)
        print("\nPages percentage mismatch is: " + str(pagesPercentageMismatch * 100) + "%")
    #
    ###################################################################################################################

    # number of hidden tags
    def getTotalNumberOfHiddenTags(self):
        return self.xmldata.xpath('count(//*[%s = \'true\'])' % commonXPATHUtils.toLowerCase('@hidden', False))

    def printTotalNumberOfHiddenTags(self):
        numberOfHiddenTags = self.getTotalNumberOfHiddenTags()
        if numberOfHiddenTags == 0:
            print("\nNone hidden tags")
            return

        print("\nTotal number of hidden tags: " + str(numberOfHiddenTags))
    #
    ###################################################################################################################

    # number of script elements
    def getNumberOfScriptElements(self):
        numberOfInlineScriptElements = self.xmldata.xpath('count(//script[not(@src)])')
        numberOfIncludedScriptElements = self.xmldata.xpath('count(//script[@src])')
        return [numberOfInlineScriptElements, numberOfIncludedScriptElements]

    def getTotalNumberOfScriptElements(self):
        return sum(self.getNumberOfScriptElements())

    def printNumberOfScriptElements(self):
        listOfScriptElements = self.getNumberOfScriptElements()
        if sum(listOfScriptElements) == 0:
            print("\nNone script elements")
            return

        print("\nTotal number of script elements: " + str(sum(listOfScriptElements)))
        print("Number of inline script elements: " + str(listOfScriptElements[0]))
        print("Number of included script elements: " + str(listOfScriptElements[1]))
    #
    ###################################################################################################################

    # number of script-tags with src value and wrong extension of file
    # NOTE: see this: http://www.w3schools.com/tags/att_script_type.asp
    # and this: http://www.iana.org/assignments/media-types/media-types.xhtml#text
    # for all text script types

    # TODO ask: Is it valid to pass through elements like this:
    # <script type="text/javascript" src="http://s7.addthis.com/js/250/addthis_widget.js#pubid=ra-4f661ec623a400f0">
    def getNumberOfScriptElementsWithWrongFileExtension(self):
        #scriptTagTypeList = ['text/javascript', 'text/ecmascript', 'application/ecmascript', 'application/javascript',
        #                     'text/vbscript']
        dictOfScriptElements = {}

        # NOTE: there is no end-with() function in xPath 1.0, so you can use something like this:
        # $str2 = substring($str1, string-length($str1)- string-length($str2) +1)
        # will return true and false as result

        # for every script type attribute value check:
        # if attribute type match pattern
        #   attribute src exists and not empty
        #   attribute type value ends-with some extension
        # NOTE: cause both category and subcategory are case insensitive (as well as file extension) we use to_lower_case
        # xPath 1.0 wrappers

        # javascript
        dictOfScriptElements['text/javascript'] \
            = self.xmldata.xpath('count(//script[%s = \'text/javascript\''
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % (commonXPATHUtils.toLowerCase('@type', False),
                                    commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                             '.js',
                                                             False,
                                                             True)))
        dictOfScriptElements['application/javascript'] \
            = self.xmldata.xpath('count(//script[%s = \'application/javascript\''
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % (commonXPATHUtils.toLowerCase('@type', False),
                                    commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                             '.js',
                                                             False,
                                                             True)))
        dictOfScriptElements['default']\
            = self.xmldata.xpath('count(//script[not(@type)'
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                            '.js',
                                                            False,
                                                            True))

        # ecmascript
        dictOfScriptElements['text/ecmascript'] \
            = self.xmldata.xpath('count(//script[%s = \'text/ecmascript\''
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % (commonXPATHUtils.toLowerCase('@type', False),
                                    commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                             '.es',
                                                             False,
                                                             True)))
        dictOfScriptElements['application/ecmascript']\
            = self.xmldata.xpath('count(//script[%s = \'application/ecmascript\''
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % (commonXPATHUtils.toLowerCase('@type', False),
                                    commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                             '.es',
                                                             False,
                                                             True)))

        # vbscript
        # NOTE: possible file extensions (.vbs, .vbe, .wsf, .wsc), maybe some of them deprecated
        dictOfScriptElements['text/vbscript']\
            = self.xmldata.xpath('count(//script[%s = \'text/vbscript\''
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % (commonXPATHUtils.toLowerCase('@type', False),
                                    commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                             '.vbs',
                                                             False,
                                                             True)))
        dictOfScriptElements['text/vbscript'] \
            = self.xmldata.xpath('count(//script[%s = \'text/vbscript\''
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % (commonXPATHUtils.toLowerCase('@type', False),
                                    commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                             '.vbs',
                                                             False,
                                                             True)))
        dictOfScriptElements['text/vbscript'] \
            = self.xmldata.xpath('count(//script[%s = \'text/vbscript\''
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % (commonXPATHUtils.toLowerCase('@type', False),
                                    commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                             '.vbs',
                                                             False,
                                                             True)))
        dictOfScriptElements['text/vbscript'] \
            = self.xmldata.xpath('count(//script[%s = \'text/vbscript\''
                                 ' and boolean(@src)'
                                 ' and @src != ""'
                                 ' and not(%s)])'
                                 % (commonXPATHUtils.toLowerCase('@type', False),
                                    commonXPATHUtils.endWith(commonXPATHUtils.toLowerCase('@src', False),
                                                             '.vbs',
                                                             False,
                                                             True)))
        return dictOfScriptElements


    def getTotalNumberOfScriptElementsWithWrongFileExtension(self):
        return sum(self.getNumberOfScriptElementsWithWrongFileExtension().values())

    def printNumberOfScriptElementsWithWrongFileExtension(self):
        dictOfScriptElementsWithWrongFileExtensions = self.getNumberOfScriptElementsWithWrongFileExtension()
        if sum(dictOfScriptElementsWithWrongFileExtensions.values()) == 0:
            print("\nNone script elements with wrong file extensions")
            return

        print("\nTotal number of script elements with wrong file extensions: "
              + str(sum(dictOfScriptElementsWithWrongFileExtensions.values())))
        print("Number of script elements with wrong file extensions:")
        for key, value in dictOfScriptElementsWithWrongFileExtensions.items():
            if value > 0:
                print("script attribute type = " + str(key) + " - " + str(value))
    #
    ###################################################################################################################

    # number of characters in page
    # number of characters in text content of page
    def getNumberOfTextCharactersInPage(self):
        # get all text nodes except script nodes (in which we must delete all comments before take len() call
        # NOTE: we ignore embed script code inside <script> tags with @src attribute, cause it can't be executed
        listOfTextNodesExceptScript = self.xmldata.xpath('//*[name() != \'script\']/text()')
        numberOfCharactersInPage = 0
        for item in listOfTextNodesExceptScript:
            numberOfCharactersInPage += len(item)

        listOfInlineScriptTextNodes = self.xmldata.xpath('//script[not(@src)]/text()')
        for item in listOfInlineScriptTextNodes:
            # NOTE: only JS-comments
            # regexp for C/C++-like comments, also suitable for js-comments
            # ( /\* - begin C-like comment
            # [^\*/]* - everything except closing C-like comment 0+ times
            # \*/ - closing C-like comment
            # | - another part of regExp
            # // - begin of C++-like comment
            # .* - any symbol 0+ times
            # \n?) - until end of line, which can be off
            regExp = re.compile(r'(/\*[^\*/]*\*/|//.*\n?)')
            numberOfCharactersInPage = len(re.sub(regExp, '', str(item.encode('utf-8'))))

        return numberOfCharactersInPage

    # number of characters in page by xPath standards
    def getTotalNumberOfCharactersInPage(self):
        numberOfCharactersInPage = 0
        listOfAllNodes = self.xmldata.xpath('//*')
        for node in listOfAllNodes:
            # get node name; add 2 characters for open and close bracket
            # duplicate it for close tag, add 1 character for slash
            numberOfCharactersInPage += ((node.xpath('string-length(name(.))') + 2) * 2) + 1
            # get attribute values list
            listOfAllAttributes = node.xpath('./@*')
            # iteratively get attributes names (and it's length) and add attributes values length
            for i in range(0, len(listOfAllAttributes)):
                # add 1, cause xPath counts list elements from 1
                numberOfCharactersInPage += node.xpath('string-length(name(./@*[%d]))' % (i + 1))
                numberOfCharactersInPage += len(listOfAllAttributes[i])
        return numberOfCharactersInPage + self.getNumberOfTextCharactersInPage()

    # number of whitespace characters in page
    # NOTE: only in text() of nodes, cause xPath can't count space in tags
    def getNumberOfWhitespaceCharactersInPage(self):
        # like in getNumberOfTextCharactersInPage()
        listOfTextNodesExceptScript = self.xmldata.xpath('//*[name() != \'script\']/text()')
        numberOfCharactersInPage = 0
        for item in listOfTextNodesExceptScript:
            numberOfCharactersInPage += len(item.replace(" ", ""))

        listOfInlineScriptTextNodes = self.xmldata.xpath('//script[not(@src)]/text()')
        for item in listOfInlineScriptTextNodes:
            # additional '|\s' for replacing spaces in one turn
            regExp = re.compile(r'(/\*[^\*/]*\*/|//.*\n?|\s)')
            numberOfCharactersInPage += len(re.sub(regExp, '', str(item.encode('utf-8'))))

        return numberOfCharactersInPage

    # print number of characters in the page
    def printNumberOfCharactersInPage(self):
        print("\nTotal number of text characters in page: " + str(self.getNumberOfTextCharactersInPage()))
        print("Total number of characters in page: " + str(self.getTotalNumberOfCharactersInPage()))
        print("Total number of whitespace characters in page: " + str(self.getNumberOfWhitespaceCharactersInPage()))
        print("Total length of page: " + str(len(self.pageReady)))

    # - the percentage of unknown tags (impossible, case xpath can't see unknown tags)
    # NOTE but we can count number of characters of unknown tags (getFileLength() - getAllChars())
    # NOTE it is impossible to count exact number of html-content in page without ending or leading whitespaces
    # cause xPath can't count spaces in tags like '</h1                           >' and even in
    # '<h1             >'
    # Moreover xPath sees tags out-of-root html-tag as children of another html-tag as child of root html-tag
    # i.e
    # xmldata.xpath('/*')  - selects list with one html-node
    # xmldata,xpath('/*')[0].xpath('./*') - selects list with head, body and html node (!) (even there is body-tag)
    # xmldata,xpath('/*')[0].xpath('./*')[2].xpath('./*') - selects list with body-tag which is after html tag
    # so we have to monitor presence of another "real" html-tag
    # i.e
    # <html>
    #   <tag1> ... </tag1>
    # </html>
    # <html>
    #   <tag2> ... </tag2>
    # </html>
    # in this case if second 'html'-tag doesn't exist xPath still sees it. But if it doesn't have any attributes it's
    # very likely doesn't exists. We can manage this fact subtracting length of "fake" 'html'-tag from total file length,
    # thus it is likely not work cause xPath can't manage spaces (fake html-tag as well, i.e <html            >)
    #
    # TODO for correct file length recognition count both str(len(pageReady) and getTotalNumberOfCharactersInPage()
    # result, then choose lesser one
    #
    def printNumberOfUnknownCharacters(self):
        print("Unknown tags, comments and unrecognized features length: " + str(len(self.pageReady) - self.getTotalNumberOfCharactersInPage()))
    #
    ###################################################################################################################

    # the percentage of unknown tags
    # unknown tags can be obtained via parsing %file_name% in XML format,
    # but it's difficult to make appropriate request (have to mention all known html tags);
    def getPercentageOfUnknownTags(self):
        if self.openedAsXML == False:
            print("\nObject not opened as XML, can't count percentage of unknown tags")
            return None

        try:
            listOfAllHTMLTagNames = self.configDict["html.all.tag.names"]
        except:
            print("\nNone list of under-head-tag elements, can't perform analysis")
            return None

        expressionForAllNonHTMLNodes = ''
        for tagName in listOfAllHTMLTagNames:
            expressionForAllNonHTMLNodes += 'name() != \'' + tagName + '\' and '
        expressionForAllNonHTMLNodes = re.sub(' and $', '', expressionForAllNonHTMLNodes)
        return float(self.xmldata.xpath('count(//*)') - self.xmldata.xpath('count(//*[%s])' % expressionForAllNonHTMLNodes)) / self.xmldata.xpath('count(//*)')

    def printPercentageOfUnknownTags(self):
        percentageOfUnknownTags = self.getPercentageOfUnknownTags()
        if percentageOfUnknownTags == None:
            print("\nImpossible to perform analysis (count percentage of unknown tags)")
            return

        print("\nPercentage of unknown tags: " + str(percentageOfUnknownTags) + "%")
    #
    ###################################################################################################################

    # number of elements whose source is on an external domain
    def getNumberOfElementsWithExternalDomainSource(self):
        # in case of file analyzing we can't say anything about domain URI
        if not str(self.uri).startswith('http'):
            return []
        srcAttributeValuesList = self.xmldata.xpath('//*[@src]/@src')
        uriPathTillTDL = str(self.uri).split('/')[0] + '//' + str(self.uri).split('/')[2]
        numberOfElementsWithExternalDomainSource = 0
        for item in srcAttributeValuesList:
            # assume that external domain sources not starts with:
            # 1. full site-path like 'http(s)://path-till-slash'
            # 2. dot (.) as begin of relative path
            # 2. slash (/) as begin of relative path
            if not str(item).startswith(uriPathTillTDL)\
                and not str(item).startswith('.')\
                and not str(item).startswith('/'):
                numberOfElementsWithExternalDomainSource += 1
        return [len(srcAttributeValuesList), numberOfElementsWithExternalDomainSource]

    def getExternalDomainToInternalDomainSourceElementsRatio(self):
        resultList = self.getNumberOfElementsWithExternalDomainSource()
        if resultList == []:
            return -1
        else:
            return float(resultList[1]) / resultList[0]

    def printNumberOfElementsWithExternalDomainSource(self):
        resultList = self.getNumberOfElementsWithExternalDomainSource()
        if resultList != []:
            print("\nNumber of elements with external domain source: "
                  + str(resultList[1]))
        else:
            print("\nFile analyzing - no URI information")

    def printExternalDomainToInternalDomainSourceElementsRatio(self):
        ratio = self.getExternalDomainToInternalDomainSourceElementsRatio()
        if ratio == -1:
            print("\nFile analyzing - no URI information")
        else:
            print("\nExternal domain to internal domain source elements ratio: " + str(ratio))
    #
    ###################################################################################################################

    # page hashing
    def getPageHashValues(self):
        pageHashSHA256 = hashlib.sha256(self.pageReady.encode('utf-8')).hexdigest()
        pageHashSHA512 = hashlib.sha512(self.pageReady.encode('utf-8')).hexdigest()

        return [pageHashSHA256, pageHashSHA512]

    def printPageHashValues(self):
        pageHashValues = self.getPageHashValues()
        print("\nPage hash (SHA-256): " + str(pageHashValues[0]))
        print("Page hash (SHA-512): " + str(pageHashValues[1]))
    #
    ###################################################################################################################

    # public functions for outer packages
    # print result of all functions via reflection with default values
    # NOTE: no order in function calls
    def printAll(self, xmldata, pageReady, uri):
        if xmldata is None or pageReady is None:
                print("Insufficient number of parameters")
                return
        self.setXMLData(xmldata)
        self.setPageReady(pageReady)
        self.uri = uri
        if str(uri).lower().endswith(".xml"):
            self.openedAsXML = True
        # FIXME remove in production
        #if(True):
        #    return
        print("\n\nhtml Analyser ----------------------")
        begin = timeit.default_timer()
        for funcName, funcValue in htmlAnalyzer.__dict__.items():
            if str(funcName).startswith("print") and callable(funcValue):
                try:
                    getattr(self, funcName)()
                except TypeError:
                    pass
        end = timeit.default_timer()
        print("\nElapsed time: " + str(end - begin) + " seconds")
        print("----------------------------------------")
    #
    ###################################################################################################################

    # @queue parameters is needed for multiprocessing
    def getTotalAll(self, xmldata, pageReady, uri, queue):
        if xmldata is None or pageReady is None:
                print("Insufficient number of parameters")
                return
        self.setXMLData(xmldata)
        self.setPageReady(pageReady)
        self.uri = uri
        resultDict = {}
        for funcName, funcValue in htmlAnalyzer.__dict__.items():
            if str(funcName).startswith("getTotal") and callable(funcValue):
                try:
                    resultDict[funcName] = getattr(self, funcName)()
                except TypeError:
                    pass
        queue.put([resultDict, htmlAnalyzer.__name__])
    #
    ###################################################################################################################

    def getAllAnalyzeReport(self, xmldata, pageReady, uri, queue):
        if xmldata is None or pageReady is None:
                print("Insufficient number of parameters")
                return
        self.setXMLData(xmldata)
        self.setPageReady(pageReady)
        self.uri = uri
        resultDict = {}
        for funcName, funcValue in htmlAnalyzer.__dict__.items():
            if funcName in self.listOfAnalyzeFunctions and callable(funcValue):
                try:
                    resultDict[funcName] = getattr(self, funcName)()
                except TypeError:
                    pass
        queue.put([resultDict, htmlAnalyzer.__name__])
        # TODO if in result dict value = 0 - do not insert it
    #
    ###################################################################################################################

    #TODO list
    # - &lt; and others characters in comparing strings (?)
    # - DTD 4.01 strict and others; take a look over every tag in wc3 site and add its restrictions in code

    # http://www.ibm.com/developerworks/ru/library/x-hiperfparse/