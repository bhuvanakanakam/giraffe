"""
tests/test_client.py - checks for client.py and the safe save in board.py

Author:  Prithvi Sunilkumar
Run from the project folder:  python -m unittest discover tests

These tests use tiny fake servers on localhost, so they don't need
server.py to be running.

AI use: I used Claude to help write these tests. I reviewed and ran all of
them and can explain each one. Cited in the README.
"""

import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from board import Board, load_board  # noqa: E402
from errors import GiraffeError, InvalidBoardError  # noqa: E402
from items import Chore, User, WorkflowStage  # noqa: E402
import protocol  # noqa: E402
from client import GiraffeClient, ServerConnectionError  # noqa: E402


def small_board() -> Board:
    board = Board("Chores")
    board.add_user(User("ana", "Ana"))
    board.add_user(User("ben", "Ben"))
    board.add_stage(WorkflowStage("Open"))
    board.add_item(Chore("c1", "Trash", due_date="2026-11-20", stage="Open"))
    return board


# ---------------------------------------------------------------------------
# Safe save (Sean's M1 feedback)
# ---------------------------------------------------------------------------

class TestSafeSave(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "board.json")

    def tearDown(self):
        self.folder.cleanup()

    def test_save_and_load_leaves_no_temp_file(self):
        board = small_board()
        board.save(self.path)
        self.assertEqual(load_board(self.path), board)
        self.assertEqual(os.listdir(self.folder.name), ["board.json"])

    def test_failed_save_keeps_old_file(self):
        board = small_board()
        board.save(self.path)
        with open(self.path, encoding="utf-8") as f:
            before = f.read()

        board.claim("c1", "ana")
        # Pretend the computer failed right before the swap.
        with mock.patch("board.os.replace", side_effect=OSError("disk failed")):
            with self.assertRaises(InvalidBoardError):
                board.save(self.path)

        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(f.read(), before)          # old board untouched
        self.assertFalse(os.path.exists(self.path + ".tmp"))  # temp cleaned up
        self.assertIsNone(load_board(self.path).get_item("c1").owner)


# ---------------------------------------------------------------------------
# Fake servers for the client
# ---------------------------------------------------------------------------

def start_server(handle_connection):
    """Run handle_connection(conn) for one client on a free port."""
    server = socket.create_server(("127.0.0.1", 0))
    port = server.getsockname()[1]

    def run():
        conn, _ = server.accept()
        with conn:
            handle_connection(conn)
        server.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return port, thread


def board_server(conn):
    """A very small real server: answers claim and get_board on one board."""
    board = small_board()
    stream = conn.makefile("rb")
    handlers = {
        "get_board": lambda f: protocol.board_to_dict(board),
        "claim": lambda f: (board.claim(f["item_id"], f["user_id"]),
                            board.get_item(f["item_id"]).to_dict())[1],
    }
    while True:
        message = protocol.read_message(stream)
        if message is None:
            return
        try:
            action, fields = protocol.validate_request(message)
            reply = protocol.ok_response(handlers[action](fields))
        except GiraffeError as e:
            reply = protocol.error_response(e)
        protocol.send_message(conn, reply)


class TestClient(unittest.TestCase):
    def test_requests_and_rejections(self):
        port, thread = start_server(board_server)
        client = GiraffeClient(port=port, timeout=2)
        client.connect()
        try:
            reply = client.request("claim", board="Chores", item_id="c1", user_id="ana")
            self.assertTrue(reply["ok"])
            self.assertEqual(reply["data"]["owner"], "ana")

            # A broken rule is a normal reply, not an exception.
            reply = client.request("claim", board="Chores", item_id="c1", user_id="ben")
            self.assertFalse(reply["ok"])
            self.assertEqual(reply["error"], "AlreadyClaimedError")

            reply = client.request("get_board", board="Chores")
            self.assertEqual(reply["data"]["name"], "Chores")
        finally:
            client.close()
            thread.join(timeout=2)

    def test_server_not_running(self):
        # Grab a free port, then close it so nothing is listening there.
        with socket.create_server(("127.0.0.1", 0)) as s:
            port = s.getsockname()[1]
        client = GiraffeClient(port=port, timeout=1)
        with self.assertRaisesRegex(ServerConnectionError, "not running"):
            client.connect()

    def test_server_too_slow(self):
        port, thread = start_server(lambda conn: time.sleep(1))
        client = GiraffeClient(port=port, timeout=0.2)
        client.connect()
        with self.assertRaisesRegex(ServerConnectionError, "did not answer in time"):
            client.request("list_boards")
        thread.join(timeout=2)

    def test_server_drops_connection(self):
        port, thread = start_server(lambda conn: None)  # hangs up right away
        client = GiraffeClient(port=port, timeout=2)
        client.connect()
        thread.join(timeout=2)
        with self.assertRaisesRegex(ServerConnectionError, "closed the connection"):
            client.request("list_boards")

    def test_client_only_knows_the_protocol(self):
        # Lecture 6: the client never imports the domain model.
        self.assertTrue(issubclass(ServerConnectionError, ConnectionError))
        with open(os.path.join(os.path.dirname(__file__), "..", "client.py")) as f:
            source = f.read()
        for module in ("items", "board", "errors"):
            self.assertNotIn(f"from {module} import", source)
            self.assertNotIn(f"import {module}\n", source)


if __name__ == "__main__":
    unittest.main()
