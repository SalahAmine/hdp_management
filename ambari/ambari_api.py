#!/usr/bin/env python
import httplib
import urllib2
import base64
import json
import ssl
import sys
from utilities.logger_util import get_module_logger
# from retrying import retry
import time
from CONST import *
from utilities.decorators import *

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

## __name__ : the name of the module
logger = get_module_logger(__name__)


def api_accessor(host, login, password, protocol, port, unsafe=None, http_debug_level=0):
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
            httpHandler.set_http_debuglevel(http_debug_level)
            httpsHandler = urllib2.HTTPSHandler(ctx)
            #Instead of using urllib2.urlopen, create an opener, and pass the HTTPHandler
            #and any other handlers... to it.
            opener = urllib2.build_opener(
                httpHandler, httpsHandler)

            # proxyHandler = urllib2.ProxyHandler({
            #     'http': '127.0.0.1:8099',
            #     'https': '127.0.0.1:8099'
            # })
            # opener.add_handler(proxyHandler)

            urllib2.install_opener(opener)

            response = opener.open(request)
            response_body= response.read()

        except urllib2.HTTPError, e:
            logger.debug(e.read())
            raise
        except urllib2.URLError:
            raise
        except httplib.HTTPException:
            raise
        except Exception:
            raise
        else:
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


def get_maintenance_mode(cluster, accessor, service_name):
    response = accessor(SERVICE_URL.format(
        cluster, service_name), GET_REQUEST_TYPE)
    service_node = json.loads(response)
    return service_node['ServiceInfo']['maintenance_state']


# @retry_exp_backoff_on_predicate(lambda x: x in REQUEST_POSSIBLE_FINAL_STATUSES)
@retry_const_backoff_on_predicate(predicate=lambda x: x in REQUEST_POSSIBLE_FINAL_STATUSES)
def get_request_status(cluster, accessor, request_id=0):
    response = json.loads(
            accessor(REQUEST_URL.format(cluster, request_id), GET_REQUEST_TYPE))
    return response['Requests']['request_status']


def set_maintenance_mode(cluster, accessor, service_name, desired_mode):
    logger.debug("about to set service {0} to maintenance mode {1}".format(
            service_name, desired_mode))

    if desired_mode not in [MAINTENANCE_MODE_ON, MAINTENANCE_MODE_OFF]:
        raise Error("maintenance mode must be either {0} or {1}".format(
            MAINTENANCE_MODE_ON, MAINTENANCE_MODE_OFF))

    maintenance_mode = get_maintenance_mode(cluster, accessor, service_name)
    if desired_mode == maintenance_mode:
        logger.debug("service {0} maintenance mode is already {1} , skipping  ".format(
            service_name, desired_mode))
        return

    request_body = '{{"RequestInfo":{{"context":"Turn On Maintenance Mode for {0} }}"}},"Body":{{"ServiceInfo":{{"maintenance_state":"{1}" }} }} }}'.format(
        service_name, desired_mode)
    accessor(SERVICE_URL.format(cluster, service_name),
             PUT_REQUEST_TYPE, request_body)

    """
    TODO: replace retry by a derorateur backoff
    """

    tries = 0
    MAX_RETRIES = 4
    TIMEOUT = 15
    maintenance_mode = None

    while True:
        time.sleep(TIMEOUT)
        maintenance_mode = get_maintenance_mode(
            cluster, accessor, service_name)
        if maintenance_mode != desired_mode and tries < MAX_RETRIES:
            logger.debug("service {0} maintenance mode is {1} ".format(
                service_name, maintenance_mode))
            tries += 1
            continue
        else:
            break

    if maintenance_mode == desired_mode:
        logger.debug("Setting maintenance mode for service {0} to {1} is successful".format(service_name, desired_mode))
    else:
        logger.error(("SETTING MAINTENANCE MODE FOR SERVICE {0} to {1} is failed ".format(
                service_name, desired_mode)))
        raise Error
