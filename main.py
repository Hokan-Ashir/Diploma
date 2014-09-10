#!/usr/bin/env/ python
# -*- coding: utf-8 -*-
import logging
import timeit
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.pyHTMLAnalyzer import pyHTMLAnalyzer

if __name__ == "__main__":
    logging.basicConfig(filename='output.log', level=logging.DEBUG, filemode='w', format='\n%(levelname)s:%(name)s:%('
                                                                                          'message)s')
    analyzer = pyHTMLAnalyzer(configNames.configFileName)

    #analyzer.printAnalyzedPageFeatures("http://www.tutorialspoint.com/python/string_split.htm")
    #dic = analyzer.getTotalNumberOfAnalyzedPageFeatures("http://www.tutorialspoint.com/python/string_split.htm")
    #listOfPages = ['http://www.tutorialspoint.com/python/string_split.htm', 'http://www.tutorialspoint
    # .com/python/string_rstrip.htm']
    #begin = timeit.default_timer()
    #dic = analyzer.getTotalNumberOfAnalyzedPagesFeatures(listOfPages)
    #end = timeit.default_timer()
    #print("\nElapsed time: " + str(end - begin) + " seconds")
    #print(dic.items())

    begin = timeit.default_timer()
    # http://www.tutorialspoint.com/python/string_rstrip.htm
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://habrahabr.ru/post/235949/')
    analyzer.analyzePages(['http://dark-world.ru/albums/Darkspace-Dark-Space-III-I.php'])
    #analyzer.analyzePages(['http://www.baidu.com'])
    #analyzer.setIsActiveModule('urlAnalyzer', False)
    #analyzer.analyzeFiles(['xmlFiles/test.htm'])
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://www.yandex.ru')
    end = timeit.default_timer()
    print("\nElapsed time: " + str(end - begin) + " seconds")

    # print all data via print and __repr__ class methods
    #connector = databaseConnector()
    #connector.printAllTablesData()

    '''begin = timeit.default_timer()
    dic = analyzer.getNumberOfAnalyzedHTMLFileFeaturesByFunction('xmlFiles/test.htm')
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://www.yandex.ru')
    analyzer.analyzeFiles(['xmlFiles/test.htm'])
    end = timeit.default_timer()
    print("\nElapsed time: " + str(end - begin) + " seconds")'''
    #print(dic.items())
    #html = htmlAnalyzer.printPagesPercentageMismatch(commonConnectionUtils.openFile('xmlFiles/VLC.htm')[0],
    #                                                commonConnectionUtils.openFile('xmlFiles/VLC1.htm')[0])
    #plottingFunctions.plotArrayOfValues('test', [10, 20, 40], [100, 400, 300], 'xLabel', 'yLabel')
    #print("sadf" + str(len(dic)))

    # TODO Global
    # - sql-integration (DB-4-lab, postgres preferable)
    # - browser-plugin - must save malicious url for post-analysis, black/white-listing
    # - statistics-class so as example and graphics
    # - cashing
    # - optimizations
    # kinda class-variables for listOfAllStrings, listOfScriptFiles, listOfScriptNodes etc.
    # http://www.ibm.com/developerworks/ru/library/x-hiperfparse/

    # TODO ask
    # in <script> tags with @src attribute no embed script will be executed, is there a way to break this rule?