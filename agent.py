# -*- coding: utf-8 -*-
"""
Agent has two main responsibilities:
    1. Constantly gather containers information and send it to backend
    2. Start packet beat for each of the containers that expose http or redis port(s)

Agent recognizes following environment variables:
    DOCKER_AGENT_BACKEND_URL                Address of 'container-storage' backend
    DOCKER_AGENT_BACKEND_PORT               Port of 'container-storage' backend
    DOCKER_AGENT_DUMMY_BACKEND              If true, then we don't connect to remote backend
    DOCKER_AGENT_SKIP_PACKETBEAT            If true, there will be no Packetbeat setup/monitoring
    DOCKER_AGENT_PACKETBEAT_IMAGE           Name of the Packetbeat image, default is 'pipetop/docker-agent-pb'
    DOCKER_AGENT_ELASTIC_SEARCH_ADDRESS     Elastic search address for Packetbeat to connect to (<host:port>)
    DOCKER_AGENT_MONITOR_HTTP_PORTS         List of http ports that Packetbeat instances will capture
"""
import schedule
import time
import logging
from backend import get_backend
from packetbeat import manage_packetbeat

log = logging.getLogger("dockeragent")
logging.basicConfig(level=logging.INFO)

backend = get_backend()
backend.register_node()

# .run() is added to force scheduler to start the task right away, otherwise we have to wait
# for 30 seconds for first execution
schedule.every(30).seconds.do(backend.send_container_list).run()
schedule.every(60).seconds.do(manage_packetbeat).run()

while True:
    schedule.run_pending()
    time.sleep(1)
