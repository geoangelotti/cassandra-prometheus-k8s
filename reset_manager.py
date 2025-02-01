import asyncio
import time
import logging
import subprocess
from typing import List
from kubernetes import client
from cassandra_manager import CassandraManager
from constants import TABLE


logger = logging.getLogger(__name__)


class ResetManager:
    def __init__(self, clients, statefulset_name, namespace):
        self.clients = clients
        self.statefulset_name = statefulset_name
        self.namespace = namespace
        self.cassandra_manager = CassandraManager(
            self.clients, self.statefulset_name, self.namespace)

    def reset(self):
        self.delete()
        self.prepare()

    def delete(self):
        self.cassandra_manager.truncate_table(TABLE)
        self.delete_statefulset()
        self.delete_all_pvcs()
        self.delete_all_pvs()
        self.run_clean_data_script()

    def prepare(self):
        self.apply_manifests()
        self.delete_hpas()
        self.is_cluster_ready()
        self.prepare_cassandra_statements()

    def delete_statefulset(self):
        apps_v1 = self.clients.apps_v1
        v1 = self.clients.v1

        logger.info(f"Deleting StatefulSet: {self.statefulset_name}")
        apps_v1.delete_namespaced_stateful_set(
            name=self.statefulset_name, namespace=self.namespace, body=client.V1DeleteOptions())
        while True:
            pods = v1.list_namespaced_pod(
                namespace=self.namespace, label_selector=f"app={self.statefulset_name}")
            if not pods.items:
                logger.info("All pods deleted")
                break
            logger.info("Waiting for pods to be deleted...")
            time.sleep(20)
        logger.info(f"StatefulSet {self.statefulset_name} deleted")

    def delete_all_pvcs(self):
        v1 = self.clients.v1

        pvcs = v1.list_namespaced_persistent_volume_claim(self.namespace)
        for pvc in pvcs.items:
            pvc_name = pvc.metadata.name
            logger.info(f"Deleting PVC: {pvc_name}")
            v1.delete_namespaced_persistent_volume_claim(
                name=pvc_name, namespace=self.namespace, body=client.V1DeleteOptions())
            logger.info(f"PVC {pvc_name} deleted")

    def delete_all_pvs(self):
        v1 = self.clients.v1
        pvs = v1.list_persistent_volume()

        for pv in pvs.items:
            pv_name = pv.metadata.name
            logger.info(f"Deleting PV: {pv_name}")
            v1.delete_persistent_volume(
                name=pv_name, body=client.V1DeleteOptions())
            logger.info(f"PV {pv_name} deleted")

    def run_clean_data_script(self):
        self.try_subprocess(["./clean-data.sh"])

    def apply_manifests(self, path: str = "manifests/"):
        self.try_subprocess(["kubectl", "apply", "-f", path])

    def try_subprocess(self, command: List[str]):
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            for line in process.stdout:
                logger.info(line.strip())
            for line in process.stderr:
                logger.error(line.strip())
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, process.args)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running {command}: {e}")

    def delete_hpas(self):
        autoscaling_v2 = self.clients.autoscaling_v2
        hpas = autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(
            self.namespace)

        for hpa in hpas.items:
            hpa_name = hpa.metadata.name
            logger.info(f"Deleting HPA: {hpa_name}")
            autoscaling_v2.delete_namespaced_horizontal_pod_autoscaler(
                name=hpa_name, namespace=self.namespace, body=client.V1DeleteOptions())

    def prepare_cassandra_statements(self):
        self.cassandra_manager.prepare_cassandra_statements()

    def is_statefulset_ready(self):
        statefulset = self.clients.apps_v1.read_namespaced_stateful_set(
            name=self.statefulset_name, namespace=self.namespace)
        ready_replicas = statefulset.status.ready_replicas or 0
        total_replicas = statefulset.status.replicas or 0
        return ready_replicas == total_replicas

    def is_cluster_ready(self):
        time.sleep(20)
        while not self.is_statefulset_ready():
            logger.info("StatefulSet is not ready yet")
            time.sleep(20)
        logger.info("StatefulSet is ready")

    async def port_forward_cassandra_loadbalancer(namespace='default', service_name='cassandra-loadbalancer', local_port=9042, remote_port=9042):
        try:
            v1 = client.CoreV1Api()
            service = v1.read_namespaced_service(
                name=service_name, namespace=namespace)
            logger.info(
                f"Service {service_name} found in namespace {namespace}")
            logger.info(f"Starting port-forward for {service_name} service")
            process = await asyncio.create_subprocess_exec(
                "kubectl", "port-forward", f"service/{service_name}", f"{local_port}:{remote_port}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                logger.info(
                    f"Port-forwarding started successfully: {stdout.decode()}")
            else:
                logger.error(f"Port-forwarding failed: {stderr.decode()}")
        except client.exceptions.ApiException as e:
            logger.error(
                f"Exception when calling CoreV1Api->read_namespaced_service: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
