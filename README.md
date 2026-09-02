# WatchWolf - Client & Clients Manager [![CodeFactor](https://www.codefactor.io/repository/github/miranda1000/watchwolf-client/badge/dev)](https://www.codefactor.io/repository/github/miranda1000/watchwolf-client/overview/dev)

The player half of [WatchWolf](https://watchwolf.dev/). Two modules ship from this repository:

- **Clients Manager** — listens on TCP **7000** and spawns bots on demand.
- **Client** — a headless Minecraft player the Tester drives: chat, run commands, walk, mine,
  place, hit, use, look around, and record video of what it sees.

Written in **Python 3** on top of [mineflayer](https://github.com/PrismarineJS/mineflayer), via
the [`javascript`](https://pypi.org/project/javascript/) Python↔Node bridge.

## How it works

```
Tester ──"start MinecraftGamer_Z on <server ip:port>"──▶ ClientsManager :7000
                                                                │
                                                    MineflayerClient
                                                                │  joins the Minecraft server
                                                                ▼
Tester ◀──────"started, at <ip>:N"────── bot's own socket on :N (client petitions)
```

Each bot gets a port from **7001 upwards, in steps of two**. The address returned is
`PUBLIC_IP:N` when the request came from a public address and `MACHINE_IP:N` when it came from the
local network — both environment variables are required.

## Dependencies

- [Docker](https://www.docker.com/get-started/)
- Python image: `docker pull nikolaik/python-nodejs`
- Build the image: `docker build --tag clients-manager .`

The image also installs `xvfb` and the X11 headers, because
[prismarine-viewer](https://github.com/PrismarineJS/prismarine-viewer)'s headless renderer — used
for recordings — needs a GL context. Running `python3 ClientsManager.py` directly on a host
without that display and without the Node packages from `requirements.py` will not work; use the
container.

> **Note:** `prismarine-viewer` and `node-canvas-webgl` are currently commented out in
> `requirements.py`, so a freshly built image cannot record. Uncomment them to re-enable
> `start_recording` / `stop_recording`.

## Launch

```bash
docker run -i --rm --name ClientsManager -p 7000-7199:7000-7199 \
    -v ./logs:/app/logs \
    --env MACHINE_IP=$(hostname -I | awk '{print $1}') \
    --env PUBLIC_IP=$(curl ifconfig.me) \
    clients-manager:latest
```

The `7000-7199` range is what caps the number of concurrent bots. `./logs` receives the
ClientsManager's log files (the folder is gitignored). The
[WatchWolf setup script](https://github.com/watch-wolf/WatchWolf) builds and runs this container
for you.

To get extra diagnostics out of the Node bridge and mineflayer, add:

```
--env NODE_OPTIONS="--unhandled-rejections=strict --trace-warnings" --env PYTHONUNBUFFERED=1
```

## Layout

| File | Role |
| --- | --- |
| `ClientsManager.py` | Entry point: port allocation and the client registry |
| `ClientsManagerConnector.py` | The `:7000` socket loop |
| `MineflayerClient.py` | The bot implementation |
| `ClientConnector.py` | Per-bot socket loop |
| `ClientPetition.py` / `ClientsManagerPetition.py` | The interfaces each module implements |
| `ConnectorHelper.py` | The wire codec (strings, shorts, doubles, positions, items, entities) |
| `view/` | `MineflayerViewer` (prismarine-viewer) and `ImageList` (frames → mp4 via imageio/ffmpeg) |
| `entities/`, `items/` | `EntityType` / `ItemType` — **generated**, ordinal-sensitive enums |

`entities/EntityType.py` and `items/items.json` come from
[WatchWolf-MaterialGetter](https://github.com/miranda1000/WatchWolf-MaterialGetter). Their
order is the wire encoding, so it must stay aligned with the Java `EntityType`/`ItemType` in
WatchWolf-Core and WatchWolf-Tester — never reorder or insert in the middle.

## Testing

There are no tests in this repository. The modules are exercised end to end by
[WatchWolf-Tester](https://github.com/miranda1000/WatchWolf-Tester)'s suite, which spawns real
bots against real servers.

## Related

- [WatchWolf](https://github.com/watch-wolf/WatchWolf) — the protocol specification and setup script
- [WatchWolf-Tester](https://github.com/miranda1000/WatchWolf-Tester) — sends the petitions
- [WatchWolf-ServersManager](https://github.com/miranda1000/WatchWolf-ServersManager) — the equivalent module for servers
