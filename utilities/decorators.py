# coding=utf-8

import time
import random
from logger_util import get_module_logger
import logging

# import sys
# print(sys.path)

logging.getLogger().setLevel("INFO")
## __name__ : the name of the module
logger = get_module_logger(__name__)


REQUEST_POSSIBLE_FINAL_STATUSES = ["ABORTED", "FAILED", "COMPLETED", "TIMEOUT"]

def retry_exp_backoff_on_predicate(cond=lambda: False):
    def decorator(func):
        metrics = {"nc": 0, "_sleep_time": 2}

        def wrapper(*args, **kwargs):
            while True:
                request_status = func(*args, **kwargs)
                logger.info(
                    "Request id {0} status: {1}   ".format(kwargs['request_id'], request_status))
                metrics['nc'] += 1
                # if request_status in ["ABORTED", "FAILED", "COMPLETED", "TIMEOUT"]:
                if cond(request_status) == True:
                    return
                else:
                    time.sleep(metrics['_sleep_time'])
                    metrics['_sleep_time'] = metrics['_sleep_time']*2
            return func(*args, **kwargs)

        return wrapper
    return decorator




# # @retry_exp_backoff(3)
# @retry_exp_backoff_on_predicate(4, lambda x: x in REQUEST_POSSIBLE_FINAL_STATUSES)
# def get_status(request_id):
#     list_status = list(REQUEST_POSSIBLE_FINAL_STATUSES)
#     list_status.extend([x * 2 for x in range(100)])
#     res = list_status[random.randint(0, len(list_status))]
#     print res
#     return res


# get_status(10)


def retry_const_backoff_on_predicate(backoff=15, predicate=lambda: False):
    def decorator(func):
        metrics = {"nc": 0, "_sleep_time": backoff}

        def wrapper(*args, **kwargs):
            while True:
                request_status = func(*args, **kwargs)
                logger.info(
                    "Request id {0} status: {1}   ".format(kwargs['request_id'], request_status))
                metrics['nc'] += 1
                # if request_status in ["ABORTED", "FAILED", "COMPLETED", "TIMEOUT"]:
                if predicate(request_status) == True:
                    return request_status
                else:
                    time.sleep(metrics['_sleep_time'])
            #return func(*args, **kwargs)

        return wrapper
    return decorator
