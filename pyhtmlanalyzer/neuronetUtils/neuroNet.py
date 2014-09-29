import logging
import os
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised import BackpropTrainer
from pybrain.tools.customxml import NetworkWriter, NetworkReader
from pybrain.tools.shortcuts import buildNetwork

__author__ = 'hokan'

# how to install scipy, that is needed for pybrain:
# http://stackoverflow.com/questions/7496547/python-scipy-needs-blas

# how to use pyBrain (in fact it's just copy-&-paste from documentation, but has fancy links in the bottom of page)
# http://habrahabr.ru/post/148407/
class neuroNet(object):
    __network = None
    __numberOfInputParameters = None
    __numberOfOutputParameters = None
    __numberOfInnerLayers = None

    # if "numberOfInputParameters" is None, we create simply stub of network
    def __init__(self, numberOfInputParameters = None, numberOfOutputParameters = 1, numberOfInnerLayers = None):
        self.createNetwork(numberOfInputParameters, numberOfOutputParameters, numberOfInnerLayers)

    def createNetwork(self, numberOfInputParameters, numberOfOutputParameters = 1, numberOfInnerLayers = None):
        self.__numberOfInputParameters = numberOfInputParameters
        self.__numberOfOutputParameters = numberOfOutputParameters
        self.__numberOfInnerLayers = numberOfInnerLayers

        if numberOfInnerLayers is None:
            # TODO manage this
            numberOfInnerLayers = 3#numberOfInputParameters + numberOfOutputParameters

        if numberOfInputParameters is not None:
            self.__network = buildNetwork(numberOfInputParameters, numberOfInnerLayers, numberOfOutputParameters)

    def saveNetworkToDirectory(self, networkName, directoryPath):
        try:
            if not os.path.exists(directoryPath):
                os.makedirs(directoryPath)
            NetworkWriter.writeToFile(self.__network, directoryPath + os.sep + ('%s.xml' % networkName))
            return True
        except Exception, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            return False

    def loadNetworkFromDirectory(self, networkName, directoryPath):
        try:
            self.__network = NetworkReader.readFrom(directoryPath + os.sep + ('%s.xml' % networkName))
            self.__numberOfInputParameters = self.__network.indim
            self.__numberOfOutputParameters = self.__network.outdim
            # TODO innerLayers count
            return True
        except Exception, error:
            logger = logging.getLogger(self.__class__.__name__)
            logger.exception(error)
            return False

    def getNumberOfInputParameters(self):
        return self.__numberOfInputParameters

    def getNumberOfOutputParameters(self):
        return self.__numberOfOutputParameters

    def getNumberOfInnerLayers(self):
        return self.__numberOfInnerLayers

    # dataList is list that consists of lists.
    # Each even element is input parameter and corresponding odd parameter is output parameter
    def trainNetworkWithDataList(self, dataList, numberOfEpochs = None):
        if len(dataList) % 2 != 0:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("Data input length (%s) is not equal data output length (%s). Abort training"
                         % (len(dataList) / 2 + 1, len(dataList) / 2))
            return

        dataInputLists = []
        dataOutputLists = []
        for i in xrange(0, len(dataList)):
            if i % 2 == 0:
                dataInputLists.append(dataList[i])
            else:
                dataOutputLists.append(dataList[i])

        return self.trainNetworkWithData(dataInputLists, dataOutputLists, numberOfEpochs)

    # returns error list for every training epoch
    # dataInputLists & dataOutputLists is lists of lists
    def trainNetworkWithData(self, dataInputLists, dataOutputLists, numberOfEpochs = None):
        if len(dataInputLists) != len(dataOutputLists):
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("Data input length (%s) is not equal data output length (%s). Abort training"
                         % (len(dataInputLists), len(dataOutputLists)))
            return

        if self.__network is None:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("No neuro-network created. Abort training")
            return

        dataSet = SupervisedDataSet(self.__numberOfInputParameters, self.__numberOfOutputParameters)

        # we cat use one iterator value, cause we already know that input and output data has same length
        for i in xrange(0, len(dataInputLists)):
            dataSet.addSample((dataInputLists[i]), (dataOutputLists[i]))

        # TODO enhance trainer selection
        trainer = BackpropTrainer(self.__network, dataSet)

        # train infinite if number of epochs is not a "number"
        if numberOfEpochs is None or not isinstance(numberOfEpochs, (int, long)):
            return trainer.trainUntilConvergence()
        else:
            trainer.trainEpochs(numberOfEpochs)
            return ("Training with (%s) ran, no output error values" % numberOfEpochs)

    def analyzeData(self, inputDataList):
        if self.__network is None:
            logger = logging.getLogger(self.__class__.__name__)
            logger.error("No neuro-network created. Abort data analysis")
            return

        return self.__network.activate(inputDataList)