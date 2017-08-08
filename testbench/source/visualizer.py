import matplotlib as mpl
from matplotlib import pyplot as plt
import os
import numpy as np
import math

#def _vizualize_metric(result):
#    for file, algorithms:


def visualize(result):
    restructured_results = {}

    for algorithm, file_results in result.items():
        for file, metrics in file_results.items():
            for metric, value in metrics.items():
                if metric not in restructured_results:
                    restructured_results[metric] = {}
                # if file not in restructured_results[metric]:
                #     restructured_results[metric][file] = {}
                restructured_results[metric][(os.path.split(file)[1],algorithm)] = value

    result = restructured_results
    if 'Losslessness' in result:
        del result['Losslessness']

    for index, (metric, metric_results) in enumerate(result.items()):
        files, algorithms = zip(*metric_results.keys())
        files = sorted(list(set(files)))
        algorithms = sorted(list(set(algorithms)))

        number_of_bar_groups = len(files)
        number_of_bars_per_group = len(algorithms)

        width = 1 / (number_of_bars_per_group + 1)
        pos = [[i + width * algorithm_index for i in range(number_of_bar_groups)] for algorithm_index in range(len(algorithms))]

        values = [[metric_results[(file, algorithms[algorithm_index])] for file in files] for algorithm_index in range(len(algorithms))]

        fig, ax = plt.subplots(figsize = (20,5))

        hsv = hsv = mpl.cm.get_cmap('Dark2')
        colors = hsv(np.linspace(0.1, 0.9, len(algorithms)))

        for i in range(len(algorithms)):
            # Create a bar with pre_score data,
            # in position pos,
            plt.bar(pos[i],
                    #using df['pre_score'] data,
                    values[i],
                    # of width
                    width,
                    # with alpha 0.5
                    alpha=0.7,
                    # with color
                    color=colors[i],
                    # with label the first value in first_name
                    label=algorithms[i])

            for position,value in zip(pos[i], values[i]):
                ax.text(position - width/2, value, '{:.3g}'.format(value), color=colors[i])

        if metric == "Cost":
            metric = "Cost reduction"

        # Set the y axis label
        ax.set_ylabel(metric)

        # Set the chart's title
        ax.set_title(metric)

        #ax.tick_params(labelsize=5)

        # Set the position of the x ticks
        ticks = pos[len(pos) // 2]
        ax.set_xticks(ticks)

        xticks = ['{}...{}'.format(file.split('_')[0], file.split('_')[-1]) if len(file) > 15 else file for file in files]
        # Set the labels for the x ticks
        ax.set_xticklabels(xticks)

        fig.canvas.set_window_title(metric)

        plt.tight_layout()
        # Adding the legend and showing the plot
        plt.legend()
        plt.grid()


    plt.show()

