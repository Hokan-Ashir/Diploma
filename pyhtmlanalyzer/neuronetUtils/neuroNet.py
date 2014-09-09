import logging
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised import BackpropTrainer
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

    def __init__(self, numberOfInputParameters, numberOfOutputParameters = 1, numberOfInnerLayers = None):

        if numberOfInnerLayers is None:
            # TODO manage this
            numberOfInnerLayers = 3#numberOfInputParameters + numberOfOutputParameters

        self.__network = buildNetwork(numberOfInputParameters, numberOfInnerLayers, numberOfOutputParameters)
        self.__numberOfInputParameters = numberOfInputParameters
        self.__numberOfOutputParameters = numberOfOutputParameters
        self.__numberOfInnerLayers = numberOfInnerLayers

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