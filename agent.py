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


def send_container_list():
    containers = get_client().containers()
    url = "{backend}:{port}/api/docker_stats".format(backend=get_backend_url(), port=get_backend_port())
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

send_container_list()
schedule.every().minute.do(send_container_list)

while True:
    schedule.run_pending()
    time.sleep(1)
