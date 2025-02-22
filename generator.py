#!/usr/bin/env python
import yaml

STORAGE_SIZE = "5Gi"


def create_pv_yaml(name, storage_size, path, node):
    pv = {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {
            "name": name
        },
        "spec": {
            "capacity": {
                "storage": storage_size
            },
            "accessModes": ["ReadWriteOnce"],
            "persistentVolumeReclaimPolicy": "Retain",
            "storageClassName": "local-storage",
            "local": {
                "path": path
            },
            "nodeAffinity": {
                "required": {
                    "nodeSelectorTerms": [
                        {
                            "matchExpressions": [
                                {
                                    "key": "kubernetes.io/hostname",
                                    "operator": "In",
                                    "values": [node]
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    return pv


def main():
    pvs = []
    for i in range(1, 6):
        for j in range(3):
            ch = chr(j+97)
            name = f"local-pv-{i+1}-{ch}"
            path = f"/mnt/data/{ch}"
            node = f"node{i+1}"
            pv_yaml = create_pv_yaml(name, STORAGE_SIZE, path, node)
            pvs.append(pv_yaml)
    with open(f"manifests/local-pv-massive.yaml", 'w') as file:
        for pv in pvs:
            file.write("---\n")
            yaml.dump(pv, file, default_flow_style=False)


if __name__ == "__main__":
    main()
