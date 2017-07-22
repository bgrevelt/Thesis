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

    #del result['Real-time compression time']
    #del result['Random access decompression time']
    del result['Losslessness']

    number_of_plots = len(result)
    # width = math.ceil(math.sqrt(number_of_plots))
    # height = math.ceil(number_of_plots / width)
    # fig, xs = plt.subplots(nrows=height, ncols=width)
    # axes = [a for list_of_axes in xs for a in list_of_axes]

    print(result)
    for index, (metric, metric_results) in enumerate(result.items()):
        files, algorithms = zip(*metric_results.keys())
        files = list(set(files))
        algorithms = sorted(list(set(algorithms)))

        number_of_bar_groups = len(files)
        number_of_bars_per_group = len(algorithms)

        width = 1 / (number_of_bars_per_group + 1)
        pos = [[i + width * algorithm_index for i in range(number_of_bar_groups)] for algorithm_index in range(len(algorithms))]

        # Plotting the bars


        values = [[metric_results[(file, algorithms[algorithm_index])] for file in files] for algorithm_index in range(len(algorithms))]

        fig, ax = plt.subplots()

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
                    alpha=0.4,
                    # with color
                    color=colors[i],
                    # with label the first value in first_name
                    label=algorithms[i])

            for position,value in zip(pos[i], values[i]):
                ax.text(position - width/2, value, '{:.3g}'.format(value), color=colors[i])

        # Set the y axis label
        ax.set_ylabel(metric)

        # Set the chart's title
        ax.set_title(metric)

        #ax.tick_params(labelsize=5)

        # Set the position of the x ticks
        ticks = pos[len(pos) // 2]
        ax.set_xticks(ticks)

        xticks = ['{}...{}'.format(file.split('_')[0], file.split('_')[-1]) for file in files]
        # Set the labels for the x ticks
        ax.set_xticklabels(xticks)

        # use short labels for the files otherwise the graphs becomes unreadable / ugly
        # xticks = ['File {}'.format(i+1) for i in range(len(files))]

        # Setting the x-axis and y-axis limits
        #plt.xlim(min(pos)-width, max(pos)+width*4)
        #plt.ylim([0, max(df['pre_score'] + df['mid_score'] + df['post_score'])] )

        # Then add a box showing the relation between the label and the actual file
        # t = ['{} = {}'.format(xticks[i], files[i]) for i in range(len(files))]
        # props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        # # place a text box in upper left in axes coords
        # ax.text(0.05, 0.95, '\n'.join(t), transform=ax.transAxes, fontsize=14,
        #         verticalalignment='top', bbox=props)

        fig.canvas.set_window_title(metric)

        plt.tight_layout()
        # Adding the legend and showing the plot
        plt.legend()
        plt.grid()

    plt.show()
    quit()
        #

    # metric
    #     file
    #         algorithm

