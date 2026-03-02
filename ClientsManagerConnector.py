#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from threading import Thread
from ClientsManagerPetition import ClientsManagerPetition
from ConnectorHelper import ConnectorHelper
import ipaddress

class ClientsManagerConnector:
	def __init__(self, petition_handler: ClientsManagerPetition, port: int = 7000, printer = lambda msg: print(msg)):
		self._petition_handler = petition_handler
		self._port = port
		self._printer = printer
	
	def run(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(("0.0.0.0", self._port))
		self.socket.listen(5)
		self._printer("[v] ClientsManager up and running!")
		
		while True:
			# accept connections from outside
			(client_socket, address) = self.socket.accept() # TODO send address to the Client so it only replies to that one
			
			self._printer("[v] One client connected from " + address[0] + ":" + str(address[1]))
			Thread(target = self._client_manager, args = (client_socket,ClientsManagerConnector._is_public_ip(address))).start()
	
	@staticmethod
	def _is_public_ip(address) -> bool:
		ip = ipaddress.ip_address(address[0])
		return not ip.is_private
	
	def _client_manager(self, socket, public_access: bool):
		while True:
			msg = None
			try:
				msg = ConnectorHelper.readShort(socket)
			except Exception:
				# socket closed
				self._printer("[i] Client disconnected")
				break

			if msg == 0b000000000001_0_010:
				# start client petition
				username = ConnectorHelper.readString(socket)
				ip = ConnectorHelper.readString(socket)
				
				self._printer("Starting client " + username + " at server " + ip + "...")
				user_ip = self._petition_handler.start_client(username, ip, public_access)
				if user_ip != "":
					self._printer("Client started at " + user_ip)
				
				# send response
				ConnectorHelper.sendShort(socket, 0b000000000001_1_010)
				ConnectorHelper.sendString(socket, user_ip)
			else:
				self._printer("Unknown request: " + str(msg))
