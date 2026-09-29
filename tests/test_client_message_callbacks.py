import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class ClientMessageCallbacksShould(unittest.TestCase):
	def setUp(self):
		self.callbacks = {}

		# The bridge supplies the emitted event arguments, without a leading emitter.
		def on(emitter, event):
			def register(callback):
				self.callbacks[event] = callback
				return callback
			return register

		bridge = SimpleNamespace(require=Mock(return_value=Mock()), On=on, Once=Mock(), console=Mock())
		viewer = SimpleNamespace(MineflayerViewer=Mock())
		spec = importlib.util.spec_from_file_location("client_under_test",
			Path(__file__).resolve().parents[1] / "MineflayerClient.py")
		self.module = importlib.util.module_from_spec(spec)
		with patch.dict("sys.modules", {"javascript": bridge, "view.MineflayerViewer": viewer}):
			spec.loader.exec_module(self.module)

		# Register the real callbacks, but do not start sockets, login timers or a Minecraft bot.
		with patch.object(self.module, "Thread"), patch.object(self.module, "ClientConnector"):
			self.client = self.module.MineflayerClient("127.0.0.1", 25565, "user1", 7001, None, None)

	def test_returns_system_command_feedback(self):
		message = SimpleNamespace(toString=lambda: "Gave 1 Dirt to user1")
		self.client._cmd_return = ["stale reply"]
		self.client._bot.chat.side_effect = lambda command: self.callbacks["message"](message, "system", None)

		with patch.object(self.module, "sleep"):
			result = self.client.send_command("give user1 dirt 1", 1000)

		self.assertEqual("Gave 1 Dirt to user1", result)
		self.client._bot.chat.assert_called_once_with("/give user1 dirt 1")

	def test_keeps_multiple_system_messages_in_order(self):
		for text in ("first reply", "second reply"):
			message = SimpleNamespace(toString=lambda text=text: text)
			self.callbacks["message"](message, "system", None, False)
		self.assertEqual(["first reply", "second reply"], self.client._cmd_return)

	def test_does_not_treat_chat_or_action_bar_as_command_feedback(self):
		for position in ("chat", "game_info"):
			message = Mock()
			self.callbacks["message"](message, position, "sender-uuid", False)
			message.toString.assert_not_called()
		self.assertEqual([], self.client._cmd_return)

	def test_forwards_chat_username_and_message_without_shifting_arguments(self):
		self.callbacks["chat"]("user2", "hello", "chat.type.text", Mock(), [])
		self.client._connector.message_received.assert_called_once_with("user2", "hello")


if __name__ == "__main__":
	unittest.main()
