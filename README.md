# hdp_management
This is a python client that enables managing a hadoop stack.  

manage_cluster.py allows to start/stop an entire cluster. 

```
usage: manage_cluster.py [-h] [-u USER] [-p PASSWORD] [-l HOST] [-t PORT]
                         [-s PROTOCOL] [--unsafe] [-a {dry-run,stop,start}]
                         [-n CLUSTER]
                         [--log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                         [--http_debug]

optional arguments:
  -h, --help            show this help message and exit
  -l HOST, --host HOST  Server external host name
  -t PORT, --port PORT  Optional port number for Ambari server. Default is
                        '8080'. Provide empty string to not use port.
  -s PROTOCOL, --protocol PROTOCOL
                        Optional support of SSL. Default protocol is 'http'
  --unsafe              Skip SSL certificate verification.
  -a {dry-run,stop,start}, --action {dry-run,stop,start}
                        Script action: <dry-run>,<stop>,<start>
  -n CLUSTER, --cluster CLUSTER
                        Name given to cluster. Ex: 'c1'
  --log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --http_debug          turn on http debug level

login_options_group:
  -u USER, --user USER  Optional user ID to use for authentication. Default is
                        'admin'
  -p PASSWORD, --password PASSWORD
                        Optional password to use for authentication. Default
                        is 'admin'


```

## Usage

Example1 
```
./hdp_management/manage_cluster.py -l master -u admin -p admin -n mytestcluster -a start

```
starts a cluster named "mytestcluster" , ambari-server API is running on host "master", port "8080" (default ), in http mode (default),
ambari admin user is "admin", related password is "admin"

Example2 
```
./hdp_management/manage_cluster.py -l master -t 8443 -s https --unsafe -u admin -p admin -n mytestcluster -a stop

```
stops a cluster named "mytestcluster" , ambari-server API is running on host "master", port "8443" (default ), in https mode, ignore ssl verification
ambari admin user is "admin", related password is "admin"

Example0
```
./hdp_management/manage_cluster.py -l master -u admin -p admin -n mytestcluster -a dry-run

```
a dry-run that tests access to ambari and provided cluster is ok 



./hdp_management/check_services.py -l 10.0.0.21 -n mytestcluster2 -a check_service