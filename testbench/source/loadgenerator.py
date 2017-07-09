from multiprocessing import Pool
from multiprocessing import cpu_count
import time

def spin_wait(dummy_arg):
    #let's spin in style and compute Fibonacci
    current = 1
    previous = 1
    while True:
        temp = current
        current += previous
        previous = temp

class CPU_load_generator:
    def __init__(self):
        self.number_of_logical_cores = cpu_count()
        self.loads = [ i * 100 / self.number_of_logical_cores for i in range(self.number_of_logical_cores+1)]
        self.pool = None

    def possible_loads(self):
        return self.loads

    def start(self, load):
        if load not in self.loads:
            raise ValueError

        if self.pool != None:
            raise ValueError

        number_of_cores_to_stress = int(load / (100 / self.number_of_logical_cores))

        if number_of_cores_to_stress > 0:
            self.pool = Pool(number_of_cores_to_stress)
            self.pool.map_async(spin_wait, [1] * number_of_cores_to_stress)
            time.sleep(3)

    def stop(self):
        if self.pool != None:
            self.pool.terminate()
            self.pool.join()
            self.pool.close()
            self.pool = None

    def __del__(self):
        self.stop()
