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
import os


PROPERTIES = 'properties'
ATTRIBUTES = 'properties_attributes'
CLUSTERS = 'Clusters'
DESIRED_CONFIGS = 'desired_configs'
SERVICE_CONFIG_NOTE = 'service_config_version_note'
TYPE = 'type'
TAG = 'tag'
ITEMS = 'items'
TAG_PREFIX = 'version'

CLUSTERS_URL = '/api/v1/clusters/{0}'
DESIRED_CONFIGS_URL = CLUSTERS_URL + '?fields=Clusters/desired_configs'
CONFIGURATION_URL = CLUSTERS_URL + '/configurations?type={1}&tag={2}'

logging.getLogger().setLevel("INFO")
## __name__ : the name of the module
logger =get_module_logger(__name__)


MIN_PYTHON_VERSION=(2,7)
used_python_version = (sys.version_info[0], sys.version_info[1])
if used_python_version < MIN_PYTHON_VERSION:
    print("This script requires Python version >= {0}.{1}".format(
        MIN_PYTHON_VERSION[0], MIN_PYTHON_VERSION[1]))
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


def get_all_current_configs(cluster, accessor):
  config_types = get_all_config_types(cluster, accessor)
  for config_type in config_types:
    # if config_type != "slider-client":
    #   continue
    ## filename is the same as the name of the config_type
    filename = config_type
    print filename
    output = output_to_file(filename)
    try:
        get_config(cluster, config_type, accessor, output)
    except Error as exc:
        message = "An exception of type {0} occurred. Arguments:\n{1!r}".format(
            type(exc).__name__, exc.args)
        logger.error(message)
        continue


def get_all_configs(cluster, accessor):
    pass

def get_all_config_types(cluster, accessor):
  response = accessor(DESIRED_CONFIGS_URL.format(cluster))
  desired_tags = json.loads(response)
  return desired_tags[CLUSTERS][DESIRED_CONFIGS].keys()

def output_to_file(filename):
  def output(config):
    dirname = os.path.dirname(__file__)
    CONFIGS_DIR = "CONFIGS"
    output_path = os.path.join(dirname, CONFIGS_DIR)
    if not os.path.exists(output_path):
      os.makedirs(output_path)
    with open(os.path.join(output_path, filename), 'w') as out_file:
      json.dump(config, out_file, indent=2)
  return output

def get_config_tag(cluster, config_type, accessor):
  response = accessor(DESIRED_CONFIGS_URL.format(cluster))
  try:
    desired_tags = json.loads(response)
    current_config_tag = desired_tags[CLUSTERS][DESIRED_CONFIGS][config_type][TAG]
  except Exception as exc:
    raise Exception('"{0}" not found in server response. Response:\n{1}'.format(
        config_type, response))
  return current_config_tag

def get_current_config(cluster, config_type, accessor):
  config_tag = get_config_tag(cluster, config_type, accessor)
  logger.info("### on (Site:{0}, Tag:{1})".format(config_type, config_tag))
  response = accessor(CONFIGURATION_URL.format(
      cluster, config_type, config_tag))
  config_by_tag = json.loads(response)
  print config_by_tag
  current_config = config_by_tag[ITEMS][0]
  ## ambari API exposes service configs endpoint even if they are empty
  if PROPERTIES in current_config:
    return current_config[PROPERTIES], current_config.get(ATTRIBUTES, {})
  else:
    logger.error("config_type {0} empty ".format(config_type))
    logger.error("current_config content : {0} ".format(current_config))
    raise Error

def get_config(cluster, config_type, accessor, output):
  properties, attributes = get_current_config(cluster, config_type, accessor)
  config = {PROPERTIES: properties}
  if len(attributes.keys()) > 0:
    config[ATTRIBUTES] = attributes
  output(config)

def get_service_configs(cluster, accessor, service_name):
    response = accessor(SERVICE_URL.format(
        cluster, service_name), GET_REQUEST_TYPE)
    service_node = json.loads(response)
    return service_node['ServiceInfo']



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
    parser.add_argument("-a", "--action", dest="action", choices=['dry-run', 'test'],
                        help="Script action: <dry-run>,<test>")
    parser.add_argument("-n", "--cluster", dest="cluster",
                        help="Name given to cluster. Ex: 'c1'")
    parser.add_argument("--log_level", dest="logLevel", choices=[
        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level")
    parser.add_argument("--http_debug", action="store_true", dest="http_debug", help="turn on http debug level")
    # will print a  namespace Object with the attributes
    args = parser.parse_args()
    if None in [args.action, args.host, args.cluster]:
        parser.error("One of required arguments is not passed")
        return 1

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
    if action == "test":
        # print get_all_config_types(cluster, accessor)
        get_all_current_configs(cluster,accessor)
        # config_type = "slider-client"
        # get_config(cluster, config_type, accessor, output_to_file(config_type))

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
