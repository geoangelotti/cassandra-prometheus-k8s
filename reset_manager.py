import time
import logging
import subprocess
from kubernetes import client
from constants import CASSANDRA_STATEFULSET_NAME, NAMESPACE, KEYSPACE, CREATE_TABLE, CREATE_KEYSPACE
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


logger = logging.getLogger(__name__)


class ResetManager:
    def __init__(self, clients, statefulset_name, namespace):
        self.clients = clients
        self.statefulset_name = statefulset_name
        self.namespace = namespace

    def reset(self):
        self.delete_statefulset()
        self.delete_all_pvcs()
        self.delete_all_pvs()
        self.run_clean_data_script()
        self.apply_manifests()
        self.delete_hpas()
        logger.info("Sleeping for 5 minutes")
        time.sleep(5 * 60)
        self.prepare_cassandra_statements()

    def delete_statefulset(self):
        namespace = self.namespace
        apps_v1 = self.clients.apps_v1

        logger.info(f"Deleting StatefulSet: {self.statefulset_name}")
        apps_v1.delete_namespaced_stateful_set(
            name=self.statefulset_name, namespace=namespace, body=client.V1DeleteOptions())
        logger.info(f"StatefulSet {self.statefulset_name} deleted")

    def delete_all_pvcs(self):
        namespace = self.namespace
        v1 = self.clients.v1
        pvcs = v1.list_namespaced_persistent_volume_claim(namespace)

        for pvc in pvcs.items:
            pvc_name = pvc.metadata.name
            logger.info(f"Deleting PVC: {pvc_name}")
            v1.delete_namespaced_persistent_volume_claim(
                name=pvc_name, namespace=namespace, body=client.V1DeleteOptions())
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
        try:
            result = subprocess.run(
                ["./clean-data.sh"], check=True, capture_output=True, text=True)
            logger.debug(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running clean-data.sh: {e.stderr}")

    def apply_manifests(self, path: str = "manifests/"):
        try:
            result = subprocess.run(
                ["kubectl", "apply", "-f", path], check=True, capture_output=True, text=True)
            logger.info(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error applying manifests: {e.stderr}")

    def delete_hpas(self):
        namespace = self.namespace
        autoscaling_v2 = self.clients.autoscaling_v2
        hpas = autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(
            namespace)

        for hpa in hpas.items:
            hpa_name = hpa.metadata.name
            logger.info(f"Deleting HPA: {hpa_name}")
            autoscaling_v2.delete_namespaced_horizontal_pod_autoscaler(
                name=hpa_name, namespace=namespace, body=client.V1DeleteOptions())

    def prepare_cassandra_statements(self):
        cluster = Cluster(['localhost'], port=9042)
        session = cluster.connect()

        try:
            session.execute(CREATE_KEYSPACE)
            logger.info("Keyspace created")

            session.set_keyspace(KEYSPACE)
            logger.info("Using keyspace my_keyspace")

            session.execute(CREATE_TABLE)
            logger.info("Table created")
        except Exception as e:
            logger.error(f"Error running Cassandra queries: {e}")
        finally:
            cluster.shutdown()
