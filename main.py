#!/usr/bin/env/ python
# -*- coding: utf-8 -*-
import logging
import timeit
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.modulesRegister import modulesRegister
from pyhtmlanalyzer.databaseUtils.databaseConnector import databaseConnector
from pyhtmlanalyzer.pyHTMLAnalyzer import pyHTMLAnalyzer

if __name__ == "__main__":
    logging.basicConfig(filename='log.log', level=logging.DEBUG, filemode='w', format='\n%(levelname)s:%(name)s:%('
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
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://www.tutorialspoint.com/python/string_rstrip.htm')
    #analyzer.analyzePages(['http://www.tutorialspoint.com/python/string_rstrip.htm'])
    analyzer.setIsActiveModule('urlAnalyzer', False)
    analyzer.analyzeFiles(['xmlFiles/test.htm'])
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://www.yandex.ru')
    end = timeit.default_timer()
    print("\nElapsed time: " + str(end - begin) + " seconds")

    # print all data via print and __repr__ class methods
    register = modulesRegister()
    connector = databaseConnector()
    for ORMClassName, ORMClass in register.getORMClassDictionary().items():
        print ORMClassName
        resultQuery = connector.select(ORMClass)
        for item in resultQuery:
            print item

    '''listOfHashes = []
    for value in (dic.values()[0]):
        listOfHashes.append([value[0], value[1]])

    listOfPageHashes = dic['htmlAnalyzer']['getPageHashValues']
    print(dic.items())

    analyzer.getModuleByName('scriptAnalyzer').setListOfHashes(listOfHashes)
    analyzer.getModuleByName('htmlAnalyzer').setListOfHashes(listOfPageHashes)'''

    begin = timeit.default_timer()
    dic = analyzer.getNumberOfAnalyzedHTMLFileFeaturesByFunction('xmlFiles/test.htm')
    #dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://www.yandex.ru')
    analyzer.analyzeFiles(['xmlFiles/test.htm'])
    end = timeit.default_timer()
    print("\nElapsed time: " + str(end - begin) + " seconds")
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