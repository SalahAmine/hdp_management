# Confirm the Agent hosts are registered with the Server.
export AMBARI_USER=admin
export AMBARI_PASSWD=admin
export AMBARI_HOST=$(cat /etc/ambari-agent/conf/ambari-agent.ini | grep ^hostname | head -1 | cut -f2 -d= | xargs)

# [[ ! -z $(cat /etc/ambari-server/conf/ambari.properties | grep api.ssl=true) ]] && ssl_enabled="true"
ssl_enabled="false"

if [[  "$ssl_enabled" == "false" ]] ; then
    WEB_PROTOCOL="http"
    AMBARI_PORT=8080
else
    WEB_PROTOCOL="https"
    # AMBARI_PORT=$(cat /etc/ambari-server/conf/ambari.propertie | grep client.api.ssl.port| cut -f2 -d= | xargs)
    AMBARI_PORT=8443
fi

export WEB_PROTOCOL
export AMBARI_PORT



export AMBARI_CREDS="$AMBARI_USER:$AMBARI_PASSWD"
export AMBARI_URLBASE="${WEB_PROTOCOL}://${AMBARI_HOST}:${AMBARI_PORT}/api/v1/clusters"

## -k, --insecure      Allow connections to SSL sites without  cert verif
export CLUSTER_NAME="$(curl -ik -u ${AMBARI_CREDS} -X GET -H 'X-Requested-By:ambari' $AMBARI_URLBASE | sed -n 's/.*"cluster_name" : "\([^\"]*\)".*/\1/p')"
echo $CLUSTER_NAME
export AMBARI_URLBASE=$AMBARI_URLBASE/$CLUSTER_NAME



# check ambari-server is up , if auth succeeds  Apache license information is displayed.
curl -ik -u ${AMBARI_USER}:${AMBARI_PASSWD} -X GET -H 'X-Requested-By:ambari'  "${WEB_PROTOCOL}://${AMBARI_HOST}:${AMBARI_PORT}"

## get services
curl -ik -u $AMBARI_CREDS -X GET -H 'X-Requested-By:ambari' $AMBARI_URLBASE/services/

# get service state
curl -ik -u $AMBARI_CREDS -X GET -H 'X-Requested-By:ambari' $AMBARI_URLBASE/services/ZOOKEEPER?fields=ServiceInfo/state

# service_name="ZOOKEEPER"
service_name="SMARTSENSE"

#start service
curl -ik -u $AMBARI_CREDS -X PUT -H 'X-Requested-By:ambari'  -d '{ "RequestInfo": {"context" :"Start service ZOOKEEPER via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}'  $AMBARI_URLBASE/services/${service_name}


# stop service
curl -ik -u $AMBARI_CREDS -X PUT -H 'X-Requested-By:ambari'  -d '{ "RequestInfo": {"context" :"Stop service ZOOKEEPER via REST"}, "Body": {"ServiceInfo": {"state": "INSTALLED"}}}'  $AMBARI_URLBASE/services/${service_name} 

# stop service (returns request id )
request_id=$(curl -k -u $AMBARI_CREDS -X PUT -H 'X-Requested-By:ambari'  -d '{ "RequestInfo": {"context" :"Stop service via REST"}, "Body": {"ServiceInfo": {"state": "INSTALLED"}}}'  $AMBARI_URLBASE/services/${service_name} | python -c "import json, sys; print(json.loads(sys.stdin.read())['Requests']['id']);" )
echo $request_id


# get request status by request id
request_id=122
curl -ik -u $AMBARI_CREDS -X GET -H 'X-Requested-By:ambari' $AMBARI_URLBASE/requests/$request_id

# poll request_id  status 
while true; do 
curl -k -u $AMBARI_CREDS -X GET  -H 'X-Requested-By:ambari' $AMBARI_URLBASE/requests/$request_id | python -c "import json, sys; print(json.loads(sys.stdin.read())['Requests']['request_status']);" 
sleep 5
done


# set maintenance state
curl -ik -u $AMBARI_CREDS -X PUT -H 'X-Requested-By:ambari'  -d '{"RequestInfo":{"context":"Turn On Maintenance Mode for HDFS"},"Body":{"ServiceInfo":{"maintenance_state":"ON"}}}'  $AMBARI_URLBASE/services/HDFS

# get maintenance state
curl -ik -u $AMBARI_CREDS -X GET -H 'X-Requested-By:ambari'   $AMBARI_URLBASE/services/HDFS


# get client  config
config_type="hdfs-site"
config_type="slider-client"
curl -ik -u $AMBARI_CREDS -X GET -H 'X-Requested-By:ambari' "$AMBARI_URLBASE/configurations?type=$config_type&tag=TOPOLOGY_RESOLVED"

#The @- part tells it to read from stdin 
# The @payload part tells it to read from file named payload
# run service check for ZOOK
curl -ik -u $AMBARI_CREDS -H 'X-Requested-By:ambari' -X POST  -d '{"RequestInfo":{"context":"ZooKeeper Service Check","command":"ZOOKEEPER_QUORUM_SERVICE_CHECK"},"Requests/resource_filters":[{"service_name":"ZOOKEEPER"}]}' "$AMBARI_URLBASE/requests"

# run service check for HDFS
curl -ik -u $AMBARI_CREDS -H 'X-Requested-By:ambari' -X POST  -d '{"RequestInfo":{"context":"HDFS Service Check","command":"HDFS_SERVICE_CHECK"},"Requests/resource_filters":[{"service_name":"HDFS"}]}' "$AMBARI_URLBASE/requests"

curl -i -s -k  -X $'POST' \
    -H $'Accept-Encoding: gzip, deflate' -H $'Content-Length: 133' -H $'X-Requested-By: ambari' -H $'Connection: close' -H $'User-Agent: Python-urllib/2.7' -H $'Host: 10.0.0.21:8080' -H $'Content-Type: application/x-www-form-urlencoded' -H $'Authorization: Basic YWRtaW46YWRtaW4=' \
    --data-binary $'{\"RequestInfo\":{\"context\":\"HDFS Service Check\",\"command\":\"HDFS_SERVICE_CHECK\"},\"Requests/resource_filters\":[{\"service_name\":\"HDFS\"}]}' \
    $'http://10.0.0.21:8080/api/v1/clusters/mytestcluster/requests'

'{"RequestInfo":{"context":"HDFS Service Check","command":"HDFS_SERVICE_CHECK"},"Requests/resource_filters":[{"service_name":"HDFS"}]}'
{"RequestInfo": {"command": "HDFS_SERVICE_CHECK", "context": "HDFS Service Check via REST"}, "Requests/resource_filters": [{"service_name": "HDFS"}]}'