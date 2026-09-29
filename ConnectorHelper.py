#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from items.Item import Item
from Position import Position
from items.ItemType import ItemType
from entities.EntityType import EntityType
from entities.Entity import Entity

import os
from struct import pack, unpack
from typing import List

class ConnectorHelper:
	@staticmethod
	def readString(socket) -> str:
		size = ConnectorHelper.readShort(socket)
		if size == 0:
			return ""
		data = socket.recv(size)
		return ''.join([chr(e) for e in data])
	
	@staticmethod
	def sendString(socket, data: str):
		size = min(len(data), 65535) # 2 bytes for the size
		ConnectorHelper.sendShort(socket, size)
		if size > 0:
			socket.sendall(b''.join([bytes([ord(e)]) for e in data[:size]])) # convert the string characters (from 0 to size-1) into an array of bytes
	
	@staticmethod
	def readShort(socket) -> int:
		first = socket.recv(1)
		if not first: raise Exception("Socket closed")
		lsb = int(first[0])
		msb = int(socket.recv(1)[0])
		return (msb<<8) | lsb
	
	@staticmethod
	def sendShort(socket, data: int):
		lsb = bytes([data & 0b11111111])
		msb = bytes([(data >> 8) & 0b11111111]) # AND just in case
		socket.sendall(b''.join([lsb, msb]))
	
	@staticmethod
	def readDouble(socket) -> float:
		double = socket.recv(8)
		return unpack('>d', double)[0]
	
	@staticmethod
	def sendDouble(socket, data: float):
		socket.sendall(pack('>d', data))
	
	@staticmethod
	def readItem(socket) -> Item:
		type = ItemType(ConnectorHelper.readShort(socket))
		amount = int(socket.recv(1)[0])
		return Item(type, amount)
	
	@staticmethod
	def sendItem(socket, item: Item):
		ConnectorHelper.sendShort(socket, item.type.value)
		socket.sendall(bytes([item.amount]))

	@staticmethod
	def sendItems(socket, items: List[Item]):
		ConnectorHelper.sendShort(socket, len(items))
		for item in items:
			ConnectorHelper.sendItem(socket, item)
	
	@staticmethod
	def readEntity(socket) -> Entity:
		type = EntityType(ConnectorHelper.readShort(socket))
		pos = ConnectorHelper.readPosition(socket)
		uuid = ConnectorHelper.readString(socket)
		# TODO create the fitting class instance
		if type == EntityType.DROPPED_ITEM:
			ConnectorHelper.readItem(socket) # we need to discard the item
		return Entity(uuid, pos)
	
	@staticmethod
	def sendEntity(socket, entity: Entity):
		pass # TODO
	
	@staticmethod
	def readPosition(socket) -> Position:
		world = ConnectorHelper.readString(socket)
		x = ConnectorHelper.readDouble(socket)
		y = ConnectorHelper.readDouble(socket)
		z = ConnectorHelper.readDouble(socket)
		return Position(world, x, y, z)
	
	@staticmethod
	def sendPosition(socket, pos: Position):
		ConnectorHelper.sendString(socket, pos.world)
		ConnectorHelper.sendDouble(socket, pos.x)
		ConnectorHelper.sendDouble(socket, pos.y)
		ConnectorHelper.sendDouble(socket, pos.z)
	
	@staticmethod
	def sendFile(socket, path: str):
		ConnectorHelper.sendString(socket, path) # TODO get only the file name, not the full path
		ConnectorHelper.sendString(socket, './')

		# size
		size = os.stat(path).st_size
		llsb = bytes([size & 0b11111111])
		mlsb = bytes([(size >> 8) & 0b11111111])
		lmsb = bytes([(size >> 16) & 0b11111111])
		mmsb = bytes([(size >> 24) & 0b11111111])
		socket.sendall(b''.join([llsb, mlsb, lmsb, mmsb]))

		# file data
		BUFFER_SIZE = 1024
		with open(path, "rb") as f:
			while True:
				bytes_read = f.read(BUFFER_SIZE)
				if not bytes_read:
					break
				socket.sendall(bytes_read)
