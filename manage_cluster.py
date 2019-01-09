#!/usr/bin/env python

import argparse
import urllib2
import base64
import json
import ssl
import sys
from utilities.logger_util import get_module_logger
import logging
# from retrying import retry
import time
from ambari.ambari_api import *
from ambari.CONST import *
import httplib

logging.getLogger().setLevel("INFO")
## __name__ : the name of the module
logger =get_module_logger(__name__)


def set_service_to_state(cluster, accessor, service_name, desired_state):

    service_state = get_service_state(cluster, accessor, service_name)
    if service_state == desired_state:
        logger.info("service {0} state is already {1} , skipping  ".format(
            service_name, service_state))
        return
    elif service_state != "INSTALLED" and service_state != "STARTED":
        logger.info("service {0} state is {1} , skipping  ".format(
            service_name, service_state))
        return
    else:
        ###  when using APIs, you need to turn off maintenance mode on the component before you send stop or start requests to it.
        set_maintenance_mode(
            cluster, accessor, service_name, MAINTENANCE_MODE_OFF)
        logger.info("service {0} state is {1}".format(
            service_name, service_state))
        request_body = '{{ "RequestInfo": {{"context" :"set service {0} to {1} via REST"}},"Body": {{"ServiceInfo": {{"state": "{1}" }} }} }}'.format(
            service_name, desired_state)
        response_body = json.loads(accessor(SERVICE_URL.format(
            cluster, service_name), PUT_REQUEST_TYPE, request_body))
        request_id = response_body['Requests']['id']

        """
        TODO check that request is accepted before moving on
        """

        """
        TODO: replace retry by a derorateur backoff
        """

        tries = 0
        MAX_RETRIES = 6*2
        if service_name == "HIVE" and desired_state == "INSTALLED":
            # when having LLAP used, it may take up to 16min to start
            MAX_RETRIES = 16*2
        TIMEOUT = 30

        while True:
            request_status = get_request_status(cluster, accessor, request_id)
            logger.info("Request_type: set service {0} to state {1}, id_request {2}, status: {3}   ".format(
                service_name, desired_state, request_id, request_status))

            time.sleep(TIMEOUT)
            if request_status == "FAILED":
                break
            elif request_status != "COMPLETED" and tries < MAX_RETRIES:
                tries += 1
                continue
            else:
                break

        if request_status == "COMPLETED":
            logger.info("Request_type: set service {0} to state {1}, id_request {2}, status: {3}   ".format(
                service_name, desired_state, request_id, request_status))
        elif request_status == "FAILED":
            logger.error("Request_type: set service {0} to state {1}, id_request {2}, status: {3}   ".format(
                service_name, desired_state, request_id, request_status))
            raise Error
        elif tries == MAX_RETRIES:
            raise Error("TIMEOUT FAILED TO SET SERVICE {0} to state {1}".format(
                service_name, desired_state))
        else:
            logger.error("Request_type: set service {0} to {1}, id_request {2}, status: {3}   ".format(
                service_name, desired_state, request_id, request_status))
            raise Error

def start_all_services(cluster, accessor):
    """ the method follows this order in stooping hdp services
    https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.0/bk_HDP_Reference_Guide/content/stopping_hdp_services.html
    """
    logger.info("about to start all services of cluster {0}  ".format(cluster))
    list_services = list_all_services(cluster, accessor)

    flag=True
    for service_name in LIST_SERVICES[::-1]:
        if service_name in list_services:
            try:
                # start_service(cluster, accessor, service_name)
                set_service_to_state(
                    cluster, accessor, service_name, "STARTED")
            except Error as exc:
                message = "An exception of type {0} occurred. Arguments:\n{1!r}".format(type(exc).__name__, exc.args)
                logger.error(message)
                flag=False
                break

    if flag :
        logger.info("All services of cluster {0} started ".format(cluster))
    else :
        logger.error(
            "error starting all services of cluster {0} ".format(cluster))
        return 1

def stop_all_services(cluster, accessor):
    """ the method follows this order in stooping hdp services
    https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.0/bk_HDP_Reference_Guide/content/stopping_hdp_services.html"""
    logger.info("about to stop all services of cluster {0}  ".format(cluster))
    list_services = list_all_services(cluster, accessor)

    flag=True
    for service_name in LIST_SERVICES:
        if service_name in list_services:
            try:
                set_service_to_state(
                    cluster, accessor, service_name, "INSTALLED")
            except Error as exc:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(exc).__name__, exc.args)
                logger.error(message)
                flag=False
                break

    if flag :
        logger.info("All services of cluster {0} stopped ".format(cluster))
    else :
        logger.error(
            "error stopping all services of cluster {0} ".format(cluster))
        return 1

def main():

    parser = argparse.ArgumentParser()

    login_options_group = parser.add_argument_group('login_options_group')
    login_options_group.add_argument("-u", "--user", dest="user", default="admin",
                                    help="Optional user ID to use for authentication. Default is 'admin'")
    login_options_group.add_argument("-p", "--password", dest="password", default="admin",
                                    help="Optional password to use for authentication. Default is 'admin'")
    # login_options_group.add_argument("-e", "--credentials-file", dest="credentials_file",
    #                                help="Optional file with user credentials separated by new line.")

    parser.add_argument("-l", "--host", dest="host",
                        help="Server external host name")
    parser.add_argument("-t", "--port", dest="port", default="8080",
                        help="Optional port number for Ambari server. Default is '8080'. Provide empty string to not use port.")
    parser.add_argument("-s", "--protocol", dest="protocol", default="http",
                        help="Optional support of SSL. Default protocol is 'http'")
    parser.add_argument("--unsafe", action="store_true",
                        dest="unsafe", help="Skip SSL certificate verification.")
    parser.add_argument("-a", "--action", dest="action",
                        help="Script action: <stop>,<start>")
    parser.add_argument("-n", "--cluster", dest="cluster",
                        help="Name given to cluster. Ex: 'c1'")
    parser.add_argument("--log_level", dest="logLevel", choices=[
        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level")
    parser.add_argument("--http_debug", action="store_true", dest="http_debug", help="turn on http debug level")
    # will print a  namespace Object with the attributes
    args = parser.parse_args()
    if None in [args.action, args.host, args.cluster]:
        parser.error("One of required arguments is not passed")

    host = args.host
    port = args.port
    protocol = args.protocol
    cluster = args.cluster
    action = args.action
    user = args.user
    password = args.password
    #options without default value
    if args.logLevel:
        logging.getLogger().setLevel(args.logLevel)

    http_dbg_level=0
    if args.http_debug:
        http_dbg_level=1

    accessor = api_accessor(host, user, password,
                            protocol, port, http_debug_level=http_dbg_level)
    # logging_tree.printout()

    if action == START_CLUSTER:
        start_all_services(cluster, accessor)
        # start_service_V2(cluster,accessor,"YARN")
    elif action == STOP_CLUSTER:
        stop_all_services(cluster, accessor)
    else:
        parser.error(" invalid action arg, Script action: <stop>,<start> ")


if __name__ == "__main__":
  try:
    sys.exit(main())
  except (KeyboardInterrupt):
    print("\nAborting ... Keyboard Interrupt.")
    sys.exit(1)
