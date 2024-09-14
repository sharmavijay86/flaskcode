from flask import Flask, render_template, request
import csv
import requests
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app = Flask(__name__)

def check_status(url, protocol):
    try:
        start_time = time.time()
        if protocol == 'http':
            response = requests.get(f"http://{url}")
        elif protocol == 'tcp':
            response = requests.get(f"http://{url}")  # Simplified for example
        response_time = time.time() - start_time
        return 'UP', response_time
    except:
        return 'DOWN', None

def get_openshift_deployments(api_url, namespace, token):
    try:
        configuration = client.Configuration()
        configuration.host = api_url
        configuration.verify_ssl = False
        configuration.api_key = {"authorization": f"Bearer {token}"}
        client.Configuration.set_default(configuration)
        v1 = client.AppsV1Api()
        deployments = v1.list_namespaced_deployment(namespace)
        down_deployments = [d.metadata.name for d in deployments.items if d.status.replicas == 0]
        active_deployments = [d.metadata.name for d in deployments.items if d.status.replicas > 0]
        return down_deployments, active_deployments, 'UP'
    except ApiException as e:
        print(f"Exception when calling AppsV1Api->list_namespaced_deployment: {e}")
        return [], [], 'DOWN'
    except Exception as e:
        print(f"General exception: {e}")
        return [], [], 'DOWN'

@app.route('/')
def index():
    urls = []
    with open('urls.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            status, response_time = check_status(row['servernameorip'], row['monitoringprotocol'])
            row['status'] = status
            row['response_time'] = response_time
            urls.append(row)
    
    groups = {}
    for url in urls:
        group = url['groupname']
        if group not in groups:
            groups[group] = {'UP': 0, 'DOWN': 0}
        groups[group][url['status']] += 1

    openshift_instances = []
    with open('openshift_instances.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            down_deployments, active_deployments, status = get_openshift_deployments(row['ocp_api_url'], row['namespace'], row['token'])
            row['down_count'] = len(down_deployments)
            row['active_count'] = len(active_deployments)
            row['down_deployments'] = down_deployments
            row['active_deployments'] = active_deployments
            row['status'] = status
            openshift_instances.append(row)

    return render_template('index.html', urls=urls, groups=groups, openshift_instances=openshift_instances)

if __name__ == '__main__':
    app.run(debug=True)
