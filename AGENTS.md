# AGENTS.md — WatchWolf-Client (Clients Manager & Client)

Two WatchWolf modules in one repository:

- **Clients Manager** (DST `0b010`) — listens on TCP **7000** and spawns bots on demand.
- **Client** (DST `0b011`) — a headless Minecraft player the Tester drives: chat, commands, move,
  mine, place, hit, use, look, and video recording.

**Python 3 + Node.js**, built on [mineflayer](https://github.com/PrismarineJS/mineflayer) through
the [`javascript`](https://pypi.org/project/javascript/) bridge. Shipped as a Docker image.

## Layout

```
ClientsManager.py            entry point; port allocation, client registry
ClientsManagerConnector.py   the :7000 socket loop (DST 0b010)
ClientsManagerPetition.py    interface: start_client
MinecraftClient.py           base class every client implements
MineflayerClient.py          the real implementation (mineflayer bot + pathfinder)
ClientConnector.py           per-client socket loop (DST 0b011)
ClientPetition.py            interface: send_message, break_block, move_to, hit, …
ConnectorHelper.py           wire codec: readShort/sendString/readPosition/readItem/…
OnClientConnected.py / OnClientDisconnected.py / OnMessage.py   callback interfaces
Position.py
entities/  Entity.py, EntityType.py   (EntityType is a GENERATED ordinal enum)
items/     Item.py, ItemType.py, items.json  (ItemType is built from items.json at import)
view/      Viewer.py, MineflayerViewer.py (prismarine-viewer), ImageList.py (frames -> mp4)
```

## Build and run

```bash
docker pull nikolaik/python-nodejs
docker build --tag clients-manager .
sudo docker run -i --rm --name ClientsManager -p 7000-7199:7000-7199 \
    --env MACHINE_IP=$(hostname -I | awk '{print $1}') \
    --env PUBLIC_IP=$(curl ifconfig.me) \
    clients-manager:latest
```

The image installs `xserver-xorg-*` + `xvfb` and launches under
`xvfb-run --auto-servernum --server-num=1 --server-args='-ac -screen 0 1280x1024x24'` because
prismarine-viewer's headless renderer needs a GL context. **`python3 ClientsManager.py` on a bare
host will not work** without that display and without the Node packages from `requirements.py`
(`mineflayer`, `mineflayer-pathfinder`, `node-canvas-webgl`, `prismarine-viewer`).

`WatchWolfSetup.sh` in the [WatchWolf repo](https://github.com/watch-wolf/WatchWolf) builds and
runs this container for you.

## Ports and IPs

- **7000** — Clients Manager. `7000-7199` is published, so ~100 concurrent bots.
- `ClientsManager.get_min_id()` hands out ports from **7001 in steps of two**, one pair per
  client: the odd port is the client's `ClientConnector` socket.
- `start_client` returns `PUBLIC_IP:port` when the requester's address is public and
  `MACHINE_IP:port` when it is private (`ClientsManagerConnector._is_public_ip`). Both env vars
  are therefore **required**.

## Conventions and gotchas

- **The protocol is hand-written** as binary literals, matching `API/API.tex` in the WatchWolf
  repo. They read low-bits-first, so `0b000000000100_0_011` is *operation 4, request, DST 0b011
  (Client)*. `ConnectorHelper` is the only place that knows the encodings — strings are a
  2-byte length followed by one byte per character, shorts are LSB-then-MSB, doubles are
  big-endian (`unpack('>d', …)`). Several `send*` helpers are still `pass`/`TODO`.
- **`entities/EntityType.py` and `items/items.json` are generated and order-sensitive.** The enum
  values are ordinals sent over the wire, so they must stay byte-for-byte aligned with
  `EntityType` / `ItemType` in WatchWolf-Core and WatchWolf-Tester. Never reorder or insert in
  the middle; they come from
  [WatchWolf-MaterialGetter](https://github.com/miranda1000/WatchWolf-MaterialGetter).
- **Tabs, not spaces.** The whole codebase indents with tabs; keep it consistent or Python will
  reject the mix.
- **`start_client` blocks and busy-waits** on `_done_clients` under a lock (marked
  `TODO move as async message`), and sleeps 8 s before creating each bot to work around
  [mineflayer#2749](https://github.com/PrismarineJS/mineflayer/issues/2749). Logins time out
  after 120 s, and a timed-out client makes `start_client` return `""` — the Tester reads that as
  a failure.
- **Recording is currently disabled at install time.** `requirements.py` has the
  `prismarine-viewer` and `node-canvas-webgl` `require()` calls commented out, so a freshly built
  image cannot record even though the Dockerfile still installs the X11/xvfb stack. Uncomment them
  to re-enable it.
- **How recording works** when enabled: `MineflayerClient.start_recording()` lazily creates a
  `MineflayerViewer`, which runs prismarine-viewer headless and streams frames over a socket into
  `ImageList`, which encodes an mp4 with `imageio`/ffmpeg on `stop_recording`. Note the viewer
  binds `self._port + 1` where `self._port` is the *Minecraft server* port, not the client's
  assigned port — it does not line up with the port pairing the Clients Manager reserves.
- **There are no tests, no linter config and no CI in this repo.** Quality is tracked externally
  by CodeFactor. Changes here are validated end-to-end from WatchWolf-Tester's
  `src/test/java/client/` and `generic/` suites.
- Sockets bind `0.0.0.0` (the ClientsManager, each client's connector, and the viewer). They used
  to bind `socket.gethostname()`, which resolved to the container IP; if you are reading older
  branches or issues, that is the difference.
- The ClientsManager writes its log to `logs/`, which the container expects as a bind mount
  (`-v ./logs:/app/logs`).
- `LICENSE.md` holds mineflayer's own MIT text (`Copyright (c) 2015 Andrew Kelley`) rather than a
  WatchWolf-authored one. The other WatchWolf repos ship their own MIT `LICENSE`; worth raising if
  licensing ever matters.
