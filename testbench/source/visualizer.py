from matplotlib import pyplot as plt



#def _vizualize_metric(result):
#    for file, algorithms:


def visualize(result):
    restructured_results = {}

    for algorithm, file_results in result.items():
        for file, metrics in file_results.items():
            for metric, value in metrics.items():
                if metric not in restructured_results:
                    restructured_results[metric] = {}
                if file not in restructured_results[metric]:
                    restructured_results[metric][file] = {}
                restructured_results[metric][file][algorithm] = value

    result = restructured_results

    print(result)



    # metric
    #     file
    #         algorithm

