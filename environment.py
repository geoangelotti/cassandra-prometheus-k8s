from kubernetes import client, config

import logging
from constants import CASSANDRA_STATEFULSET_NAME, NAMESPACE, CREATE_KEYSPACE, CREATE_TABLE, KEYSPACE
from clients import Clients
from reset_manager import ResetManager
from prometheus import PrometheusClient

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KubernetesEnv:
    def __init__(self):
        config.load_kube_config()

        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        autoscaling_v2 = client.AutoscalingV2Api()
        clients = Clients(v1, apps_v1, autoscaling_v2)

        self.statefulset_name = CASSANDRA_STATEFULSET_NAME
        self.namespace = NAMESPACE
        self.clients = clients
        self.reset_manager = ResetManager(
            self.clients, self.statefulset_name, self.namespace)
        self.prometheus_client = PrometheusClient("http://localhost:9090")

    def reset(self):
        self.reset_manager.reset()


if __name__ == "__main__":
    environment = KubernetesEnv()
    environment.reset()
