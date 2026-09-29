#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from items.Item import Item
from Position import Position
from entities.Entity import Entity
from typing import List

class ClientPetition:
	def send_message(self, msg: str):
		pass
		
	def send_command(self, cmd: str, timeout: int) -> str:
		pass
	
	def break_block(self, block: Position):
		pass
	
	def place_block(self, block: Position):
		pass
	
	def equip_item_in_hand(self, item: Item):
		pass
	
	def move_to(self, pos: Position):
		pass
	
	def look_at(self, pitch: float, yaw: float):
		pass
	
	def synchronize(self):
		pass
	
	def hit(self):
		pass
	
	def use(self):
		pass

	def attack(self, uuid: str):
		pass

	def get_position(self) -> Position:
		pass

	def get_pitch(self) -> float:
		pass

	def get_yaw(self) -> float:
		pass

	def get_inventory(self) -> List[Item]:
		pass

	def start_recording(self) -> int:
		pass

	def stop_recording(self, id: int, out: str):
		pass
