import io
import unittest

from ClientConnector import ClientConnector
from ConnectorHelper import ConnectorHelper
from Position import Position
from items.Item import Item
from items.ItemType import ItemType


class LocalPetitionHandler:
	def __init__(self):
		self.calls = []

	def get_position(self):
		self.calls.append("position")
		return Position("world", 1.25, 64.0, -8.5)

	def get_pitch(self):
		self.calls.append("pitch")
		return -12.5

	def get_yaw(self):
		self.calls.append("yaw")
		return 92.25

	def get_inventory(self):
		self.calls.append("inventory")
		return [Item(ItemType.STONE, 3), Item(ItemType.DIAMOND, 1)]


class MemorySocket:
	def __init__(self, received=b""):
		self.received = io.BytesIO(received)
		self.sent = io.BytesIO()

	def recv(self, size):
		return self.received.read(size)

	def sendall(self, data):
		self.sent.write(data)


class ClientLocalPetitionsShould(unittest.TestCase):
	def setUp(self):
		self.handler = LocalPetitionHandler()
		self.connector = ClientConnector(self.handler, 0, lambda _: None)

	def assert_response(self, response, operation):
		self.assertEqual(operation << 4 | 0b1_011, ConnectorHelper.readShort(response))

	def test_serves_player_state_without_a_server_petition(self):
		requests = b"".join((operation << 4 | 0b011).to_bytes(2, "little")
			for operation in range(17, 21))
		wire = MemorySocket(requests)
		self.connector._serve(wire)
		response = MemorySocket(wire.sent.getvalue())

		self.assert_response(response, 17)
		self.assertEqual(Position("world", 1.25, 64.0, -8.5), ConnectorHelper.readPosition(response))

		self.assert_response(response, 18)
		self.assertEqual(-12.5, ConnectorHelper.readDouble(response))

		self.assert_response(response, 19)
		self.assertEqual(92.25, ConnectorHelper.readDouble(response))

		self.assert_response(response, 20)
		items = [ConnectorHelper.readItem(response)
			for _ in range(ConnectorHelper.readShort(response))]
		self.assertEqual([Item(ItemType.STONE, 3), Item(ItemType.DIAMOND, 1)], items)

		self.assertEqual(["position", "pitch", "yaw", "inventory"], self.handler.calls)


if __name__ == "__main__":
	unittest.main()
