#!/usr/bin/env python

import urllib2
import base64
import json
import ssl
import sys
import logging
# from retrying import retry
import time
from CONST import *


## __name__ : the name of the module
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)



def api_accessor(host, login, password, protocol, port, unsafe=None):
    def do_request(api_url, request_type=GET_REQUEST_TYPE, request_body=''):
        try:
            url = '{0}://{1}:{2}{3}'.format(protocol, host, port, api_url)
            admin_auth = base64.encodestring(
                '%s:%s' % (login, password)).replace('\n', '')
            request = urllib2.Request(url)
            request.add_header('Authorization', 'Basic %s' % admin_auth)
            request.add_header('X-Requested-By', 'ambari')
            request.add_data(request_body)
            """urlib2  doesn't have a method to set the http method
            it uses the get_method method to pick the right http method
            the default get_method method return value is based on the data content
            here we override the get_method function to return the request type we want to have"""
            request.get_method = lambda: request_type

            ctx=None
            if unsafe:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

            httpHandler = urllib2.HTTPHandler()
            httpHandler.set_http_debuglevel(0)
            httpsHandler = urllib2.HTTPSHandler(ctx)
            #Instead of using urllib2.urlopen, create an opener, and pass the HTTPHandler
            #and any other handlers... to it.
            opener = urllib2.build_opener(httpHandler, httpsHandler)

            response = opener.open(request)
            response_body = response.read()
        except Exception as exc:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(exc).__name__, exc.args)
            logger.error(message)
            raise Exception(
                'Problem with accessing api. Reason: {0}'.format(exc))
        return response_body
    return do_request


def list_all_services(cluster, accessor):
    response = json.loads(
        accessor(SERVICES_URL.format(cluster), GET_REQUEST_TYPE))
    list_services = []
    for service in response['items']:
        list_services.append(service['ServiceInfo']["service_name"])
    return list_services


def get_service_state(cluster, accessor, service_name):
    response = accessor(SERVICE_URL.format(
        cluster, service_name), GET_REQUEST_TYPE)
    service_node = json.loads(response)
    return service_node['ServiceInfo']['state']


# def wait_service_to_get_started(func):
#     def wrapper(cluster, accessor, service_name):
#         tries = 0
#         MAX_RETRIES = 5
#         TIMEOUT = 40
#         service_state = None
#         while True:
#             is_started = func(cluster, accessor, service_name)
#             if is_started == False and tries < MAX_RETRIES:
#                 tries += 1
#                 time.sleep(TIMEOUT)
#                 continue
#             else:
#                 break
#         if service_state == "STARTED":
#                 logging.info(
#                     "Starting service {0} is successful ".format(service_name))
#         else:
#             raise Exception("TIMEOUT FAILED TO START SERVICE {0}".format(
#                 service_name))
#     return wrapper


# @wait_service_to_get_started
# def check_is_service_started(cluster, accessor, service_name):
#     return get_service_state(cluster, accessor, service_name) == "STARTED"



