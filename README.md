# WatchWolf - Client & Clients Manager [![CodeFactor](https://www.codefactor.io/repository/github/rogermiranda1000/watchwolf-client/badge/dev)](https://www.codefactor.io/repository/github/rogermiranda1000/watchwolf-client/overview/dev)
A Python library to test Minecraft Plugins in the client side. For more information about WatchWolf check the [WatchWolf website](https://watchwolf.dev/).

## Dependencies
- [Docker](https://www.docker.com/get-started/)
- Python image: `docker pull nikolaik/python-nodejs`
- Build the image: `docker build --tag clients-manager .`

## Launch

- Run the docker container: `docker run -i --rm --name ClientsManager -p 7000-7199:7000-7199 -v ./logs:/app/logs --env MACHINE_IP=$(hostname -I | awk '{print $1}') --env PUBLIC_IP=$(curl ifconfig.me) clients-manager:latest`

Optional: add debug information `--env NODE_OPTIONS="--unhandled-rejections=strict --trace-warnings" --env PYTHONUNBUFFERED=1`
