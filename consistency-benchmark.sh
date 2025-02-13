#!/bin/bash

/home/ubuntu/cassandra-prometheus-k8s/cli.py reset

CASSANDRA_HOSTS=$(kubectl get pods -l app=cassandra -o jsonpath='{.items[*].status.podIP}' | tr ' ' ',')
CURRENT_TIME=$(date +"%Y-%m-%d_%H:%M:%S")
LOAD_THREADS=50
THREADS=10
LOG_DIR=/home/ubuntu/cassandra-prometheus-k8s/logs/consistency/${CURRENT_TIME}
THREADS=20
OPERATIONCOUNT=2000000
RECORDCOUNT=1000000

#kubectl apply -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
sleep 10
cd /home/ubuntu/ycsb || exit
mkdir -p ${LOG_DIR}	
kubectl scale statefulset cassandra --replicas=10
sleep 6m
/home/ubuntu/ycsb/bin/ycsb load cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloadaConstant -threads ${LOAD_THREADS} -p recordcount=${RECORDCOUNT} | tee ${LOG_DIR}/load.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ${LOG_DIR}/after_load_status.log
sleep 15m

/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloadb -threads ${THREADS} -p recordcount=${RECORDCOUNT} -p operationcount=${OPERATIONCOUNT} -p cassandra.readconsistencylevel=ONE -p cassandra.writeconsistencylevel=ONE | tee ${LOG_DIR}/run_b_one.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ${LOG_DIR}/after_run_status_b_one.log
#kubectl delete -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
kubectl get pods --all-namespaces -o wide -l app=cassandra | tee ${LOG_DIR}/cassandra_pods_b_one.log

sleep 7m
/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloadb -threads ${THREADS} -p recordcount=${RECORDCOUNT} -p operationcount=${OPERATIONCOUNT} -p cassandra.readconsistencylevel=ALL -p cassandra.writeconsistencylevel=ALL | tee ${LOG_DIR}/run_b_all.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ${LOG_DIR}/after_run_status_b_all.log
#kubectl delete -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
kubectl get pods --all-namespaces -o wide -l app=cassandra | tee ${LOG_DIR}/cassandra_pods_b_all.log
sleep 7m

/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloada -threads ${THREADS} -p recordcount=${RECORDCOUNT} -p operationcount=${OPERATIONCOUNT} -p cassandra.readconsistencylevel=ONE -p cassandra.writeconsistencylevel=ONE | tee ${LOG_DIR}/run_a_one.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ${LOG_DIR}/after_run_status_a_one.log
#kubectl delete -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
kubectl get pods --all-namespaces -o wide -l app=cassandra | tee ${LOG_DIR}/cassandra_pods_a_one.log
sleep 7m

/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=${CASSANDRA_HOSTS} -s -P workloads/workloada -threads ${THREADS} -p recordcount=${RECORDCOUNT} -p operationcount=${OPERATIONCOUNT} -p cassandra.readconsistencylevel=ALL -p cassandra.writeconsistencylevel=ALL | tee ${LOG_DIR}/run_a_all.log
kubectl exec -it cassandra-0 -c cassandra -- nodetool status | tee ${LOG_DIR}/after_run_status_a_all.log
#kubectl delete -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
kubectl get pods --all-namespaces -o wide -l app=cassandra | tee ${LOG_DIR}/cassandra_pods_a_all.log
