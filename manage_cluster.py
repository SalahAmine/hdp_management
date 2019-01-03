#!/usr/bin/env python

import argparse
import urllib2
import base64
import json
import ssl
import sys
import logging
# from retrying import retry
import time
from ambari.ambari_api import *
from ambari.CONST import *


## __name__ : the name of the module
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start_all_services(cluster, accessor):
    """ the method follows this order in stooping hdp services
    https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.0/bk_HDP_Reference_Guide/content/stopping_hdp_services.html
    """
    logging.info("about to start all services of cluster {0}  ".format(cluster))
    list_services = list_all_services(cluster, accessor)

    flag=True
    for service_name in LIST_SERVICES[::-1]:
        if service_name in list_services:
            try:
                start_service(cluster, accessor, service_name)
            except Error as exc:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(exc).__name__, exc.args)
                logging.error(message)
                flag=False
                break

    if flag :
        logging.info("All services of cluster {0} started ".format(cluster))
    else :
        logging.error("error starting all services of cluster {0} ".format(cluster))
        return 1

def start_service(cluster, accessor, service_name):

    ###  when using APIs, you need to turn off maintenance mode on the component before you send stop or start requests to it.
    set_maintenance_mode(cluster, accessor, service_name, MAINTENANCE_MODE_OFF)

    service_state =get_service_state(cluster, accessor, service_name)

    if service_state == "STARTED" :
        logging.info("service {0} state is {1} , skipping  ".format(service_name, service_state))
        return
    elif service_state !="INSTALLED" :
        logging.info("service {0} state is {1} , skipping  ".format(service_name, service_state))
        return
    else :
        logging.info("service {0} state is {1} , starting  ".format(
            service_name, service_state))
        request_body = '{{ "RequestInfo": {{"context" :"Start service {0} via REST"}},"Body": {{"ServiceInfo": {{"state": "STARTED"}} }} }}'.format(service_name)
        accessor(SERVICE_URL.format(cluster, service_name), PUT_REQUEST_TYPE, request_body)

        """
        TODO: replace retry by a derorateur backoff
        """

        tries = 0
        MAX_RETRIES = 12
        TIMEOUT = 30
        service_state = None

        while True:
            time.sleep(TIMEOUT)
            service_state= get_service_state(cluster, accessor, service_name)
            logging.info("service {0} state is {1} ".format(
                service_name, service_state))
            if service_state != "STARTED" and tries < MAX_RETRIES:
                tries += 1
                continue
            else:
                break

        if service_state == "STARTED":
            logging.info("Starting service {0} is successful ".format(service_name))
        else:
            raise Error("TIMEOUT FAILED TO START SERVICE {0}".format(service_name))

def stop_all_services(cluster, accessor):
    """ the method follows this order in stooping hdp services
    https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.0/bk_HDP_Reference_Guide/content/stopping_hdp_services.html"""
    logging.info("about to stop all services of cluster {0}  ".format(cluster))
    list_services = list_all_services(cluster, accessor)

    flag=True
    for service_name in LIST_SERVICES:
        if service_name in list_services:
            try:
                stop_service(cluster, accessor, service_name)
            except Error as exc:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(exc).__name__, exc.args)
                logging.error(message)
                flag=False
                break

    if flag :
        logging.info("All services of cluster {0} stopped ".format(cluster))
    else :
        logging.error("error stopping all services of cluster {0} ".format(cluster))
        return 1

def stop_service(cluster, accessor, service_name):

    ###  when using APIs, you need to turn off maintenance mode on the component before you send stop or start requests to it.
    set_maintenance_mode(cluster, accessor, service_name, MAINTENANCE_MODE_OFF)

    service_state =get_service_state(cluster, accessor, service_name)

    if service_state == "INSTALLED" :
        logging.info("service {0} state is {1} , skipping  ".format(service_name, service_state))
        return
    elif service_state !="STARTED" :
        logging.info("service {0} state is {1} , skipping  ".format(service_name, service_state))
        return
    else :
        logging.info("service {0} state is {1} , stopping  ".format(
            service_name, service_state))
        request_body = '{{ "RequestInfo": {{"context" :"Stop service {0} via REST"}},"Body": {{"ServiceInfo": {{"state": "INSTALLED"}} }} }}'.format(
            service_name)
        accessor(SERVICE_URL.format(cluster, service_name), PUT_REQUEST_TYPE, request_body)

        """
        TODO: replace retry by a derorateur backoff
        """

        tries = 0
        MAX_RETRIES = 6
        TIMEOUT = 30
        service_state = None

        while True:
            time.sleep(TIMEOUT)
            service_state = get_service_state(cluster, accessor, service_name)
            logging.info("service {0} state is {1} ".format(
                service_name, service_state))
            if service_state != "INSTALLED" and tries < MAX_RETRIES:
                tries += 1
                continue
            else:
                break

        if service_state == "INSTALLED":
            logging.info("Stopping service {0} is successful ".format(service_name))
            set_maintenance_mode(cluster, accessor, service_name, MAINTENANCE_MODE_ON)
        else:
            raise Error("TIMEOUT FAILED TO STOP SERVICE {0}".format(
                service_name))


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


    accessor = api_accessor(host, user, password, protocol, port)
    if action == START_CLUSTER:
        start_all_services(cluster, accessor)
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

