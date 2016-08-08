# -*- coding: utf-8 -*-
import os
import uuid
import logging
import requests
import time
import simplejson
import datetime
from util import docker_client, env_true, get_project_image_names

log = logging.getLogger("dockeragent")


class DummyBackend(object):
    def register_node(self):
        self.node_id = str(uuid.uuid1())
        log.info("registering as random UUID: %s", self.node_id)
        return self.node_id

    def send_container_list(self):
        dc = docker_client()
        containers = get_containers(dc)
        print "conts=", containers
        log.info("container list for node %s is: %s",
                 self.node_id,
                 get_container_names(containers))
        log.info("networks for node %s: %s",
                 self.node_id,
                 simplejson.dumps(get_networks(dc, [c["Id"] for c in containers])))


class RemoteBackend(object):
    def __init__(self):
        self.backend_url = os.getenv('DOCKER_AGENT_BACKEND_URL', "http://vizdemo-backend")
        self.backend_port = os.getenv('DOCKER_AGENT_BACKEND_PORT', "8878")

    def register_node(self):
        while True:
            try:
                url = "{backend}:{port}/containers/api/register/{node_id}".format(
                    backend=self.backend_url,
                    port=self.backend_port,
                    node_id=str(uuid.uuid1()))
                response = requests.get(url)
                response.raise_for_status()

                log.info("Node registered, id: {txt}".format(txt=response.text))
                self.node_id = response.text
                return self.node_id
            except Exception as e:
                log.warn("Failed to register node: {}. Retry in 10s.".format(e))
                time.sleep(10)

    def send_container_list(self):
        try:
            dc = docker_client()
            containers = get_containers(dc)
            url = "{backend}:{port}/containers/api/snapshot/{node}/".format(
                backend=self.backend_url,
                port=self.backend_port,
                node=self.node_id)
            data = {
                "containers": containers,
                "networks": get_networks(dc, [c["Id"] for c in containers])
            }
            response = requests.post(url, data=simplejson.dumps(data))
            log.info("[{timestamp}] {response} {containers}".format(
                timestamp=datetime.datetime.utcnow().strftime("%Y:%m:%d %H:%M:%S"),
                response=response.status_code,
                containers=get_container_names(containers)
            ))
            response.raise_for_status()
        except Exception as e:
            log.exception(e)
            log.warn("[{timestamp}] FAILED to send data.".format(
                timestamp=datetime.datetime.utcnow().strftime("%Y:%m:%d %H:%M:%S")))


def get_container_names(containers_info):
    return ','.join(c["Image"] for c in containers_info if "Image" in c)


def get_networks(dc, cids):
    # Find all networks for each of the container ids. This is needed, because docker API
    # doesn't return all network info with inspect_container() command.
    networks = dict()
    hostnames = get_hostnames(dc, cids)

    for network in dc.networks():
        for container_id, net_info in (network.get("Containers") or {}).iteritems():
            if container_id in cids:
                if container_id not in networks:
                    networks[container_id] = {"hostname": hostnames.get(container_id), "networks": {}}
                data = {
                    "Name": network["Name"]
                }
                data.update(net_info)
                networks[container_id]["networks"][network["Id"]] = data
    return networks


def get_containers(dc):
    # get container info for all containers except of those that belong to agent and/or packetbeat
    return [c for c in dc.containers() if c["Image"] not in get_project_image_names()]


def get_hostnames(dc, cids):
    return {
        cid: dc.inspect_container(cid).get("Config", {}).get("Hostname")
        for cid in cids
    }


def get_backend():
    return DummyBackend() if env_true('DOCKER_AGENT_DUMMY_BACKEND', 'no') else RemoteBackend()
