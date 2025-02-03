import json
from kubernetes import client, config
import logging
import time
from constants import CASSANDRA_STATEFULSET_NAME, NAMESPACE, CREATE_KEYSPACE, CREATE_TABLE, KEYSPACE
from clients import Clients
from reset_manager import ResetManager
from prometheus import PrometheusClient
from typing import List, Any

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

    def prepare(self):
        self.reset_manager.prepare()

    def delete(self):
        self.reset_manager.delete()

    def monitor_released_pvs(self):
        while True:
            pvs = self.clients.v1.list_persistent_volume()
            failed_pvs = [
                pv for pv in pvs.items if pv.status.phase == 'Released']
            self.clean_pvs(failed_pvs)
            time.sleep(30)

    def clean_pvs(self, pvs: List[Any]):
        for pv in pvs:
            name = pv.metadata.name
            path = pv.spec.local.path
            node = pv.spec.node_affinity.required.node_selector_terms[
                0].match_expressions[0].values[0]
            self.delete_pv(name)
            self.clean_mnt_directory(node, path)
            logger.info(f"Persistent Volume {name} cleaned successfully.")
        if pvs:
            self.reset_manager.apply_manifests(
                "manifests/local-pv-massive.yaml")

    def clean_mnt_directory(self, node: str, path: str):
        command = f"rm -rf {path}/*"
        ssh_command = ["ssh", f"ubuntu@{node}", f"{command}"]
        logger.info(" ".join(ssh_command))
        self.reset_manager.try_subprocess(ssh_command)

    def delete_pv(self, pv_name: str):
        try:
            self.clients.v1.delete_persistent_volume(name=pv_name)
            logger.info(f"Persistent Volume {pv_name} deleted successfully.")
        except client.exceptions.ApiException as e:
            logger.error(
                f"Exception when deleting Persistent Volume {pv_name}: {e}")


if __name__ == "__main__":
    environment = KubernetesEnv()
    environment.monitor_released_pvs()
