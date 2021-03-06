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



MIN_PYTHON_VERSION = (2, 7)
used_python_version = (sys.version_info[0], sys.version_info[1])
if used_python_version < MIN_PYTHON_VERSION:
    print("This script requires Python version >= {0}.{1}").format(
        MIN_PYTHON_VERSION[0], MIN_PYTHON_VERSION[1])
    print ("You are using Python version {0}.{1}".format(
        used_python_version[0], used_python_version[1]))
    sys.exit(1)




def dry_run(cluster, accessor):
    """
    this dry-run checks if ambari-server is up and reachable
    print the URL
    """
    logger.info("check access to ambari")
    try:
        accessor("")
    except Exception :
        logger.error("check access to ambari: Failed")
        raise
    logger.info("check access to ambari: Succeded")


    logger.info("check access to cluster {0}".format(cluster))
    try:
        accessor(CLUSTERS_URL.format(cluster))
    except Exception:
        logger.error("check access to cluster {0}: Failed".format(cluster))
        raise
    logger.info("check access to cluster {0}: Succeded".format(cluster))

def set_service_to_state(cluster, accessor, service_name, desired_state):

    service_state = get_service_state(cluster, accessor, service_name)
    if service_state == "UNKNOWN":
        logger.error("service {0} state is {1}, aborting, please fix this before moving on".format(
            service_name, service_state))
        raise Error
    elif service_state == desired_state:
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
        # as of Ambari 2.6.2,and for each service, the timeouts on differents tasks are placed under
        # /var/lib/ambari-server/resources/common-services/<SERVICE_NAME>/0.12.0.2.0/metainfo.xml
        # Some tasks are not declared and don't have a timeout assigned, in this case the value of agent.task.tiemout param
        # under ambari-server properties is inherited
        request_status = get_request_status(cluster, accessor, request_id=request_id)

        if request_status == "COMPLETED":
            logger.info("Request_type: set service {0} to state {1}, id_request {2}, status: {3}   ".format(
                service_name, desired_state, request_id, request_status))
            if desired_state == "INSTALLED":
                        set_maintenance_mode(cluster, accessor, service_name, MAINTENANCE_MODE_ON)
                        # service_state = get_service_state(cluster, accessor, service_name)
        else:
            logger.error("Request_type: set service {0} to state {1}, id_request {2}, status: {3}   ".format(
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
    parser.add_argument("-a", "--action", dest="action", choices=['dry-run', 'stop', 'start'],
                        help="Script action: <dry-run>,<stop>,<start>")
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
    elif action == DRY_RUN:
        dry_run(cluster,accessor)
    else:
        parser.error(" invalid action arg ")


if __name__ == "__main__":
  try:
    sys.exit(main())
  except (KeyboardInterrupt):
    print("\nAborting ... Keyboard Interrupt.")
    sys.exit(1)
