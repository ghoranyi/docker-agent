# -*- coding: utf-8 -*-
import os
import logging
from util import docker_client, env_true, get_packetbeat_image_name

log = logging.getLogger("dockeragent")


def manage_packetbeat():
    if env_true('DOCKER_AGENT_SKIP_PACKETBEAT', 'no'):
        log.info("Skipping Packetbeat setup, because DOCKER_AGENT_SKIP_PACKETBEAT is set to true")
        return

    dc = docker_client()
    # First, stop all packet beat containers that are attached to stopped/non-existing source containers
    for pbc in get_packet_beat_containers(dc=dc):
        source_id = _source_container_id(pbc)
        if source_id:
            source_container = _inspect_container(dc, source_id)
            if not source_container or 'running' not in source_container.get("State", {}).get("Status"):
                log.info("Stopping packet beat %s, because its source container is not running", pbc.get("Id"))
                dc.stop(container=pbc.get("Id"))
                dc.remove_container(container=pbc.get("Id"))

    # Get a list of containers and check each of them if they expose ports that we want.
    # Those that do will be paired with Packetbeat instance
    magic_ports = [int(x) for x in get_http_monitor_ports().split(',') + ['6379', '3306', '5432']]
    already_attached_ids = get_source_container_ids(dc=dc)
    pulled = False
    for c in dc.containers():
        if c.get("Id") in already_attached_ids:
            continue

        for port in c.get("Ports", []):
            matching_port = next(
                (p for p in magic_ports if p in [port.get("PublicPort"), port.get("PrivatePort")]),
                None)
            if matching_port:
                # woohoo, start packetbeat
                cid = c.get("Id")
                log.info("Starting packetbeat for container %s with id %s, because it exposes port %s",
                         c.get("Image"), cid, matching_port)
                if not pulled:
                    # will pull the image if it doesn't exist yet or is not the latest version
                    for line in dc.pull('{}:latest'.format(get_packetbeat_image_name()), stream=True):
                        log.debug(line)
                    pulled = True

                host_config = dc.create_host_config(network_mode='container:' + cid)
                packet_beat = dc.create_container(
                    image=get_packetbeat_image_name(),
                    host_config=host_config,
                    environment={
                        'ES_ADDRESS': os.getenv('DOCKER_AGENT_ELASTIC_SEARCH_ADDRESS', 'vizdemo-backend:9200'),
                        'LOGSTASH_ADDRESS': os.getenv('DOCKER_AGENT_LOGSTASH_ADDRESS'),
                        'MONITOR_HTTP_PORTS': get_http_monitor_ports()
                    },
                    command="./start-pb.sh",
                    detach=True)
                dc.start(container=packet_beat.get("Id"))


def get_packet_beat_containers(dc=None):
    # get a list of already running packet beat containers
    return [
        _inspect_container(dc, c.get("Id"))
        for c in dc.containers()
        if get_packetbeat_image_name() in c.get("Image", "")]


def get_source_container_ids(dc=None):
    # Get the ids of all those containers that have packet beat already attached.
    # This is possible, because we set <container:id> as network mode when starting packet beat.
    return [_source_container_id(_inspect_container(dc, c.get("Id"))) for c in get_packet_beat_containers(dc)]


def _source_container_id(container):
    net_mode = container.get("HostConfig", {}).get("NetworkMode", "")
    if ':' in net_mode:
        return net_mode.split(':')[1]
    return None


def get_http_monitor_ports():
    return os.getenv('DOCKER_AGENT_MONITOR_HTTP_PORTS', '80, 5000, 5001, 8000, 8001, 8080')


def _inspect_container(client, cid):
    try:
        return client.inspect_container(cid)
    except:
        return {}
