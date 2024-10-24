#!/bin/bash

nodes=("node1" "node2" "node3" "node4" "node5" "node6")

for node in "${nodes[@]}"
do
  echo $node start
  number="${node//[^0-9]/}"
  ssh ubuntu@$node "sudo apt-get update"
  ssh ubuntu@$node "sudo apt-get upgrade -y"
  ssh ubuntu@$node "sudo reboot"
  echo $node done
done