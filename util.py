# -*- coding: utf-8 -*-
import os
from docker import Client


def docker_client():
    return Client(base_url='unix://var/run/docker.sock')


def get_packetbeat_image_name():
    return os.getenv('DOCKER_AGENT_PACKETBEAT_IMAGE', 'pipetop/docker-agent-pb')


def get_agent_image_name():
    return os.getenv('DOCKER_AGENT_IMAGE', 'pipetop/docker-agent')


def get_project_image_names():
    # Get the image names of this project, which can be useful in scenarios, when we want to do something on
    # every container except fot agent or packet beat containers.
    return [get_agent_image_name(), get_packetbeat_image_name()]


def env_true(name, default_value):
    x = os.getenv(name, default_value)
    if not x:
        return False
    return x.lower() in ['yes', 'y', '1', 'true', 't']
