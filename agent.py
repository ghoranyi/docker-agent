import datetime
from docker import Client
import logging
import os
import requests
import schedule
import simplejson
import time
import uuid


log = logging.getLogger("dockeragent")
logging.basicConfig(level=logging.INFO)


class DummyBackend(object):
    def register_node(self):
        self.node_id = str(uuid.uuid1())
        log.info("registering as random UUID: %s", self.node_id)
        return self.node_id

    def send_container_list(self):
        log.info("container list for node %s is: %s",
                 self.node_id,
                 get_container_names(get_client().containers()))


class RemoteBackend(object):
    def __init__(self):
        self.backend_url = os.getenv('DOCKER_AGENT_BACKEND_URL', "http://backend")
        self.backend_port = os.getenv('DOCKER_AGENT_BACKEND_PORT', "8878")

    def register_node(self):
        while True:
            try:
                url = "{backend}:{port}/containers/api/register".format(
                    backend=self.backend_url,
                    port=self.backend_port)
                response = requests.get(url)
                if response.status_code == 200:
                    log.info("Node registered, id: {txt}".format(txt=response.text))
                    self.node_id = response.text
                    return self.node_id
                raise Exception()
            except:
                log.warn("Failed to register node. Retry in 10s.")
                time.sleep(10)

    def send_container_list(self):
        try:
            containers = get_client().containers()
            url = "{backend}:{port}/containers/api/snapshot/{node}/".format(
                backend=self.backend_url,
                port=self.backend_port,
                node=self.node_id)
            data = {
                "containers": containers
            }
            response = requests.post(url, data=simplejson.dumps(data))
            log.info("[{timestamp}] {response} {containers}".format(
                timestamp=datetime.datetime.utcnow().strftime("%Y:%m:%d %H:%M:%S"),
                response=response.status_code,
                containers=get_container_names(containers)
            ))
        except:
            log.warn("[{timestamp}] FAILED to send data.".format(
                timestamp=datetime.datetime.utcnow().strftime("%Y:%m:%d %H:%M:%S")))


def get_client():
    return Client(base_url='unix://var/run/docker.sock')


def get_container_names(containers_info):
    return ','.join(c["Image"] for c in containers_info if "Image" in c)


dummy_backend = os.getenv('DOCKER_AGENT_DUMMY_BACKEND', 'no').lower() in ['yes', 'y', '1', 'true', 't']
backend = DummyBackend() if dummy_backend else RemoteBackend()
backend.register_node()

schedule.every().minute.do(backend.send_container_list).run()

while True:
    schedule.run_pending()
    time.sleep(1)
