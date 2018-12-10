#!/usr/bin/env python

import urllib2
import base64
import json
import ssl
import sys

HTTP_PROTOCOL = 'http'
HTTPS_PROTOCOL = 'https'
SET_ACTION = 'set'
GET_ACTION = 'get'
DELETE_ACTION = 'delete'
GET_REQUEST_TYPE = 'GET'
PUT_REQUEST_TYPE = 'PUT'

CLUSTERS_URL = '/api/v1/clusters/{0}'
DESIRED_CONFIGS_URL = CLUSTERS_URL + '?fields=Clusters/desired_configs'
CONFIGURATION_URL = CLUSTERS_URL + '/configurations?type={1}&tag={2}'
SERVICES_URL = CLUSTERS_URL + '/services'
SERVICE_URL = SERVICES_URL + "/{1}"

LIST_SERVICES_TO_STOP = ["SMARTSENSE", "AMBARI_INFRA", "RANGER", "KNOX", "OOZIE", "HIVE", "HBASE", "SPARK2", "MAPREDUCE2", "YARN", "HDFS", "ZOOKEEPER", "HUE",
                         "STORM", "KAFKA", "ATLAS", "LOG_SEARCH", "AMBARI_METRICS"]


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
            if unsafe:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                response = urllib2.urlopen(request, context=ctx)
            else:
                response = urllib2.urlopen(request)
                response_body = response.read()
        except Exception as exc:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(exc).__name__, exc.args)
            print (message)
            raise Exception(
                'Problem with accessing api. Reason: {0}'.format(exc))
        return response_body
    return do_request


def list_all_services(cluster, accessor):
    response = json.loads(accessor(SERVICES_URL.format(cluster)))
    list_services = []
    for service in response['items']:
        list_services.append(service['ServiceInfo']["service_name"])
    return list_services


def stop_all_services(cluster, accessor):
    """ the method follows this order in stooping hdp services
    https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.0/bk_HDP_Reference_Guide/content/stopping_hdp_services.html"""
    list_services = list_all_services(cluster, accessor)

    for service_name in LIST_SERVICES_TO_STOP:
        if service_name in list_services:
            stop_service(cluster, accessor, service_name)


def stop_service(cluster, accessor, service_name):

    request_body = '{{ "RequestInfo": {{"context" :"Stop service {0} via REST"}}, "Body": {{"ServiceInfo": {{"state": "INSTALLED"}} }} }}'.format(
        service_name)
    print ("about to stop {0}".format(service_name))
    response = accessor(SERVICE_URL.format(
        cluster, service_name), PUT_REQUEST_TYPE, request_body)
    return response



def main():

    host = "10.0.0.21"
    login = "admin"
    password = "admin"
    protocol = "http"
    port = "8080"
    accessor = api_accessor(host, login, password, protocol, port)
    cluster = "mytestcluster"
    # api_url after port number
    # print "list of my all services "
    # print (list_all_services(cluster, accessor))
    # stop_all_services(cluster, accessor)
    stop_all_services(cluster, accessor)


if __name__ == "__main__":
  try:
    sys.exit(main())
  except (KeyboardInterrupt):
    print("\nAborting ... Keyboard Interrupt.")
    sys.exit(1)

# print (stop_service(cluster,accessor,service_name))
# print (start_service(cluster, accessor, service_name))

# print json.dumps(response, indent=2, sort_keys=True)
# print json.dumps(response['items'], indent=2, sort_keys=True)
# print json.dumps(response['items'][0]['ServiceInfo']["service_name"], indent=2, sort_keys=True)
