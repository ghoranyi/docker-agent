import datetime
from docker import Client
import os
import requests
import schedule
import simplejson
import time


def get_client():
    return Client(base_url='unix://var/run/docker.sock')


def get_backend_url():
    return os.getenv('DOCKER_AGENT_BACKEND_URL', "http://backend")


def get_backend_port():
    return os.getenv('DOCKER_AGENT_BACKEND_PORT', "8878")


def register_node():
    while True:
        try:
            url = "{backend}:{port}/containers/api/register".format(backend=get_backend_url(), port=get_backend_port())
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            raise Exception()
        except:
            print("Failed to register node. Retry in 10s.")
            time.sleep(10)


def send_container_list(node_id):
    try:
        containers = get_client().containers()
        url = "{backend}:{port}/containers/api/snapshot/{node}/".format(
            backend=get_backend_url(),
            port=get_backend_port(),
            node=node_id)
        data = {
            "containers": containers
        }
        response = requests.post(url, data=simplejson.dumps(data))
        container_names = [c["Image"] for c in containers]
        print("[{timestamp}] {response} {containers}".format(
            timestamp=datetime.datetime.utcnow().strftime("%Y:%m:%d %H:%M:%S"),
            response=response.status_code,
            containers=','.join(container_names)
        ))
    except:
        print("[{timestamp}] FAILED to send data.".format(
            timestamp=datetime.datetime.utcnow().strftime("%Y:%m:%d %H:%M:%S")))

node_id = register_node()
send_container_list()
schedule.every().minute.do(send_container_list, node_id=node_id)

while True:
    schedule.run_pending()
    time.sleep(1)
