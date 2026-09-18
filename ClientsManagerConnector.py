#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from threading import Thread
from ClientsManagerPetition import ClientsManagerPetition
from ConnectorHelper import ConnectorHelper
from ReplyAddress import ReplyAddress

class ClientsManagerConnector:
	def __init__(self, petition_handler: ClientsManagerPetition, port: int = 7000, printer = lambda msg: print(msg), reply_address: ReplyAddress = None):
		self._petition_handler = petition_handler
		self._port = port
		self._printer = printer
		self._reply_address = reply_address if reply_address is not None else ReplyAddress(printer = printer)
	
	def run(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(("0.0.0.0", self._port))
		self.socket.listen(5)
		self._printer("[v] ClientsManager up and running!")
		
		while True:
			# accept connections from outside
			(client_socket, address) = self.socket.accept() # TODO send address to the Client so it only replies to that one
			
			self._printer("[v] One client connected from " + address[0] + ":" + str(address[1]))
			# the requester proved which of our addresses works by reaching us on it; that is the one
			# their bots' ports should be handed back on
			reply_host = self._reply_address.for_connection(client_socket.getsockname(), address)
			Thread(target = self._client_manager, args = (client_socket, reply_host)).start()
	
	def _client_manager(self, socket, reply_host: str):
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
				user_ip = self._petition_handler.start_client(username, ip, reply_host)
				if user_ip != "":
					self._printer("Client started at " + user_ip)
				
				# send response
				ConnectorHelper.sendShort(socket, 0b000000000001_1_010)
				ConnectorHelper.sendString(socket, user_ip)
			else:
				self._printer("Unknown request: " + str(msg))
