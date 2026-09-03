#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ipaddress
import os

from HostNetwork import HostNetwork


class ReplyAddress:
	"""Works out which of our addresses to hand a bot's port back on.

	`MACHINE_IP` is set from `hostname -I | awk '{print $1}'` -- whichever interface the kernel
	happens to list first. On a machine with a VirtualBox host-only adapter, a VPN or a second NIC
	that is routinely an address the Tester cannot route to, and the Tester has no way of knowing:
	it dutifully connects to what it was told and fails on a port it never saw.

	We can do better, because the requester already proved which of our addresses works -- they used
	it to reach us. That only holds while our addresses are the host's (see `HostNetwork`);
	otherwise we fall back to `PUBLIC_IP`/`MACHINE_IP`, as before.
	"""

	def __init__(self, host_network: HostNetwork = None, printer = print):
		self._host_network = host_network if host_network is not None else HostNetwork()
		self._printer = printer

	def for_connection(self, local_address, peer_address) -> str:
		"""
		:param local_address: `socket.getsockname()` of the accepted connection
		:param peer_address: `socket.accept()`'s address of whoever connected
		:return: The host to answer with
		"""
		reached_on = self._reached_address(local_address)
		if reached_on is not None and self._host_network.shares_host_network():
			self._printer("[i] Answering with " + reached_on + " (the address " + str(peer_address[0]) + " reached us on)")
			return reached_on

		variable = "PUBLIC_IP" if ReplyAddress._is_public_ip(peer_address) else "MACHINE_IP"
		configured = os.environ.get(variable)
		if configured is not None:
			self._printer("[i] Answering with " + configured + " (source: " + variable + ")")
			return configured

		# nothing configured; the address we were reached on is all we have, container or not
		self._printer("[w] " + variable + " is not set; answering with " + str(reached_on) + ", the address we were reached on")
		return "" if reached_on is None else reached_on

	@staticmethod
	def _reached_address(local_address):
		"""
		:return: Our side of the connection, or None if it names no interface
		"""
		if local_address is None or len(local_address) < 1:
			return None

		host = local_address[0]
		return None if host in ("", "0.0.0.0", "::") else host

	@staticmethod
	def _is_public_ip(address) -> bool:
		try:
			return not ipaddress.ip_address(address[0]).is_private
		except (ValueError, TypeError, IndexError):
			return False
