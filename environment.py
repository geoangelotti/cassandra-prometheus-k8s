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
        pass

    def get_state(self):
        apps_v1 = self.clients.apps_v1
        statefulset = apps_v1.read_namespaced_stateful_set(
            self.statefulset_name, self.namespace)
        print(statefulset)


if __name__ == "__main__":
    environment = KubernetesEnv()
    print(environment)
