import matplotlib.pyplot as plt

__author__ = 'hokan'

class plottingFunctions:
    def __init__(self):
        pass

    @staticmethod
    def plotArrayOfValues(plotName, xValues, yValues, xLabel, yLabel):
        fig = plt.figure()
        ax = plt.subplot(111)
        # Create the plot
        ax.plot(xValues, yValues, label=plotName)
        ax.set_xlabel(xLabel)
        ax.set_ylabel(yLabel)

        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                         box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10),
                  fancybox=True, shadow=True, ncol=5)

        # Save the figure in a separate file
        plt.savefig('%s.png' % plotName)

        # Draw the plot to the screen
        #plt.show()