"""
tests/test_protocol.py - checks for protocol.py and the M2 history fix

Author:  Bhuvana Kanakam (bkanakam)
Run from the project folder:  python -m unittest discover tests

AI use: I used Claude to help write these tests. I reviewed and ran all of
them and can explain each one. Cited in the README.
"""

import io
import json
import os
import socket
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from board import Board, load_board  # noqa: E402
from errors import GiraffeError, InvalidItemError, StageFullError  # noqa: E402
from items import Chore, User, WorkflowStage, item_from_dict  # noqa: E402
import protocol  # noqa: E402
from protocol import FramingError, ProtocolError  # noqa: E402


def small_board() -> Board:
    board = Board("Chores")
    board.add_user(User("ana", "Ana"))
    board.add_stage(WorkflowStage("Open"))
    board.add_stage(WorkflowStage("Done", limit=1))
    board.add_item(Chore("c1", "Trash", due_date="2026-11-20", stage="Open"))
    return board


def claim_board() -> Board:
    board = Board("Chores")
    board.add_user(User("ana", "Ana"))
    board.add_stage(WorkflowStage("Unclaimed"))
    board.add_stage(WorkflowStage("To Do"))
    board.add_item(Chore("c1", "Trash", due_date="2026-11-20", stage="Unclaimed"))
    return board


class TestFraming(unittest.TestCase):
    def test_round_trip(self):
        message = {"action": "claim", "board": "Chores", "item_id": "c1", "user_id": "ana"}
        stream = io.BytesIO(protocol.encode(message))
        self.assertEqual(protocol.read_message(stream), message)

    def test_one_message_per_line_even_with_newlines_in_text(self):
        message = {"action": "add_comment", "board": "Chores", "item_id": "c1",
                   "text": "line one\nline two"}
        data = protocol.encode(message)
        self.assertEqual(data.count(b"\n"), 1)
        self.assertTrue(data.endswith(b"\n"))
        self.assertEqual(protocol.read_message(io.BytesIO(data)), message)

    def test_two_messages_back_to_back(self):
        stream = io.BytesIO(protocol.encode({"a": 1}) + protocol.encode({"b": 2}))
        self.assertEqual(protocol.read_message(stream), {"a": 1})
        self.assertEqual(protocol.read_message(stream), {"b": 2})
        self.assertIsNone(protocol.read_message(stream))

    def test_clean_close_returns_none(self):
        self.assertIsNone(protocol.read_message(io.BytesIO(b"")))

    def test_cut_off_message(self):
        with self.assertRaises(FramingError):
            protocol.read_message(io.BytesIO(b'{"action": "list_b'))

    def test_oversized_message(self):
        line = b"x" * (protocol.MAX_MESSAGE_BYTES + 10) + b"\n"
        with self.assertRaises(FramingError):
            protocol.read_message(io.BytesIO(line))

    def test_bad_json_keeps_connection_usable(self):
        stream = io.BytesIO(b"not json\n" + protocol.encode({"action": "list_boards"}))
        with self.assertRaises(ProtocolError) as caught:
            protocol.read_message(stream)
        self.assertNotIsInstance(caught.exception, FramingError)
        self.assertEqual(protocol.read_message(stream), {"action": "list_boards"})

    def test_json_that_is_not_an_object(self):
        for line in (b"[1, 2]\n", b'"hi"\n', b"42\n"):
            with self.assertRaises(ProtocolError):
                protocol.read_message(io.BytesIO(line))

    def test_bad_utf8(self):
        with self.assertRaises(ProtocolError):
            protocol.read_message(io.BytesIO(b"\xff\xfe\n"))


