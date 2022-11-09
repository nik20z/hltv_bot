import time

def no_except(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return
    return wrapper


def time_of_function(func):
    def wrapped(*args, **kwargs):
        start_time = time.perf_counter_ns()
        res = func(*args, **kwargs)
        print(f"{func.__name__} {(time.perf_counter_ns() - start_time)/10**9}")
        return res
    return wrapped
