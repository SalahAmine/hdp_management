#!/usr/bin/env python

import urllib2
import base64

HTTP_PROTOCOL = 'http'
HTTPS_PROTOCOL = 'https'
SET_ACTION = 'set'
GET_ACTION = 'get'
DELETE_ACTION = 'delete'
GET_REQUEST_TYPE = 'GET'
PUT_REQUEST_TYPE = 'PUT'

# JSON Keywords
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


protocol="http"
host="10.0.0.21"
port="8080"
api_url="/api/v1/clusters"
login="admin"
password="admin"


def do_request(api_url, request_type=GET_REQUEST_TYPE, request_body=''):
    try:
        url = '{0}://{1}:{2}{3}'.format(protocol, host, port, api_url)
        admin_auth = base64.encodestring('%s:%s' % (login, password)).replace('\n', '')
        print ("target url is {0}".format(url))
        request = urllib2.Request(url)
        request.add_header('Authorization', 'Basic %s' % admin_auth)
        request.add_header('X-Requested-By', 'ambari')
        # return the content of GET_REQUEST_TYPE const string
        # due to abscence of CONSTANT notion in python, GET_REQUEST_TYPE is technically speaking a variable,
        # so instead of having a second refrence to its content, we get a copy of its value by calling the lambda function
        # request.get_method= lambda: GET_REQUEST_TYPE
        response=urllib2.urlopen(request)
        response_body = response.read()

    except Exception as exc:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(exc).__name__, exc.args)
        print (message)
        raise Exception('Problem with accessing api. Reason: {0}'.format(exc))

    return response_body


print (do_request(api_url))


#
# request.add_data(request_body)
# request.get_method = lambda: request_type
