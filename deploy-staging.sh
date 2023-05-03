#!/bin/bash

echo "Deploying Notifier SMS Platform | v1.6"
echo "========================================="

echo -n "Cleaning up existing docker containers..."

docker stop $(docker ps -a -q --filter "name=staging") >/dev/null 2>&1
docker kill $(docker ps -q --filter "name=staging") >/dev/null 2>&1
docker rm $(docker ps -a -q --filter "name=staging") >/dev/null 2>&1
docker rmi $(docker images -q --filter "name=staging") >/dev/null 2>&1
docker system prune -a -f >/dev/null 2>&1
docker volume prune -f >/dev/null 2>&1
docker builder prune -a -f >/dev/null 2>&1

shopt -s extglob

#rm -rf /var/lib/docker
#
#systemctl restart docker

echo "COMPLETE"

echo -n "Creating docker project directory..."

mkdir -p /home/nf_docker_project/staging >/dev/null 2>&1

echo "COMPLETE"

echo -n "Creating docker data directory..."

mkdir -p /home/nf_docker_data/staging/pgadmin >/dev/null 2>&1

chmod 777 /home/nf_docker_data/staging/pgadmin

echo "COMPLETE"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

echo -n "Creating docker container..."

docker-compose -f "$SCRIPT_DIR/docker-compose-staging.yml" up -d

docker system prune -a -f >/dev/null 2>&1

echo "COMPLETE"

cp -n "$SCRIPT_DIR/env.example" "$SCRIPT_DIR/.env"
