from kubernetes import client, config
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import subprocess
import time
import logging
from constants import CASSANDRA_STATEFULSET_NAME, NAMESPACE, CREATE_KEYSPACE, CREATE_TABLE, KEYSPACE
from clients import Clients

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
        self.state = self.get_state()

    def reset(self):
        self.delete_statefulset()
        self.delete_all_pvcs()
        self.delete_all_pvs()
        self.run_clean_data_script()
        self.apply_manifests()
        self.delete_hpas()
        logger.info("Sleeping for 5 minutes")
        time.sleep(5*60)
        # self.run_cassandra_statements()

    def get_state(self):
        apps_v1 = self.clients.apps_v1
        statefulset = apps_v1.read_namespaced_stateful_set(
            self.statefulset_name, self.namespace)

    def delete_hpas(self):
        namespace = self.namespace
        autoscaling_v2 = self.clients.autoscaling_v2
        hpas = autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(
            namespace)

        for hpa in hpas.items:
            hpa_name = hpa.metadata.name
            logger.info(f"Deleting HPA: {hpa_name}")
            autoscaling_v2.delete_namespaced_horizontal_pod_autoscaler(
                name=hpa_name,
                namespace=namespace,
                body=client.V1DeleteOptions()
            )
            logger.info(f"HPA {hpa_name} deleted")

    def delete_all_pvs(self):
        v1 = self.clients.v1
        pvs = v1.list_persistent_volume()

        for pv in pvs.items:
            pv_name = pv.metadata.name
            logger.info(f"Deleting PV: {pv_name}")
            v1.delete_persistent_volume(
                name=pv_name, body=client.V1DeleteOptions())
            logger.info(f"PV {pv_name} deleted")

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

    def delete_statefulset(self):
        namespace = self.namespace
        apps_v1 = self.clients.apps_v1

        logger.info(f"Deleting StatefulSet: {self.statefulset_name}")
        apps_v1.delete_namespaced_stateful_set(
            name=self.statefulset_name, namespace=namespace, body=client.V1DeleteOptions())
        logger.info(f"StatefulSet {self.statefulset_name} deleted")

    def run_clean_data_script(self):
        try:
            result = subprocess.run(
                ["./clean-data.sh"], check=True, capture_output=True, text=True)
            logger.debug(result.stdout)
            logger.info("Data cleaned")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running clean-data.sh: {e.stderr}")

    def apply_manifests(self):
        try:
            result = subprocess.run(
                ["kubectl", "apply", "-f", "manifests/"], check=True, capture_output=True, text=True)
            logger.info(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error applying manifests: {e.stderr}")

    def run_cassandra_statements(self):
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


if __name__ == "__main__":
    environment = KubernetesEnv()
    # environment.reset()
    environment.run_cassandra_statements()
