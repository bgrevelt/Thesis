import numpy as np
import psutil
import time
from loadgenerator import CPU_load_generator

class RealTimeEmulation:
    def __init__(self):
        self.number_of_logical_cores = None
        self.load_generator = CPU_load_generator()
        self.allocated_memory = None
        pass

    def time(self, function, timer_function, available_cpu, available_memory):
        if available_cpu < 0 or available_cpu > 100:
            raise ValueError

        if available_memory < 0:
            raise ValueError

        time.sleep(1)
        current_cpu_load = self._get_current_cpu_load()

        self._claim_memory(available_memory)

        required_additional_load = 100 - available_cpu - current_cpu_load

        lower_load, upper_load = self._get_load_bounds(required_additional_load)

        print('Starting lower bound: {}%'.format(lower_load))
        lower_time = self._time_under_cpu_load(function, timer_function, lower_load)
        if lower_load == upper_load:
            return lower_time

        print('Starting upper bound: {}%'.format(upper_load))
        upper_time = self._time_under_cpu_load(function, timer_function, upper_load)

        print('Interpolating to {} from using {} and {}'.format(required_additional_load, lower_time, upper_time))

        self._release_claimed_memory()

        return np.interp(required_additional_load, [lower_load, upper_load], [lower_time, upper_time])

    def _get_current_cpu_load(self):
        time.sleep(1)
        return psutil.cpu_percent(3)

    def _claim_memory(self, requested_available_meory):
        requested_available_meory = requested_available_meory * 1024**2
        available_memory = psutil.virtual_memory().available
        to_allocate = available_memory - requested_available_meory
        if to_allocate <= 0:
            #TODO: log
            return

        self.allocated_memory = bytearray(to_allocate)
        pass

    def _release_claimed_memory(self):
        self.allocated_memory = None

    def _time_under_cpu_load(self, function, timer_function, load):
        self.load_generator.start(load)
        time = self._time_function(function, timer_function)
        self.load_generator.stop()
        return time

    def _time_function(self, function, timer_function):
        start = timer_function()
        function()
        return timer_function() - start

    def _get_load_bounds(self, load):
        start_load = None
        end_load = None

        if load < 0:
            load = 0

        possible_loads = self.load_generator.possible_loads()

        for s, e in [(possible_loads[i], possible_loads[i+1]) for i in range(len(possible_loads)-1)]:
            if s == load:
                start_load = s
                end_load = start_load
                break
            elif e == load:
                start_load = s
                end_load = start_load
                break
            elif s < load and e > load:
                start_load = s
                end_load = e
                break

        assert start_load != None and end_load != None

        return (start_load, end_load)
