#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import threading
from time import sleep

from ClientsManagerPetition import ClientsManagerPetition
from ClientsManagerConnector import ClientsManagerConnector
from MineflayerClient import MineflayerClient

from MinecraftClient import MinecraftClient
from OnClientConnected import OnClientConnected
from OnClientDisconnected import OnClientDisconnected

class ClientsManager(ClientsManagerPetition, OnClientConnected, OnClientDisconnected):
	def __init__(self, client_builder, port: int = 7000):
		def connector_printer(msg: str):
			print(msg)
			with open("logs/clients_manager.log", "a") as log_file:
				log_file.write(msg + "\n")

		#self._connector = ClientsManagerConnector(self, printer = connector_printer)
		self._connector = ClientsManagerConnector(self)
		self._client_builder = client_builder
		
		self._base_port = port+1
		self._client_list = {}
		
		self._done_clients = []
		self._thread_lock = threading.Lock()
		
	def run(self):
		self._connector.run()
	
	def client_connected(self, client: MinecraftClient):
		self._thread_lock.acquire()
		self._done_clients.append(client)
		self._thread_lock.release()
		
	def client_disconnected(self, client: MinecraftClient):
		self._thread_lock.acquire()
		port = [k for k, v in self._client_list.items() if v == client][0]
		del self._client_list[port]
		self._thread_lock.release()
	
	def start_client(self, username: str, server_ip: str, reply_host: str = None) -> str:
		ip = server_ip.split(":")
		port = self.get_min_id()
		sleep(8) # @ref https://github.com/PrismarineJS/mineflayer/issues/2749
		client = self._client_builder(username, ip[0], int(ip[1]), port, self, self)
		self._thread_lock.acquire()
		self._client_list[port] = client
		self._thread_lock.release()
		
		# wait for client_connected signal
		# TODO move as anync message
		stay = True
		while stay:
			self._thread_lock.acquire()
			stay = not (client in self._done_clients)
			self._thread_lock.release()
		self._thread_lock.acquire()
		self._done_clients.remove(client)
		self._thread_lock.release()
		
		if client.timedout:
			return "" # error

		# the connector already worked out which of our addresses the requester can reach
		host = reply_host if reply_host else os.environ['MACHINE_IP']
		return f"{host}:{port}"
	
	def get_min_id(self) -> int:
		current_port = self._base_port
		self._thread_lock.acquire()
		while (current_port in self._client_list):
			current_port += 2 # each client has 2 ports (one for the connector, the other for the images)
		self._client_list[current_port] = None # reserve the port
		self._thread_lock.release()
		return current_port

if __name__ == '__main__':
	client_builder = lambda username, ip, ip_port, assigned_port, on_client_connected, on_client_disconnected : MineflayerClient(ip, ip_port, username, assigned_port, on_client_connected, on_client_disconnected)
	ClientsManager(client_builder).run()
