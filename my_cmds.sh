ambari_server_host=master
clsuter_name=mytestcluster
./configs.py --user=admin --password=admin --port=8080 --action=get --host=${ambari_server_host} --cluster=${clsuter_name} --config-type=yarn-site --file=/tmp/yarn_site_payload.json