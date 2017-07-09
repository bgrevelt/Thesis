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
import gwf

class TestManager:
    def __init__(self):
        self.config = configuration()
        self.input_files = self.config.get_input_files()
        self.algorithms = []
        self.metrics = {}
        self.temporary_directory = './temp/'
        self.realtime = RealTimeEmulation()
        self.random_access_records = None

        self._load_algorithms()
        if not os.path.exists(self.temporary_directory):
            os.makedirs(self.temporary_directory)

    def run(self):
        for name, module, parameters in self.algorithms:
            module.init(parameters)

        for file in self.input_files:
            print('Starting on file {}'.format(file))
            meta_info = self._get_file_meta_data(file)
            print('Starting on file {} which contains {} records over {} seconds'.format(file, len(meta_info.ping_numbers), meta_info.timespan))
            # Get file meta data
            # Select records for random access decompression
            self._get_random_access_records(file, meta_info.ping_numbers, 10)
            for name, module, _ in self.algorithms:
                print('Algorithm {}'.format(name))

                # determine output file name and decompressed file name
                compressed_path, decompressed_path, real_time_compressed_path = self._get_temporary_file_names(file)

                # compress file meauring time
                print('Starting full file compression')
                compression_time = self._compress(module, file, compressed_path)
                compression_ratio = os.path.getsize(compressed_path) / os.path.getsize(file)

                # decompress file measuring time
                print('Starting full file decompression')
                decompression_time = self._decompress(module, compressed_path, decompressed_path)
                print('Checking for losslessness')
                lossless = filecmp.cmp(file, decompressed_path, False)

                # random access decompression
                random_access_decompression_time, random_access_lossless = self.random_access_compression(module,file, compressed_path)

                # real time stuff
                print('Starting real time compression')
                realtime_compression_time = self._compress_real_time(module, file, real_time_compressed_path)

                if name not in self.metrics:
                    self.metrics[name] = {}

                self.metrics[name][file] = {}
                self.metrics[name][file]['compression time'] = compression_time
                self.metrics[name][file]['decompression time'] = decompression_time
                self.metrics[name][file]['compression ratio'] = compression_ratio
                self.metrics[name][file]['lossless'] =  lossless
                self.metrics[name][file]['real time compression time'] =  realtime_compression_time
                self.metrics[name][file]['random access decompression time'] =  random_access_decompression_time
                self.metrics[name][file]['random access lossless'] =  random_access_lossless

        print(self.metrics)
        self._cleanup()

    def _compress(self, module, input_path, output_path):
        try:
            return timer.time_process(lambda : module.compress(input_path, output_path))
        except:
            print('compression failed')
            return 0

    def _decompress(self, module, input_path, output_path):
        try:
            return timer.time_process(lambda : module.decompress(input_path, output_path))
        except:
            print('decompression failed')
            return 0

    def _compress_real_time(self, module, input_path, output_path):
        available_cpu = int(self.config.get_metric_parameters('acquisition cpu available'))
        available_memory = int(self.config.get_metric_parameters('acquisition memory available'))
        return self.realtime.time(lambda : module.compress(input_path, output_path), time.perf_counter, available_cpu, available_memory)


    def random_access_compression(self, module, original_file, compressed_file):
        name = os.path.splitext(os.path.split(original_file)[1])[0]
        times = []
        lossless = []

        for record_id, (file_offset, size) in self.random_access_records.items():
            output_path = os.path.join(self.temporary_directory, name + '.ra_decompressed_{}'.format(record_id))
            times.append(timer.time_process(lambda : module.decompress(compressed_file, output_path, record_id)))

            # get the decompressed data
            with open(original_file, 'rb') as original, open(output_path, 'rb') as decompressed:
                decompressed_data = decompressed.read()
                original.seek(file_offset)
                original_data = original.read(size)
                lossless.append(decompressed_data == original_data)

                #print('file offset {}'.format(file_offset))
                #original_decoded = gwf.GenericWaterColumnPing.from_file(original)
                #decompressed_decoded = gwf.GenericWaterColumnPing.from_file(decompressed)

                #print('test bench. Record {} original {} decoded {}'.format(record_id, original_decoded.ping_number, decompressed_decoded.ping_number))

        print(lossless)

        return (numpy.average(times), all(lossless))


    def _get_temporary_file_names(self, orignial):
        name = os.path.splitext(os.path.split(orignial)[1])[0]
        compressed = os.path.join(self.temporary_directory, name + '.compressed')
        decompressed = os.path.join(self.temporary_directory, name + '.decompressed')
        compressed_rt = os.path.join(self.temporary_directory, name + '.compressed_rt')
        return (compressed, decompressed, compressed_rt)

    def _cleanup(self):
        shutil.rmtree(self.temporary_directory)

    def _load_algorithms(self):
        for algorithm in self.config.get_algorithms():
            path = self.config.get_algorithm_module_path(algorithm)
            base = os.path.split(path)[0]
            module = os.path.splitext(os.path.split(path)[1])[0]
            parameters = self.config.get_algorithm_parameters(algorithm)

            #TODO: REMOVE
            if not 'fake' in path.lower():
                sys.path.append(base)
                self.algorithms.append((algorithm, importlib.import_module(module), parameters))
                # TODO: we don't check if the proper methods exist in this module because that's not pythonic. Instead we should catch atribute errors when we try to call the function

    def _get_file_meta_data(self, file):
        meta_info = namedtuple('meta_info', 'timespan ping_numbers')
        gwf = gwf_file(file)
        record_info = [(wc.ping_number, wc.ping_time_seconds + (wc.ping_time_micro_seconds / 1E6)) for wc in gwf.read()]
        ping_numbers, generation_times = zip(*record_info)
        return meta_info(timespan = generation_times[len(generation_times) -1] - generation_times[0], ping_numbers = ping_numbers)

    def _get_random_access_records(self, file, records_in_file, number_of_records_to_select):
        records = random.sample(records_in_file, number_of_records_to_select)
        gwf = gwf_file(file)
        self.random_access_records = { wc.ping_number : (wc.file_offset, wc.size) for wc in gwf.read() if wc.ping_number in records}


# Very important to keep this line. The multiprocessing module will do all kinds of wonky stuuf if it is omitted
if __name__ == '__main__':
    manager = TestManager()
    manager.run()


