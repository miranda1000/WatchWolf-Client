#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from threading import Lock

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
		self.socket = None
		self._socket = None
		self._closed = False
		self._socket_lock = Lock()
	
	def run(self):
		try:
			with self._socket_lock:
				if self._closed:
					return
				self.socket = listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				listener.bind(("0.0.0.0", self._port))
				listener.listen(5)
				# Also bound the wait on platforms where shutdown cannot interrupt accept.
				listener.settimeout(0.5)

			while not self._closed:
				try:
					client_socket, address = listener.accept()
				except socket.timeout:
					continue
				with self._socket_lock:
					if self._closed:
						self._close_socket(client_socket)
						return
					self._socket = client_socket
				client_socket.settimeout(None)
				self._serve(client_socket)
				break
		except OSError:
			if not self._closed:
				raise
		finally:
			self.close()

	def _serve(self, client_socket):
		while not self._closed:
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
				ConnectorHelper.sendShort(client_socket, 0b000000000100_1_011)
				ConnectorHelper.sendString(client_socket, reply)
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
	
	def close(self):
		with self._socket_lock:
			if self._closed:
				return
			self._closed = True
			listener, client_socket = self.socket, self._socket
			self.socket = self._socket = None
		# Closing the listener alone leaves the worker blocked reading the accepted socket.
		self._close_socket(client_socket)
		self._close_socket(listener)

	@staticmethod
	def _close_socket(sock):
		if sock is None:
			return
		try:
			sock.shutdown(socket.SHUT_RDWR)
		except OSError:
			pass # not connected, or already shut down
		finally:
			try:
				sock.close()
			except OSError:
				pass

	def message_received(self, username: str, msg: str):
		with self._socket_lock:
			client_socket = self._socket
		if client_socket is None:
			return # no one to send
		
		try:
			ConnectorHelper.sendShort(client_socket, 0b000000000011_1_011)
			ConnectorHelper.sendString(client_socket, username)
			ConnectorHelper.sendString(client_socket, msg)
		except OSError:
			if not self._closed:
				raise

	@staticmethod
	def _random_mp4(size: int = 15) -> str:
		return ''.join(random.choice(string.ascii_letters) for x in range(size)) + '.mp4'
