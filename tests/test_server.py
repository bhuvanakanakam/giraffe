"""Tests for server.py request handling and TCP replies."""

import os
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from board import Board  # noqa: E402
from items import Chore, User, WorkflowStage  # noqa: E402
import protocol  # noqa: E402
from server import BoardStore, GiraffeServer  # noqa: E402


def write_test_board(folder: str) -> Path:
    board = Board("Chores")
    board.add_user(User("ana", "Ana"))
    for stage in ("Unclaimed", "To Do", "In Progress", "Done"):
        board.add_stage(WorkflowStage(stage))
    board.add_item(Chore("c1", "Take out trash", due_date="2026-11-20",
                         stage="Unclaimed"))
    path = Path(folder) / "chores.json"
    board.save(str(path))
    return path


class TestBoardStore(unittest.TestCase):
    def test_claim_moves_unclaimed_item_to_to_do(self):
        with tempfile.TemporaryDirectory() as folder:
            write_test_board(folder)
            store = BoardStore(Path(folder))

            response = store.handle_request(protocol.make_request(
                "claim", board="Chores", item_id="c1", user_id="ana"))

            self.assertTrue(response["ok"])
            self.assertEqual(response["data"]["stage"], "To Do")
            self.assertEqual(store.boards["Chores"].get_item("c1").stage,
                             "To Do")


class TestGiraffeServer(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        write_test_board(self.folder.name)
        self.server = GiraffeServer(
            ("127.0.0.1", 0), BoardStore(Path(self.folder.name)))
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.folder.cleanup()

    def test_success_and_error_replies(self):
        address = self.server.server_address
        with socket.create_connection(address, timeout=2) as client, \
                client.makefile("rb") as stream:
            protocol.send_message(client, protocol.make_request("list_boards"))
            self.assertEqual(protocol.read_message(stream),
                             protocol.ok_response(["Chores"]))

            claim = protocol.make_request(
                "claim", board="Chores", item_id="c1", user_id="ana")
            protocol.send_message(client, claim)
            response = protocol.read_message(stream)
            self.assertTrue(response["ok"])
            self.assertEqual(response["data"]["stage"], "To Do")

            protocol.send_message(client, claim)
            response = protocol.read_message(stream)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"], "AlreadyClaimedError")

    def test_logs_request_and_response(self):
        with self.assertLogs("server", level="INFO") as captured:
            address = self.server.server_address
            with socket.create_connection(address, timeout=2) as client, \
                    client.makefile("rb") as stream:
                protocol.send_message(
                    client, protocol.make_request("list_boards"))
                protocol.read_message(stream)

        self.assertTrue(any("REQUEST" in line and "action=list_boards" in line
                            for line in captured.output))
        self.assertTrue(any("RESPONSE" in line and "outcome=ok" in line
                            for line in captured.output))


if __name__ == "__main__":
    unittest.main()
