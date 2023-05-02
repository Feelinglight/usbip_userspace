from linecache import checkcache, getline
from collections import defaultdict
from typing import Iterable
from enum import IntEnum
from sys import exc_info
import traceback
import logging
import base64
import math
import time
import re


def exception_handler(a_exception):
    e_type, e_obj, e_tb = exc_info()
    frame = e_tb.tb_frame
    lineno = e_tb.tb_lineno
    filename = frame.f_code.co_filename
    checkcache(filename)
    line = getline(filename, lineno, frame.f_globals)
    return "Exception{0} in {1}\n"\
           "Line {2}: '{3}'\n"\
           "Message: {4}".format(type(a_exception), filename, lineno, line.strip(), a_exception)


def get_decorator(errors=(Exception, ), default_value=None, log_out_foo=print):
    def decorator(func):
        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                log_out_foo(traceback.format_exc())
                return default_value
        return new_func
    return decorator


exception_decorator = get_decorator(log_out_foo=logging.critical)
exception_decorator_print = get_decorator(log_out_foo=print)
assertion_decorator = get_decorator(errors=(AssertionError, ), log_out_foo=logging.critical)


class Timer:
    def __init__(self, a_interval_s: float):
        self.interval_s = a_interval_s
        self.start_time = 0
        self.stop_time = 0
        self.__started = False

    def start(self, a_interval_s=None):
        self.__started = True
        self.start_time = time.perf_counter()
        if a_interval_s is not None:
            self.interval_s = a_interval_s
        self.stop_time = self.start_time + self.interval_s

    def stop(self):
        self.start_time = 0
        self.stop_time = 0
        self.__started = False

    def check(self):
        if not self.__started:
            return False
        return time.perf_counter() > self.stop_time

    def started(self):
        return self.__started

    def time_passed(self):
        if not self.__started:
            return 0
        elif time.perf_counter() > self.stop_time:
            return self.interval_s
        else:
            return time.perf_counter() - self.start_time


class PerfTime:
    def __init__(self, threshold_s):
        self.threshold_s = threshold_s
        self.start_time = 0
        self.times = defaultdict(list)

    def start(self):
        self.start_time = time.perf_counter()

    def trace(self, trace_name):
        trace_time = time.perf_counter() - self.start_time
        if trace_time > self.threshold_s:
            self.times[trace_name].append(trace_time)
            print(trace_name, trace_time)

        self.start()

    def get_times(self):
        return self.times
