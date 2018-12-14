# Confirm the Agent hosts are registered with the Server.
export AMBARI_USER=admin
export AMBARI_PASSWD=admin
export AMBARI_HOST=$(cat /etc/ambari-agent/conf/ambari-agent.ini | grep hostname | cut -f2 -d=)
export AMBARI_PORT=8080
export AMBARI_CREDS="$AMBARI_USER:$AMBARI_PASSWD"
export AMBARI_URLBASE="http://${AMBARI_HOST}:${AMBARI_PORT}/api/v1/clusters"

export CLUSTER_NAME="$(curl -u ${AMBARI_CREDS} -i -H 'X-Requested-By:ambari' $AMBARI_URLBASE | sed -n 's/.*"cluster_name" : "\([^\"]*\)".*/\1/p')"
echo $CLUSTER_NAME
export AMBARI_URLBASE=$AMBARI_URLBASE/$CLUSTER_NAME

# check ambari-server is up , if auth succeeds  Apache license information is displayed.
curl -u ${AMBARI_USER}:${AMBARI_PASSWD}  http://${AMBARI_HOST}:${AMBARI_PORT}

# curl -u $AMBARI_CREDS -X GET -H 'X-Requested-By:ambari' $AMBARI_URLBASE/services/

# get service state
curl -u $AMBARI_CREDS -X GET -H 'X-Requested-By:ambari' $AMBARI_URLBASE/services/ZOOKEEPER?fields=ServiceInfo/state

service_name="ZOOKEEPER"
service_name="SMARTSENSE"

#start service
curl -i -u $AMBARI_CREDS -X PUT -H 'X-Requested-By:ambari'  -d '{ "RequestInfo": {"context" :"Start service ZOOKEEPER via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}'  $AMBARI_URLBASE/services/${service_name}

# stop service
curl -i -u $AMBARI_CREDS -X PUT -H 'X-Requested-By:ambari'  -d '{ "RequestInfo": {"context" :"Stop service ZOOKEEPER via REST"}, "Body": {"ServiceInfo": {"state": "INSTALLED"}}}'  $AMBARI_URLBASE/services/${service_name}


