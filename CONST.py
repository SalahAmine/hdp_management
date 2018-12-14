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

LIST_SERVICES_TO_STOP = ["SMARTSENSE", "LOG_SEARCH", "AMBARI_INFRA", "RANGER", "KNOX", "OOZIE", "HIVE", "HBASE", "SPARK2", "MAPREDUCE2", "YARN", "HDFS", "ZOOKEEPER", "HUE",
                         "STORM", "KAFKA", "ATLAS", "AMBARI_METRICS"]

