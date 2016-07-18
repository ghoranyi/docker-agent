# -*- coding: utf-8 -*-
import os
from docker import Client


def docker_client():
    return Client(base_url='unix://var/run/docker.sock')


def env_true(name, default_value):
    x = os.getenv(name, default_value)
    if not x:
        return False
    return x.lower() in ['yes', 'y', '1', 'true', 't']
