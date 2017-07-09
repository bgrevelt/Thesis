import time

def time_process(f):
    return timer(f, time.process_time)

def time_wall(f):
    return timer(f, time.perf_counter)

def timer(f, t):
    before = t()
    f()
    return t() - before

