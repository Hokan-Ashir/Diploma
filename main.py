#!/usr/bin/env/ python
# -*- coding: utf-8 -*-
import logging
import logging.config
from optparse import OptionParser
import sys
from pyhtmlanalyzer.commonFunctions import configNames
from pyhtmlanalyzer.commonFunctions.commonFunctions import commonFunctions
from pyhtmlanalyzer.pyHTMLAnalyzer import pyHTMLAnalyzer
from pyhtmlanalyzer.server.ConnectionServer import ConnectionServer

def parserCallback(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                  help="analyze urls from file")
    parser.add_option("-l", "--list", dest="list", type='string',
                  action='callback',
                  callback=parserCallback,
                  help="analyze urls from argument list separated by commas")
    parser.add_option("-g", "--generate",
                  action="store_true",
                  help="generate networks. WARNING: this option will cause database dropping")
    parser.add_option("-s", "--server", action="store_true",
                  help="start Twisted server")

    (options, args) = parser.parse_args()

    logging.config.fileConfig('logging.ini')
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logger = logging.getLogger("main")

    if options.server is None \
        and options.filename is None \
        and options.generate is None \
        and options.list is None:
        parser.print_help()
        sys.exit(1)

    analyzer = pyHTMLAnalyzer(configNames.configFileName)
    if options.server:
        server = ConnectionServer(analyzer)
        server.run()
    elif options.generate:
        analyzer.generateNetworks(configNames.configFileName)
    elif options.filename:
        analyzer.analyzePages(commonFunctions.getObjectNamesFromFile(args.filename))
    elif options.list:
        # commonFunctions.getObjectNamesFromFile('testDataSet/testDataSet_')
        # analyzer.analyzePages(['http://www.tutorialspoint.com/python/string_rstrip.htm'])
        analyzer.analyzePages(args.list)

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
