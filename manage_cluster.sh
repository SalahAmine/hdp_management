# Confirm the Agent hosts are registered with the Server.
export AMBARI_USER=admin
export AMBARI_PASSWD=admin
export AMBARI_HOST=$(cat /etc/ambari-agent/conf/ambari-agent.ini | grep ^hostname | head -1 | cut -f2 -d= | xargs)

# [[ ! -z $(cat /etc/ambari-server/conf/ambari.properties | grep api.ssl=true) ]] && ssl_enabled="true"
ssl_enabled="false"

if [[  $ssl_enabled == "false " ]] ; then
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

service_name="ZOOKEEPER"
service_name="SMARTSENSE"

#start service
curl -ik -u $AMBARI_CREDS -X PUT -H 'X-Requested-By:ambari'  -d '{ "RequestInfo": {"context" :"Start service ZOOKEEPER via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}'  $AMBARI_URLBASE/services/${service_name}

# stop service
curl -ik -u $AMBARI_CREDS -X PUT -H 'X-Requested-By:ambari'  -d '{ "RequestInfo": {"context" :"Stop service ZOOKEEPER via REST"}, "Body": {"ServiceInfo": {"state": "INSTALLED"}}}'  $AMBARI_URLBASE/services/${service_name}


