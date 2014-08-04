import matplotlib.pyplot as plt

__author__ = 'hokan'

class plottingFunctions:
    def __init__(self):
        pass

    @staticmethod
    def plotArrayOfValues(plotName, xValues, yValues, xLabel, yLabel):
        # Create the plot
        plt.plot(xValues, yValues)
        plt.xlabel(xLabel)
        plt.ylabel(yLabel)

        # Save the figure in a separate file
        plt.savefig('%s.png' % plotName)

        # Draw the plot to the screen
        #plt.show()