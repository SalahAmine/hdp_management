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

# print(sys.path)

logging.getLogger().setLevel("INFO")
## __name__ : the name of the module
logger = get_module_logger(__name__)


def service_check_gen_payload(service_name):
    command=service_name
    if service_name == "ZOOKEEPER":
        # https://community.hortonworks.com/articles/11852/ambari-api-run-all-service-checks-bulk.html
        command = "ZOOKEEPER_QUORUM"
    service_check_payload = {
            "RequestInfo": {
                "context": "{0} Service Check via REST".format(service_name),
                "command": "{0}_SERVICE_CHECK".format(command)
            },
            "Requests/resource_filters": [
                {
                    "service_name": "{0}".format(service_name)
                }
            ]
    }
    return json.dumps(service_check_payload)

def run_service_check(cluster,accessor,service_name):
    """
    return : returns the service_check result final status which could be in  ["ABORTED","FAILED","COMPLETED","TIMEOUT"]
    """

    logger.info("about to run service_check on service {0}  ".format(service_name))
    payload = service_check_gen_payload(service_name)
    response_body = json.loads(accessor(REQUESTS_URL.format(
        cluster), POST_REQUEST_TYPE, payload))
    request_id = response_body['Requests']['id']
    request_status= get_request_status(cluster, accessor, request_id=request_id)
    return request_status

def run_all_service_check(cluster, accessor):
    list_services = list_all_services(cluster,accessor)
    for service_name in LIST_SERVICES[::-1]:
        if service_name in list_services:
                request_status = run_service_check(cluster, accessor, service_name)
                if request_status in ["ABORTED", "FAILED"]:
                    logger.error("Request_type: run service_check on service {0} request_status {1}".format(service_name,request_status) )
                    return



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
    parser.add_argument("-a", "--action", dest="action", choices=['dry-run', 'stop', 'start', 'check_service'],
                        help="Script action: <dry-run>,<stop>,<start>")
    parser.add_argument("-n", "--cluster", dest="cluster",
                        help="Name given to cluster. Ex: 'c1'")
    parser.add_argument("--log_level", dest="logLevel", choices=[
        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level")
    parser.add_argument("--http_debug", action="store_true",
                        dest="http_debug", help="turn on http debug level")
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

    http_dbg_level = 0
    if args.http_debug:
        http_dbg_level = 1

    accessor = api_accessor(host, user, password,
                            protocol, port, http_debug_level=http_dbg_level)
    # logging_tree.printout()

    if action == RUN_SERVICE_CHECK:
        run_all_service_check(cluster, accessor)
        # run_service_check(cluster, accessor, "YARN")
        # start_service_V2(cluster,accessor,"YARN")
    else:
        parser.error(" invalid action arg ")


if __name__ == "__main__":
  try:
    sys.exit(main())
  except (KeyboardInterrupt):
    print("\nAborting ... Keyboard Interrupt.")
    sys.exit(1)
