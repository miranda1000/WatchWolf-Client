#!/bin/bash

# some utilities
script_path=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# parse params
force_recreate=0
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --force-recreate) force_recreate=1 ;;
        *) echo "[e] Unknown parameter passed: $1" >&2 ; exit 1 ;;
    esac
    shift
done

# build if needed
if [ $force_recreate -eq 1 ] || ! docker image inspect clients-manager >/dev/null 2>&1; then
    echo "[v] Building Docker image..."
    docker build --tag clients-manager .
fi

# run
echo "[v] Running..."
export MACHINE_IP=$(hostname -I | awk '{print $1}')
export PUBLIC_IP=$(curl ifconfig.me)

docker run -d --rm --name ClientsManager \
    --network host \
    -p 7000-7199:7000-7199 \
    --env MACHINE_IP="$MACHINE_IP" \
    --env PUBLIC_IP="$PUBLIC_IP" \
    clients-manager
