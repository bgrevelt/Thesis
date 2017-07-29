from configuration import configuration
from realtime import RealTimeEmulation
import importlib
import os
import sys
import timer
import filecmp
import shutil
import time
from gwf import File as gwf_file
from collections import namedtuple
import random
import numpy
import logging
import visualizer
import result_storage
import pandas
import command_line_parser

class TestManager:

    def __init__(self):
        self.config = configuration()
        self.input_files = self.config.get_input_files()
        self.algorithms = []
        self.metrics = {}
        self.temporary_directory = './temp/'
        self.results_file = 'results.sqlite'
        self.realtime = RealTimeEmulation()
        self.random_access_records = None
        self.clean_after_use = True
        self.check_for_losslelssness = False
        self.file_info = {}
        self.results = result_storage.StorageManager()
        self.options = command_line_parser.Parser()

        self.init_logging(logging.DEBUG if self.options.verbose() else logging.INFO)

        # some pandas settings to get printing of the table right
        pandas.set_option('display.height', 1000)
        pandas.set_option('display.max_rows', 500)
        pandas.set_option('display.max_columns', 500)
        pandas.set_option('display.width', 1000)

        self._load_algorithms()

    def recompute_derived(self):
        self._get_input_file_meta_info()

        self.metrics = self.results.fetch_most_recent()
        self._compute_derived_metrics()
        self._store_results()

    def display_last_results_table(self):
        table = self.results._get_most_recent_table()
        print(pandas.read_sql_query("SELECT * FROM '{}'".format(table), self.results.conn).to_string(index=False))

    def display_last_results_chart(self):
        self._get_input_file_meta_info()
        self.metrics = self.results.fetch_most_recent()
        self.normalize_metrics()
        visualizer.visualize(self.metrics)

    def run(self):
        if self.options.compute_metrics() or self.options.compute_derived_metrics() or self.options.normalize_results():
            self._get_input_file_meta_info()

        if self.options.compute_metrics():
            self._compute_metrics()
        else:
            self.metrics = self.results.fetch_most_recent()

        if self.options.compute_derived_metrics():
            self._compute_derived_metrics()

        if self.options.store():
            self._store_results()

        if self.options.normalize_results():
            self._normalize_metrics()

        if self.options.show_table():
            table = self.results._get_most_recent_table()
            print(pandas.read_sql_query("SELECT * FROM '{}'".format(table), self.results.conn).to_string(index=False))

        if self.options.show_graph():
            visualizer.visualize(self.metrics)


    def _get_input_file_meta_info(self):
        for file in self.input_files:
            meta_info = self._get_file_meta_data(file)
            self.file_info[file] = meta_info

    def _compute_metrics(self):
        if not os.path.exists(self.temporary_directory):
                os.makedirs(self.temporary_directory)

        # for name, module, parameters in self.algorithms:
        #     module.init(parameters)

        for file in self.input_files:
            logging.info('Starting on file {}'.format(file))
            meta_info = self.file_info[file]

            logging.info('Starting on file {} which contains {} records over {} seconds'.format(file, len(meta_info.ping_numbers), meta_info.timespan))

            # Get file meta data
            # Select records for random access decompression
            self._get_random_access_records(file, meta_info.ping_numbers, 10)
            for name, module, parameters in self.algorithms:
                logging.info('Algorithm {}'.format(name))

                module.init(parameters)

                # determine output file name and decompressed file name
                compressed_path, decompressed_path, real_time_compressed_path = self._get_temporary_file_names(file)

                # compress file meauring time
                logging.info('Starting full file compression')
                compression_time = self._compress(module, file, compressed_path)
                compression_ratio = os.path.getsize(compressed_path) / os.path.getsize(file)
                logging.info('Compression time {} seconds.'.format(compression_time))
                logging.info('Compression ratio {}'.format(compression_ratio))

                # decompress file measuring time
                logging.info('Starting full file decompression')
                decompression_time = self._decompress(module, compressed_path, decompressed_path)
                logging.info('Decompression time {} seconds.'.format(decompression_time))


                if self.check_for_losslelssness:
                    logging.info('Checking for losslessness')
                    lossless = filecmp.cmp(file, decompressed_path, False)
                else:
                    lossless = True

                # random access decompression
                logging.info('Starting random access decompression')
                random_access_decompression_time, random_access_lossless = self.random_access_compression(module,file, compressed_path)
                logging.info('Random access decompression time {} seconds.'.format(random_access_decompression_time))

                # real time stuff
                logging.info('Starting real time compression')
                realtime_compression_time = self._compress_real_time(module, file, real_time_compressed_path)
                logging.info('Real time compression time {} seconds.'.format(realtime_compression_time))

                if name not in self.metrics:
                    self.metrics[name] = {}

                metrics = {
                'Compression ratio' : compression_ratio,
                'Compression time' : compression_time,
                'Decompression time' : decompression_time,
                'Losslessness' : lossless and random_access_lossless,
                'Random access decompression time' : random_access_decompression_time,
                'Real-time compression time' : realtime_compression_time
                }

                self.metrics[name][file] = metrics

                if self.clean_after_use:
                    os.remove(compressed_path)
                    os.remove(decompressed_path)
                    os.remove(real_time_compressed_path)

        if self.clean_after_use:
            self._cleanup()


    def _compress(self, module, input_path, output_path):
        return timer.time_process(lambda : module.compress(input_path, output_path))


    def _decompress(self, module, input_path, output_path):
        return timer.time_process(lambda : module.decompress(input_path, output_path))


    def _compress_real_time(self, module, input_path, output_path):
        available_cpu = int(self.config.get_metric_parameters('acquisition cpu available'))
        available_memory = int(self.config.get_metric_parameters('acquisition memory available'))
        return self.realtime.time(lambda : module.compress(input_path, output_path), time.perf_counter, available_cpu, available_memory)


    def random_access_compression(self, module, original_file, compressed_file):
        name = os.path.splitext(os.path.split(original_file)[1])[0]
        times = []
        lossless = []

        print(len(self.random_access_records.items()))
        print(self.random_access_records.keys())

        for record_id, (file_offset, size) in self.random_access_records.items():
            output_path = os.path.join(self.temporary_directory, name + '.ra_decompressed_{}'.format(record_id))
            times.append(timer.time_process(lambda : module.decompress(compressed_file, output_path, record_id)))

            if self.check_for_losslelssness:
                # get the decompressed data
                with open(original_file, 'rb') as original, open(output_path, 'rb') as decompressed:
                    decompressed_data = decompressed.read()
                    original.seek(file_offset)
                    original_data = original.read(size)
                    lossless.append(decompressed_data == original_data)

            if self.clean_after_use:
                os.remove(output_path)

        return (numpy.average(times), all(lossless))


    def _get_temporary_file_names(self, orignial, algorithm_name):
        name = os.path.splitext(os.path.split(orignial)[1])[0]
        dir = os.path.join(self.temporary_directory, algorithm_name)
        if not os.path.exists(dir):
            os.makedirs(dir)
        compressed = os.path.join(dir, name + '.compressed')
        decompressed = os.path.join(dir, name + '.decompressed')
        compressed_rt = os.path.join(dir, name + '.compressed_rt')
        return (compressed, decompressed, compressed_rt)

    def _cleanup(self):
        shutil.rmtree(self.temporary_directory)

    def _load_algorithms(self):
        for algorithm in self.config.get_algorithms():
            path = self.config.get_algorithm_module_path(algorithm)
            base = os.path.split(path)[0]
            module = os.path.splitext(os.path.split(path)[1])[0]
            parameters = self.config.get_algorithm_parameters(algorithm)

            sys.path.append(base)
            self.algorithms.append((algorithm, importlib.import_module(module), parameters))

    def _get_file_meta_data(self, file):
        logging.info('Reading input file meta data for file {}'.format(file))
        meta_info = namedtuple('meta_info', 'timespan ping_numbers path size')
        gwf = gwf_file(file)
        record_info = [(wc.ping_number, wc.ping_time_seconds + (wc.ping_time_micro_seconds / 1E6)) for wc in gwf.read()]
        ping_numbers, generation_times = zip(*record_info)
        size = os.path.getsize(file)
        return meta_info(timespan = generation_times[len(generation_times) -1] - generation_times[0], ping_numbers = ping_numbers, path=file, size=size)

    def _get_random_access_records(self, file, records_in_file, number_of_records_to_select):
        records = random.sample(records_in_file, number_of_records_to_select)
        gwf = gwf_file(file)
        self.random_access_records = { wc.ping_number : (wc.file_offset, wc.size) for wc in gwf.read() if wc.ping_number in records}

    def _compute_derived_metrics(self):
        algorithms = self.metrics.keys()
        files = set(file for algorithm in self.metrics.values() for file in algorithm.keys())

        logging.debug('Started computing derived metrics')
        for algorithm in algorithms:
            logging.debug('Algorithm: {}'.format(algorithm))
            for file in files:
                logging.debug('\tFile: {}'.format(file))
                if file in self.metrics[algorithm]:

                    file_meta_info = self.file_info[file]
                    compression_ratio = self.metrics[algorithm][file]['Compression ratio']
                    compression_time = self.metrics[algorithm][file]['Compression time']
                    decompression_time = self.metrics[algorithm][file]['Decompression time']
                    ra_decompression_time = self.metrics[algorithm][file]['Random access decompression time']
                    real_time_compression_time = self.metrics[algorithm][file]['Real-time compression time']
                    real_time_metric = self._computeRealTimeMetric(file_meta_info, real_time_compression_time)
                    processing_metric = self._computeProcessingMetric(file_meta_info, decompression_time, ra_decompression_time)
                    cost_metric = self._computeCostMetric(file_meta_info, compression_ratio, compression_time, real_time_metric, processing_metric)

                    self.metrics[algorithm][file]['Real-time'] = real_time_metric
                    self.metrics[algorithm][file]['Processing'] = processing_metric
                    self.metrics[algorithm][file]['Cost'] = cost_metric

    def _computeRealTimeMetric(self, file_meta_info, real_time_compression_time):
        number_of_records_in_file = len(file_meta_info.ping_numbers)
        file_timespan = file_meta_info.timespan
        average_wc_generation_time = file_timespan / (number_of_records_in_file - 1)
        average_wc_compression_time = real_time_compression_time / number_of_records_in_file
        real_time_metric = average_wc_generation_time / average_wc_compression_time
        return real_time_metric
        pass

    def _computeProcessingMetric(self, file_meta_info, decompression_time, random_access_decompression_time):
        logging.debug('\t\tStarted computing processing metric')
        number_of_decompressions = self.config.get_metric_parameters('number of processing decompressions')
        decompression_ratio = self.config.get_metric_parameters('Processing ratio')
        logging.debug('\t\t\tNumber of decompressions: {}. Decompression ratio: {}'.format(number_of_decompressions, decompression_ratio))
        full_decompression_time = decompression_time
        number_of_records_in_file = len(file_meta_info.ping_numbers)
        partial_decompression_time = number_of_records_in_file * decompression_ratio * random_access_decompression_time
        logging.debug('\t\t\tPartial decompression time = <number of records in file> * <decompression ration> * <random access decopression time> = {} * {} * {} = {}'.format(number_of_records_in_file, decompression_ratio, random_access_decompression_time, partial_decompression_time))
        processing_decompression_time = min(full_decompression_time, partial_decompression_time)
        logging.debug('\t\t\tProcessing decompressin time = min(<full file decompression time>, <partial decompression time>) = min({}, {}) = {}'.format(full_decompression_time, partial_decompression_time, processing_decompression_time))
        processing_metric = number_of_decompressions * processing_decompression_time
        logging.debug('\t\t\tProcessing metric = <number of decompressions> * <processing decompression time> = {} * {} = {}'.format(number_of_decompressions, processing_decompression_time, processing_metric))
        return processing_metric

    def _computeCostMetric(self, file_meta_info, compression_ratio, compression_time, real_time_metric, processing_metric):
        logging.debug('\t\tStarted computing cost metric')
        cost_of_ship_time = self.config.get_metric_parameters('cost of ship time')
        logging.debug('\t\t\tCost of ship time: {}'.format(cost_of_ship_time))
        compression_time_hours = compression_time / 3600
        cost_of_compression = cost_of_ship_time * compression_time_hours if real_time_metric < 1 else 0
        logging.debug('\t\t\tReal time metric: {}'.format(real_time_metric))
        logging.debug('\t\t\tCost of compression: {}'.format(cost_of_compression))

        cost_of_processing_time = self.config.get_metric_parameters('cost of processing time')
        processing_time_hours = processing_metric / 3600
        cost_of_decompression = processing_time_hours * cost_of_processing_time
        logging.debug('\t\t\tCost of decompression = <processing time> * <cost of processing time> ='
                     '{} * {} = {}'.format(processing_time_hours, cost_of_processing_time, cost_of_decompression))

        size_in_mb = file_meta_info.size / (1024**2)
        data_reduction = size_in_mb * (1 - compression_ratio)
        logging.debug('\t\t\tData redcution = <file size> * (1- <compression ratio> ='
                     '{} * (1 - {}) = {}'.format(size_in_mb, compression_ratio, data_reduction))

        cost_of_data_ownership = self.config.get_metric_parameters('cost of data ownership')
        cost_of_ownership_reduction = data_reduction * cost_of_data_ownership
        logging.debug('\t\t\tReduction in cost of ownership = <data reduction> * <cost of ownership> ='
                     '{} * {} = {}'.format(data_reduction, cost_of_data_ownership, cost_of_ownership_reduction))

        cost_metric = cost_of_ownership_reduction - cost_of_compression - cost_of_decompression
        logging.debug('\t\t\tCost metric = <Reduction in cost of ownership> - <cost of compression> - <cost of decompression> ='
                     '{} - {} - {} = {}'.format(cost_of_ownership_reduction, cost_of_compression, cost_of_decompression, cost_metric))

        return cost_metric

    def _store_results(self):
         self.results.store(self.metrics)


    def _normalize_metrics(self):
        algorithms = self.metrics.keys()
        files = set(file for algorithm in self.metrics.values() for file in algorithm.keys())
        for algorithm in algorithms:
            for file in files:
                if file in self.metrics[algorithm]:
                    file_size = self.file_info[file].size
                    avg_record_size = self.file_info[file].size / len(self.file_info[file].ping_numbers)
                    self.metrics[algorithm][file]['Compression time (seconds per byte)'] = self.metrics[algorithm][file]['Compression time'] / file_size
                    self.metrics[algorithm][file]['Decompression time (seconds per byte)'] = self.metrics[algorithm][file]['Decompression time'] / file_size
                    self.metrics[algorithm][file]['Random access decompression (seconds per byte)'] = self.metrics[algorithm][file]['Random access decompression time'] / (avg_record_size)
                    self.metrics[algorithm][file]['Real-time compression time (seconds per byte)'] = self.metrics[algorithm][file]['Real-time compression time'] / file_size

        #del self.metrics[algorithm][file]['Compression time']
        #del self.metrics[algorithm][file]['Decompression time']
        #del self.metrics[algorithm][file]['Random access decompression time']
        #del self.metrics[algorithm][file]['Real-time compression time']

    def init_logging(self, level):
        logging.basicConfig(filename='testbench_run.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', filemode='w')
        rootLogger = logging.getLogger()
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(level)
        rootLogger.addHandler(consoleHandler)

# Very important to keep this line. The multiprocessing module will do all kinds of wonky stuuf if it is omitted
if __name__ == '__main__':
    manager = TestManager()
    manager.run()

