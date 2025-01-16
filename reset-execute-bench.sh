#!/bin/bash

python3 /home/ubuntu/cassandra-prometheus-k8s/environment.py
sleep 15
/home/ubuntu/ycsb/bin/ycsb load cassandra-cql -p hosts=localhost -s -P workloads/workloadaConstantLoad
sleep 3m
date "+%Y-%m-%d %H:%M:%S"
/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=localhost -s -P workloads/workloadaSineLoad -p period=300000
date "+%Y-%m-%d %H:%M:%S"
