#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


class HostNetwork:
	"""Answers whether this process shares the host's network namespace.

	It decides whether the address a requester reached us on is worth anything to them. Bots get
	ports published on the **host** (`-p 7000-7199:7000-7199`), so when we run in a container of our
	own on a bridge network, every connection reaches us as the bridge gateway and our side of it is
	a `172.x` address nobody outside the bridge can route to. Handing that back would be strictly
	worse than the `MACHINE_IP` guess it replaced.

	With `--network host`, or when running straight on the host, our address *is* the host's, and it
	is the best answer available: it is the interface the requester demonstrably reached.

	The signal is that a bridged container sees only `lo` and its own `eth*`, while a process sharing
	the host namespace sees the host's Docker bridges (`docker0`, `br-<id>`).
	"""

	CONTAINER_MARKERS = ["/.dockerenv", "/run/.containerenv"]
	NET_INTERFACES_PATH = "/sys/class/net"

	def __init__(self):
		self._shares_host_network = None

	def shares_host_network(self) -> bool:
		if self._shares_host_network is None:
			self._shares_host_network = not HostNetwork._is_containerized() or HostNetwork._sees_host_docker_bridges()
		return self._shares_host_network

	@staticmethod
	def _is_containerized() -> bool:
		return any(os.path.exists(marker) for marker in HostNetwork.CONTAINER_MARKERS)

	@staticmethod
	def _sees_host_docker_bridges() -> bool:
		try:
			interfaces = os.listdir(HostNetwork.NET_INTERFACES_PATH)
		except OSError:
			return False # can't tell; assume the conservative answer
		return any(name == "docker0" or name.startswith("br-") for name in interfaces)
