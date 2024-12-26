from kubernetes import client, config
from constants import CASSANDRA_STATEFULSET_NAME, NAMESPACE
from clients import Clients


class KubernetesEnv:
    def __init__(self):
        # Load Kubernetes configuration
        config.load_kube_config()

        # Create API clients
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        autoscaling_v2 = client.AutoscalingV2Api()

        clients = Clients(v1, apps_v1, autoscaling_v2)

        self.statefulset_name = CASSANDRA_STATEFULSET_NAME
        self.namespace = NAMESPACE
        self.clients = clients
        self.state = self.get_state()

    def reset(self):
        self.delete_hpas()
        self.delete_all_pvcs()
        self.delete_all_pvs()

    def get_state(self):
        apps_v1 = self.clients.apps_v1
        statefulset = apps_v1.read_namespaced_stateful_set(
            self.statefulset_name, self.namespace)
        print(statefulset)

    def delete_hpas(self):
        namespace = self.namespace

        autoscaling_v2 = self.clients.autoscaling_v2
        hpas = autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(
            namespace)

        for hpa in hpas.items:
            hpa_name = hpa.metadata.name
            print(f"Deleting HPA: {hpa_name}")
            autoscaling_v2.delete_namespaced_horizontal_pod_autoscaler(
                name=hpa_name,
                namespace=namespace,
                body=client.V1DeleteOptions()
            )

    def delete_all_pvs(self):
        v1 = self.clients.v1
        pvs = v1.list_persistent_volume()

        for pv in pvs.items:
            pv_name = pv.metadata.name
            print(f"Deleting PV: {pv_name}")
            v1.delete_persistent_volume(
                name=pv_name, body=client.V1DeleteOptions())
            print(f"PV {pv_name} deleted")

    def delete_all_pvcs(self):
        namespace = self.namespace

        v1 = self.clients.v1
        pvcs = v1.list_namespaced_persistent_volume_claim(namespace)

        # Delete each PersistentVolumeClaim
        for pvc in pvcs.items:
            pvc_name = pvc.metadata.name
            print(f"Deleting PVC: {pvc_name}")
            v1.delete_namespaced_persistent_volume_claim(
                name=pvc_name, namespace=namespace, body=client.V1DeleteOptions())
            print(f"PVC {pvc_name} deleted")

        def delete_all_pods_and_statefulset(self):
            namespace = self.namespace

            apps_v1 = self.clients.apps_v1
            print(f"Deleting StatefulSet: {self.statefulset_name}")
            apps_v1.delete_namespaced_stateful_set(
                name=self.statefulset_name, namespace=namespace, body=client.V1DeleteOptions())


if __name__ == "__main__":
    environment = KubernetesEnv()
    environment.delete_hpas()
