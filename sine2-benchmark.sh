#!/bin/bash

sleep 180
/home/ubuntu/cassandra-prometheus-k8s/cli.py reset

CASSANDRA_HOSTS=$(kubectl get pods -l app=cassandra -o jsonpath='{.items[*].status.podIP}' | tr ' ' ',')
CURRENT_TIME=$(date +"%Y-%m-%d_%H:%M:%S")
THREADS=15
OPERATIONCOUNT=5000000
RECORDCOUNT=100000
PERIOD=100000

kubectl apply -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
sleep 10
cd /home/ubuntu/ycsb || exit
LOG_DIR=/home/ubuntu/cassandra-prometheus-k8s/logs/sine2/${CURRENT_TIME}
mkdir -p ${LOG_DIR}
/home/ubuntu/ycsb/bin/ycsb load cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloadaConstant -threads ${THREADS} -p recordcount=${RECORDCOUNT} | tee ${LOG_DIR}/load.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ${LOG_DIR}/after_load_status.log
sleep 30
/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloadaSine -threads ${THREADS} -p recordcount=${RECORDCOUNT} -p operationcount=${OPERATIONCOUNT} -p period=${PERIOD} -p amplitude=150 -p baseTarget=200 -p strategy=sine2 | tee ${LOG_DIR}/run.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ${LOG_DIR}/after_run_status.log
kubectl delete -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
kubectl get pods --all-namespaces -o wide -l app=cassandra | tee ${LOG_DIR}/cassandra_pods.log
