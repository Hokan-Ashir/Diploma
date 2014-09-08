import StringIO
import gzip
import logging
import lxml
import lxml.html
import os
import urllib2

__author__ = 'hokan'

class commonConnectionUtils:
    @staticmethod
    def openFile(filePath):
        try:
            file = open(filePath)
            pageReady = file.read().decode('utf-8')
        except:
            logger = logging.getLogger("commonConnectionUtils")
            logger.error("Cannot open file")
            print("Cannot open file")
            return []
        return [lxml.html.document_fromstring(pageReady), pageReady]

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
                print("Cannot open page - response code: " + str(page.code))
                return []

            if page.info().get('Content-Encoding') == 'gzip':
                buf = StringIO.StringIO(page.read())
                gzip_f = gzip.GzipFile(fileobj=buf)
                if page.headers.getparam('charset') is not None:
                    pageReady = gzip_f.read().decode(page.headers.getparam('charset'))
                else:
                    pageReady = gzip_f.read()
            else:
                if page.headers.getparam('charset') is not None:
                    pageReady = page.read().decode(page.headers.getparam('charset'))
                else:
                    pageReady = page.read()

        except urllib2.HTTPError, error:
            logger = logging.getLogger("commonConnectionUtils")
            logger.exception(error)
            print("Cannot open page - reason: " + str(error))
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
            pageReady = pageReady.encode('utf-8')
            xmldata = lxml.html.document_fromstring(pageReady)

        return [xmldata, pageReady]

    @staticmethod
    def openRelativeScriptObject(uri, filePath):
        # in case 'src=http://path-to-script'
        if str(filePath).startswith('http'):
            openedFile = commonConnectionUtils.openPage(filePath)
        # in case 'src=http://path-to-script'
        elif str(filePath).startswith('//'):
            openedFile = commonConnectionUtils.openPage('http:' + filePath)
        # in case of relative path to script
        else:
            # in case of file analyzing
            if not str(uri).startswith('http'):
                tmpPath = os.path.join(os.path.dirname(uri), filePath)
                openedFile = commonConnectionUtils.openFile(tmpPath)
            # in case of page analyzing
            else:
                # http(s): + // + path-to-TLD + path-to-script
                tmpPath = str(uri).split('/')[0] + '//' + str(uri).split('/')[2] + filePath
                openedFile = commonConnectionUtils.openPage(tmpPath)
        return openedFile