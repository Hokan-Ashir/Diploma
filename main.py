#!/usr/bin/env/ python
# -*- coding: utf-8 -*-
import logging
import logging.config
import timeit
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.pyHTMLAnalyzer import pyHTMLAnalyzer

if __name__ == "__main__":
    logging.config.fileConfig('logging.ini')
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logger = logging.getLogger("main")
    totalBegin = timeit.default_timer()
    analyzer = pyHTMLAnalyzer(configNames.configFileName)

    #analyzer.printAnalyzedPageFeatures("http://www.tutorialspoint.com/python/string_split.htm")
    #dic = analyzer.getTotalNumberOfAnalyzedPageFeatures("http://www.tutorialspoint.com/python/string_split.htm")
    #listOfPages = ['http://www.tutorialspoint.com/python/string_split.htm', 'http://www.tutorialspoint
    # .com/python/string_rstrip.htm']
    #begin = timeit.default_timer()
    #dic = analyzer.getTotalNumberOfAnalyzedPagesFeatures(listOfPages)
    #end = timeit.default_timer()
    #logger.info("\nElapsed time: " + str(end - begin) + " seconds")
    #logger.info(dic.items())

    begin = timeit.default_timer()
    # http://www.tutorialspoint.com/python/string_rstrip.htm
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://habrahabr.ru/post/235949/')
    analyzer.analyzePages(['http://dark-world.ru/albums/Darkspace-Dark-Space-III-I.php'])
    #analyzer.analyzePages(['http://www.baidu.com'])
    #analyzer.setIsActiveModule('urlAnalyzer', False)
    #analyzer.analyzeFiles(['xmlFiles/test.htm'])
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://www.yandex.ru')
    end = timeit.default_timer()
    logger.info("Elapsed time: " + str(end - begin) + " seconds")

    # print all data via print and __repr__ class methods
    #connector = databaseConnector()
    #connector.printAllTablesData()

    '''begin = timeit.default_timer()
    dic = analyzer.getNumberOfAnalyzedHTMLFileFeaturesByFunction('xmlFiles/test.htm')
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://www.yandex.ru')
    analyzer.analyzeFiles(['xmlFiles/test.htm'])
    end = timeit.default_timer()
    logger.info("Elapsed time: " + str(end - begin) + " seconds")'''
    #logger.info(dic.items())
    #html = htmlAnalyzer.printPagesPercentageMismatch(commonConnectionUtils.openFile('xmlFiles/VLC.htm')[0],
    #                                                commonConnectionUtils.openFile('xmlFiles/VLC1.htm')[0])
    #plottingFunctions.plotArrayOfValues('test', [10, 20, 40], [100, 400, 300], 'xLabel', 'yLabel')
    #logger.info("sadf" + str(len(dic)))
    totalEnd = timeit.default_timer()
    logger.info("Total elapsed time: " + str(totalEnd - totalBegin) + " seconds")

    # TODO Global
    # - browser-plugin - must save malicious url for post-analysis, black/white-listing
    # - statistics-class so as example and graphics
    # - cashing
    # - optimizations
    # kinda class-variables for listOfAllStrings, listOfScriptFiles, listOfScriptNodes etc.
    # http://www.ibm.com/developerworks/ru/library/x-hiperfparse/

    # TODO ask
    # in <script> tags with @src attribute no embed script will be executed, is there a way to break this rule?

    # TODO known bugs:
    # 1.
    #   make lists of invalid and valid pages, no networks saved, run analysis, delete networks files, run analysis
    # again (DO NOT drop or clean database)
    #   result: data that you got from second analysis almost consists of dicts like {'id' : X}, which indicate that
    #           such object already exists in database
    #           so when it comes to networks creation you got error like
    #           "ValueError: cannot copy sequence with size 18 to array axis with dimension 1"
    #           that means your analysis data has less dimension that network input
    #
    #           it CAN be improved - we can obtain data from database for already existed objects, but for common sense
    #           it is not necessary - when no networks exists, we must clean up everything, analyze valid/invalid
    #           pages and ONLY THEN perform any other analysis. If any networks exists we DO NOT need to clean up
    #           anything and can perform analysis right from the start
    #
    #           shorter: no networks - recreate database, networks exists - DO NOT clean up database or recreate it
