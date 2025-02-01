from constants import KEYSPACE, CREATE_TABLE, CREATE_KEYSPACE
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import logging

logger = logging.getLogger(__name__)


class CassandraManager:
    def __init__(self, clients, statefulset_name, namespace):
        self.clients = clients
        self.statefulset_name = statefulset_name
        self.namespace = namespace

    def prepare_cassandra_statements(self):
        v1 = self.clients.v1
        pod_name = "cassandra-0"
        pod = v1.read_namespaced_pod(name=pod_name, namespace=self.namespace)
        pod_ip = pod.status.pod_ip

        cluster = Cluster([pod_ip], port=9042)
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
