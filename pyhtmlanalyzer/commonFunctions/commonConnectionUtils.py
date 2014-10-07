import StringIO
import chardet
import gzip
import logging
import lxml
import lxml.html
import os
import urllib2
import urlparse
from lxml.etree import ParserError
from pyhtmlanalyzer.full.commonAnalysisData import commonAnalysisData

__author__ = 'hokan'

class commonConnectionUtils:
    @staticmethod
    def openFile(filePath):
        isUtf8 = True
        try:
            file = open(filePath)
            pageReady = file.read().decode('utf-8')
        except UnicodeDecodeError, error:
            logger = logging.getLogger("commonConnectionUtils")
            logger.warning(filePath)
            logger.warning(error)
            try:
                pageReady = file.read()
                isUtf8 = False
            except Exception, error:
                logger = logging.getLogger("commonConnectionUtils")
                logger.error(filePath)
                logger.exception(error)
                return []

        return commonAnalysisData(lxml.html.document_fromstring(pageReady),
                                  pageReady,
                                  'utf-8' if isUtf8 else None)

    @staticmethod
    def openPage(url):
        page = None
        try:
            accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
            request = urllib2.Request(url)
            request.add_header('Accept', accept)
            request.add_header('User-Agent', user_agent)
            page = urllib2.urlopen(request)
            if (page.code != 200):
                logger = logging.getLogger("commonConnectionUtils")
                logger.error("Cannot open page (%s) - response code: %s" % (url, str(page.code)))
                return []

            if page.info().get('Content-Encoding') == 'gzip':
                buf = StringIO.StringIO(page.read())
                gzip_f = gzip.GzipFile(fileobj=buf)
                rawdata = gzip_f.read()
                encoding = chardet.detect(rawdata)
                pageReady = rawdata.decode(encoding['encoding'])
            else:
                rawdata = page.read()
                encoding = chardet.detect(rawdata)
                pageReady = rawdata.decode(encoding['encoding'])

        except UnicodeDecodeError:
            # try to decode encoding 'gb2312', usual for chinese sites. Also 'chardet' often not correctly detect
            # chinese encoding. So we try to decode data with 'gbk', regular for chinese hieroglyphs
            # inspired by:
            # http://stackoverflow.com/questions/4092606/python-beautifulsoup-html-parsing-handle-gbk-encoding-poorly-chinese-webscra
            try:
                if encoding['encoding'].lower() == 'gb2312':
                    pageReady = rawdata.decode('gbk')
                    encoding['encoding'] = 'gbk'
                else:
                    raise UnicodeDecodeError
            except UnicodeDecodeError, error:
                logger = logging.getLogger("commonConnectionUtils")
                logger.error(url)
                logger.exception(error)
                return []

        except Exception as error:
            logger = logging.getLogger("commonConnectionUtils")
            logger.error(url)
            logger.exception(error)
            return []

        if pageReady == "":
            logger = logging.getLogger("commonConnectionUtils")
            logger.warning("Empty file - " + str(url))
            return []

        try:
            xmldata = lxml.html.document_fromstring(pageReady)
        except ValueError, error:
            # in case "Unicode strings with encoding declaration are not supported." error
            # try to read page once more, but without decoding
            logger = logging.getLogger('commonConnectionUtils')
            logger.warning(error)
            # encode to utf-8 backwards
            pageReady = pageReady.encode(encoding['encoding'])
            xmldata = lxml.html.document_fromstring(pageReady)
        except ParserError, error:
            # "Document is empty" also catches here
            logger = logging.getLogger('commonConnectionUtils')
            logger.warning(error)
            return []

        return commonAnalysisData(xmldata,
                                  pageReady,
                                  encoding['encoding'])

    @staticmethod
    def openRelativeScriptObject(uri, filePath):
        # in case of page analyzing
        if uri.startswith('http'):
            tmpPath = urlparse.urljoin(uri, filePath)
            logger = logging.getLogger("openRelativeScriptObject")
            logger.info(tmpPath)
            openedFile = commonConnectionUtils.openPage(tmpPath)
        # in case of file analyzing
        else:
            tmpPath = os.path.join(os.path.dirname(uri), filePath)
            openedFile = commonConnectionUtils.openFile(tmpPath)

        return openedFile