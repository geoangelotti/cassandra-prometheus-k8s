import requests
import os


class PrometheusClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def query(self, query):
        url = f"{self.base_url}/api/v1/query"
        params = {'query': query}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def query_from_file(self, query_file):
        with open(query_file, 'r') as file:
            query = file.read().strip()
        return self.query(query)

    def query_all_from_directory(self, directory="queries"):
        results = {}
        for filename in os.listdir(directory):
            print(filename)
            if filename.endswith(".promql"):
                file_path = os.path.join(directory, filename)
                results[filename] = self.query_from_file(file_path)
        return results
