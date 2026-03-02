#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

# view file
import os
import random
import string

from ConnectorHelper import ConnectorHelper
from OnMessage import OnMessage
from ClientPetition import ClientPetition

class ClientConnector(OnMessage):
	def __init__(self, petition_handler: ClientPetition, port: int, printer):
		self._petition_handler = petition_handler
		self._port = port
		self._printer = printer
		self._socket = None
		self._closed = False
	
	def run(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(("0.0.0.0", self._port))
		self.socket.listen(5)
		
		# accept connections from outside
		(client_socket, address) = self.socket.accept() # TODO send address to the Client so it only replies to that one
		
		self._socket = client_socket
		while not self._closed: # TODO sync
			try:
				msg = ConnectorHelper.readShort(client_socket)
			except Exception:
				break # socket closed
				
			if msg == 0b000000000011_0_011:
				message = ConnectorHelper.readString(client_socket)
				self._printer(f"Sending '{message}'...")
				self._petition_handler.send_message(message)
			elif msg == 0b000000000100_0_011:
				command = ConnectorHelper.readString(client_socket)
				timeout = ConnectorHelper.readShort(client_socket)
				self._printer(f"Running '{command}'...")
				reply = self._petition_handler.send_command(command, timeout)
				if len(reply) > 0: self._printer(f"Result of '{command}' was '{reply}'")
				
				# response
				ConnectorHelper.sendShort(self._socket, 0b000000000100_1_011)
				ConnectorHelper.sendString(self._socket, reply)
			elif msg == 0b000000000101_0_011:
				pos = ConnectorHelper.readPosition(client_socket)
				self._printer(f"Breaking block at {pos}...")
				self._petition_handler.break_block(pos)
			elif msg == 0b000000000110_0_011:
				item = ConnectorHelper.readItem(client_socket)
				self._printer(f"Set {item} as item in hand")
				self._petition_handler.equip_item_in_hand(item)
			elif msg == 0b000000000111_0_011:
				pos = ConnectorHelper.readPosition(client_socket)
				self._printer(f"Going to {pos}")
				self._petition_handler.move_to(pos)
			elif msg == 0b000000001000_0_011:
				pitch = ConnectorHelper.readDouble(client_socket)
				yaw = ConnectorHelper.readDouble(client_socket)
				self._printer(f"Looking at {pitch}, {yaw}")
				self._petition_handler.look_at(pitch, yaw)
			elif msg == 0b000000001001_0_011:
				self._petition_handler.synchronize()
				ConnectorHelper.sendShort(client_socket, 0b000000001001_1_011) # response
			elif msg == 0b000000001010_0_011:
				self._printer(f"Hitting with current item...")
				self._petition_handler.hit()
			elif msg == 0b000000001011_0_011:
				self._printer(f"Using current item...")
				self._petition_handler.use()
			elif msg == 0b000000001100_0_011:
				pos = ConnectorHelper.readPosition(client_socket)
				self._printer(f"Placing current block at {pos}...")
				self._petition_handler.place_block(pos)
			elif msg == 0b000000001101_0_011:
				uuid = ConnectorHelper.readString(client_socket)
				self._printer(f"Hitting entity with uuid={uuid}...")
				self._petition_handler.attack(uuid)
			elif msg == 0b000000001111_0_011:
				camera_id = self._petition_handler.start_recording()
				self._printer(f"Starting recording (id {camera_id})")
				# response
				ConnectorHelper.sendShort(client_socket, 0b000000001111_1_011)
				ConnectorHelper.sendShort(client_socket, camera_id)
			elif msg == 0b000000010000_0_011:
				camera_id = ConnectorHelper.readShort(client_socket)
				self._printer(f"Stopping recording {camera_id}")
				file_name = ClientConnector._random_mp4()
				self._petition_handler.stop_recording(camera_id, file_name)
				# response
				ConnectorHelper.sendShort(client_socket, 0b000000010000_1_011)
				ConnectorHelper.sendFile(client_socket, file_name)
				os.remove(file_name)
			else:
				self._printer("Unknown request: " + str(msg))
		self._socket = None # socket closed
	
	def close(self):
		self._closed = True # TODO sync
		self.socket.close()

	def message_received(self, username: str, msg: str):
		if self._socket == None:
			return # no one to send
		
		ConnectorHelper.sendShort(self._socket, 0b000000000011_1_011)
		ConnectorHelper.sendString(self._socket, username)
		ConnectorHelper.sendString(self._socket, msg)

	@staticmethod
	def _random_mp4(size: int = 15) -> str:
		return ''.join(random.choice(string.ascii_letters) for x in range(size)) + '.mp4'