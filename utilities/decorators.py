# coding=utf-8

import time
import random
from logger_util import get_module_logger
import logging


logging.getLogger().setLevel("INFO")
## __name__ : the name of the module
logger = get_module_logger(__name__)


def retry_exp_backoff_on_predicate(max_times=5, cond=lambda: False):
    def decorator(func):
        metrics = {"nc": 0,     "_sleep_time": 2}

        def wrapper(*args, **kwargs):
            while True:
                request_status = func(*args, **kwargs)
                logger.info(
                    "Request id status: {0}   ".format(request_status))
                metrics['nc'] += 1
                # if request_status in ["ABORTED", "FAILED", "COMPLETED", "TIMEOUT"]:
                if cond(request_status) == True:
                    return
                else:
                    time.sleep(metrics['_sleep_time'])
                    if metrics['nc'] >= max_times:
                        return
                    metrics['_sleep_time'] = metrics['_sleep_time']*2

            return func(*args, **kwargs)

        return wrapper
    return decorator


# @retry_exp_backoff(3)
# @retry_exp_backoff_on_predicate(4, lambda x: x in REQUEST_FINAL_STATUS)
# def get_status(id):
#     list_status = REQUEST_FINAL_STATUS
#     list_status.extend([x * 2 for x in range(10)])
#     res = list_status[random.randint(0, len(list_status))]
#     print res
#     return res


# get_status(10)
