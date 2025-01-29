#!/bin/bash

CASSANDRA_HOSTS=$(kubectl get pods -l app=cassandra -o jsonpath='{.items[*].status.podIP}' | tr ' ' ',')
CURRENT_TIME=$(date +"%Y-%m-%d_%H:%M:%S")
THREADS=500
OPERATIONCOUNT=20000000
RECORDCOUNT=100000

kubectl apply -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
sleep 10
cd /home/ubuntu/ycsb || exit
mkdir -p ./${CURRENT_TIME}
/home/ubuntu/ycsb/bin/ycsb load cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloadaConstant -threads ${THREADS} -p recordcount=${RECORDCOUNT} | tee ./${CURRENT_TIME}/load.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ./${CURRENT_TIME}/after_load_status.log
sleep 30
/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloadaConstant -threads ${THREADS} -p recordcount=${RECORDCOUNT} -p operationcount=${OPERATIONCOUNT} | tee ./${CURRENT_TIME}/run.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ./${CURRENT_TIME}/after_run_status.log
kubectl delete -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloadaConstant -threads ${THREADS} -p recordcount=${RECORDCOUNT} -p operationcount=${OPERATIONCOUNT}> ./${CURRENT_TIME}/run.log
kubectl exec -i -t cassandra-0 -c cassandra -- nodetool status > ./${CURRENT_TIME}/after_run_status.log
kubectl delete -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
