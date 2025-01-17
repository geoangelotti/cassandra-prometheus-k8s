#!/bin/bash

while [[ $# -gt 0 ]]; do
    case $1 in
        --hpa)
            HPA="$2"
            shift 2
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

python3 /home/ubuntu/cassandra-prometheus-k8s/environment.py
sleep 15
cd /home/ubuntu/ycsb || exit
/home/ubuntu/ycsb/bin/ycsb load cassandra-cql -p hosts=localhost -s -P workloads/workloadaConstantLoad -p recordcount=5000
sleep 3m

case $HPA in
    "cpu")
        echo "Configuring CPU-based HPA"
        # Your CPU HPA command here
        kubectl apply -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-cpu.yaml
        ;;
    "mem")
        echo "Configuring Memory-based HPA"
        # Your Memory HPA command here
        kubectl apply -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa-mem.yaml
        ;;
    "both")
        echo "Configuring both CPU and Memory HPA"
        # Commands for both
        kubectl apply -f /home/ubuntu/cassandra-prometheus-k8s/manifests/cassandra-hpa.yaml
        ;;
    "")
        echo "No HPA type specified. Use --hpa with cpu, mem, or both"
		echo "Starting dry"
        ;;
    *)
        echo "Invalid HPA type. Use cpu, mem, or both"
        exit 1
        ;;
esac

date "+%Y-%m-%d %H:%M:%S"
/home/ubuntu/ycsb/bin/ycsb run cassandra-cql -p hosts=localhost -s -P workloads/workloadaSineLoad -p period=300000 -p recordcount=5000 -p operationcount=800000
date "+%Y-%m-%d %H:%M:%S"
