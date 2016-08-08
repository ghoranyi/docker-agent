# docker-agent

Docker agent recognizes following env variables:

```
    DOCKER_AGENT_IMAGE                      Name of the Agent image, default is 'ghoranyi/docker-agent'
    DOCKER_AGENT_BACKEND_URL                Address of 'container-storage' backend
    DOCKER_AGENT_BACKEND_PORT               Port of 'container-storage' backend
    DOCKER_AGENT_DUMMY_BACKEND              If true, then we don't connect to remote backend
    DOCKER_AGENT_SKIP_PACKETBEAT            If true, there will be no Packetbeat setup/monitoring
    DOCKER_AGENT_PACKETBEAT_IMAGE           Name of the Packetbeat image, default is 'ghoranyi/docker-agent-pb'
    DOCKER_AGENT_ELASTIC_SEARCH_ADDRESS     Elastic search address for Packetbeat to connect to (<host:port>)
    DOCKER_AGENT_LOGSTASH_ADDRESS           Logstash address for Packetbeat to connect to (<host:port>)
    DOCKER_AGENT_MONITOR_HTTP_PORTS         List of http ports that Packetbeat instances will capture
```

Example run command with dummy backend:

```
docker run -e DOCKER_AGENT_DUMMY_BACKEND=1 -e DOCKER_AGENT_ELASTIC_SEARCH_ADDRESS=192.168.99.100:9200 -v /var/run/docker.sock:/var/run/docker.sock docker_agent
```

Example run command in aws (has to be run on specific node, not through swarm connection):

```
docker run -d \
    -e DOCKER_AGENT_PACKETBEAT_IMAGE=ghoranyi/docker-agent-pb \
    -e DOCKER_AGENT_BACKEND_URL=http://backend-2129167539.eu-west-1.elb.amazonaws.com \
    -e DOCKER_AGENT_BACKEND_PORT=80 \
    -e DOCKER_AGENT_LOGSTASH_ADDRESS=52.208.120.22:22711 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    ghoranyi/docker-agent
```