class TestRequests(unittest.TestCase):
    def test_every_action_accepts_its_fields(self):
        samples = {
            "list_boards": {},
            "get_board": {"board": "Chores"},
            "claim": {"board": "Chores", "item_id": "c1", "user_id": "ana"},
            "move": {"board": "Chores", "item_id": "c1", "stage": "Done"},
            "add_comment": {"board": "Chores", "item_id": "c1", "text": "hi"},
            "add_item": {"board": "Chores", "item": {"kind": "chore"}},
        }
        self.assertEqual(set(samples), set(protocol.REQUEST_FIELDS))
        for action, fields in samples.items():
            got_action, got_fields = protocol.validate_request(
                protocol.make_request(action, **fields))
            self.assertEqual((got_action, got_fields), (action, fields))

    def test_rejections(self):
        bad = [
            {},                                                      # no action
            {"action": "delete_everything"},                         # unknown action
            {"action": 5},                                           # action not text
            {"action": "claim", "board": "Chores", "item_id": "c1"},  # missing user_id
            {"action": "claim", "board": "Chores", "item_id": "c1",
             "user_id": 7},                                          # wrong type
            {"action": "list_boards", "board": "Chores"},            # extra field
        ]
        for message in bad:
            with self.subTest(message=message):
                with self.assertRaises(ProtocolError):
                    protocol.validate_request(message)

    def test_protocol_errors_are_giraffe_errors(self):
        self.assertTrue(issubclass(ProtocolError, GiraffeError))
        self.assertTrue(issubclass(FramingError, ProtocolError))


class TestResponses(unittest.TestCase):
    def test_claim_moves_unclaimed_item_to_to_do(self):
        board = claim_board()
        board.claim("c1", "ana")
        item = board.get_item("c1")
        self.assertEqual(item.owner, "ana")
        self.assertEqual(item.stage, "To Do")

    def test_ok(self):
        self.assertEqual(protocol.ok_response([1]), {"ok": True, "data": [1]})

    def test_error_uses_class_name(self):
        reply = protocol.error_response(StageFullError("Stage 'Done' has reached its limit"))
        self.assertEqual(reply, {"ok": False, "error": "StageFullError",
                                 "message": "Stage 'Done' has reached its limit"})

    def test_board_to_dict_matches_save_file(self):
        board = small_board()
        board.claim("c1", "ana")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "b.json")
            board.save(path)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(protocol.board_to_dict(board), json.load(f))

    def test_board_to_dict_does_not_change_board(self):
        board = small_board()
        before = protocol.board_to_dict(board)
        before["items"][0]["owner"] = "mallory"
        self.assertIsNone(board.get_item("c1").owner)


class TestHistoryValidation(unittest.TestCase):
    """Sean's M1 feedback: validate saved item history when loading."""

    def load_with_history(self, history):
        board = small_board()
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "b.json")
            board.save(path)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data["items"][0]["history"] = history
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return load_board(path)

    def test_bad_history_rejected(self):
        for history in ("oops", {"a": 1}, [1, None], ["ok", 3]):
            with self.subTest(history=history):
                with self.assertRaises(InvalidItemError):
                    self.load_with_history(history)

    def test_missing_or_unknown_fields_are_giraffe_errors(self):
        for data in ({"kind": "chore"},
                     {"kind": "task", "item_id": "t", "title": "x", "points": 1, "colour": "red"}):
            with self.subTest(data=data):
                with self.assertRaises(InvalidItemError):
                    item_from_dict(data)

    def test_good_history_loads(self):
        board = self.load_with_history(["owner set to ana", "Comment: hi"])
        self.assertEqual(board.get_item("c1").history,
                         ["owner set to ana", "Comment: hi"])


class TestOverRealSocket(unittest.TestCase):
    """Sends messages through an actual TCP connection on localhost."""

    def test_socket_round_trip(self):
        server = socket.create_server(("127.0.0.1", 0))
        port = server.getsockname()[1]
        received = []

        def echo_once():
            conn, _ = server.accept()
            with conn, conn.makefile("rb") as stream:
                while (message := protocol.read_message(stream)) is not None:
                    received.append(message)
                    protocol.send_message(conn, protocol.ok_response(message))

        thread = threading.Thread(target=echo_once)
        thread.start()
        requests = [protocol.make_request("list_boards"),
                    protocol.make_request("add_comment", board="Chores",
                                          item_id="c1", text="multi\nline")]
        with socket.create_connection(("127.0.0.1", port), timeout=5) as client, \
                client.makefile("rb") as stream:
            for request in requests:
                protocol.send_message(client, request)
                self.assertEqual(protocol.read_message(stream),
                                 protocol.ok_response(request))
        thread.join(timeout=5)
        server.close()
        self.assertEqual(received, requests)


if __name__ == "__main__":
    unittest.main()
