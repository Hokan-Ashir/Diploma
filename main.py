#!/usr/bin/env/ python
# -*- coding: utf-8 -*-
from multiprocessing import Process, Queue
import re
import timeit
from pyhtmlanalyzer.commonFunctions.commonConnectionUtils import commonConnectionUtils
from pyhtmlanalyzer.commonFunctions.plottingFunctions import plottingFunctions
from pyhtmlanalyzer.commonFunctions.processProxy import processProxy
from pyhtmlanalyzer.full.html.htmlAnalyzer import htmlAnalyzer
from pyhtmlanalyzer.pyHTMLAnalyzer import pyHTMLAnalyzer

class Foo:
    def bar(self, u, queue):
        d = {}
        print("Hello " + str(u))
        d[u] = 'hello' + str(u)
        print(Foo.__name__)
        queue.put(d)

if __name__ == "__main__":
    q = Queue()
    foo = Foo()
    u = 1
    p1 = processProxy(foo, [u, q], 'bar')
    p1.start()
    u = 2
    p2 = processProxy(foo, [u, q], 'bar')
    p2.start()
    p1.join()
    p2.join()
    l = [q.get(), q.get()]

    analyzer = pyHTMLAnalyzer("config")

    #analyzer.printAnalyzedPageFeatures("http://www.tutorialspoint.com/python/string_split.htm")
    #dic = analyzer.getTotalNumberOfAnalyzedPageFeatures("http://www.tutorialspoint.com/python/string_split.htm")
    #listOfPages = ['http://www.tutorialspoint.com/python/string_split.htm', 'http://www.tutorialspoint.com/python/string_rstrip.htm']
    #begin = timeit.default_timer()
    #dic = analyzer.getTotalNumberOfAnalyzedPagesFeatures(listOfPages)
    #end = timeit.default_timer()
    #print("\nElapsed time: " + str(end - begin) + " seconds")

    begin = timeit.default_timer()
    # TODO encoding, tested on yandex.ru
    #dic = analyzer.getTotalNumberOfAnalyzedPageFeatures(u'http://www.tutorialspoint.com/python/string_rstrip.htm')
    dic = analyzer.getNumberOfAnalyzedPageFeaturesByFunction('http://www.yandex.ru')
    end = timeit.default_timer()
    print("\nElapsed time: " + str(end - begin) + " seconds")
    #html = htmlAnalyzer.printPagesPercentageMismatch(commonConnectionUtils.openFile('xmlFiles/VLC.htm')[0],
    #                                                commonConnectionUtils.openFile('xmlFiles/VLC1.htm')[0])
    #plottingFunctions.plotArrayOfValues('test', [10, 20, 40], [100, 400, 300], 'xLabel', 'yLabel')
    #print("sadf" + str(len(dic)))

    # TODO Global
    # - sql-integration (DB-4-lab, postgres preferable)
    # - browser-plugin - must save malicious url for post-analysis, black/white-listing
    # - statistics-class so as example and graphics
    # - cashing
    # - multi-threading
    # - optimizations
    # kinda class-variables for listOfAllStrings, listOfScriptFiles, listOfScriptNodes etc.
    # http://www.ibm.com/developerworks/ru/library/x-hiperfparse/

    # TODO ask
    # in <script> tags with @src attribute no embed script will be executed, is there a way to break this rule?