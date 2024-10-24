#!/bin/bash

nodes=("node1" "node2" "node3" "node4" "node5" "node6")

for node in "${nodes[@]}"
do
  echo $node start
  number="${node//[^0-9]/}"
  ssh ubuntu@$node "rm -rfv /mnt/data/a/*"
  ssh ubuntu@$node "rm -rfv /mnt/data/b/*"
  ssh ubuntu@$node "rm -rfv /mnt/data/c/*"
  ssh ubuntu@$node "rm -rfv /mnt/data/d/*"
  ssh ubuntu@$node "rm -rfv /mnt/data/e/*"
  ssh ubuntu@$node "rm -rfv /mnt/data/f/*"
  ssh ubuntu@$node "ls -la /mnt/data"
  echo $node done
done