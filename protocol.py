"""
protocol.py - the message format Giraffe's server and client share

Author:  Bhuvana Kanakam (bkanakam)
Team:    404NotFound (Ayush Jain, Bhuvana Kanakam, Prithvi Sunilkumar)
Course:  95-895 Python Systems Fundamentals, Fall 2026, Mini 2
Part of: M2 Networked

What lives here:
  - Framing: one JSON object per line over TCP (read_message, send_message)
  - The list of requests the server accepts and the fields each one needs
  - Building success and error responses
  - Turning a Board into JSON for replies (board_to_dict)

Everything that converts between Python objects and JSON for the network
happens in this file, so server.py and client.py never call json directly.

AI use: I used Claude to help structure this file. I reviewed and
tested every part, and can explain all of it. Cited in the README.
"""

from __future__ import annotations

import json
import socket
from typing import Any, BinaryIO

from board import Board
from errors import GiraffeError

# A message is one JSON object followed by "\n". json.dumps escapes any
# newline inside a string as \n, so a real newline byte can only ever mean
# "end of message".
ENCODING = "utf-8"
MAX_MESSAGE_BYTES = 64 * 1024  # stops one huge line from eating the server's memory

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050


class ProtocolError(GiraffeError):
    """Raised when a message is not valid Giraffe protocol.

    It inherits from GiraffeError, so the server can answer a malformed
    request and a broken board rule with the same error response.
    After a ProtocolError the connection is still usable: the bad line was
    read completely, so the next line is the next message.
    """


class FramingError(ProtocolError):
    """Raised when a message's boundaries are broken (too long, or cut off).

    The rest of that line may still be sitting in the socket, so the reader
    can't find where the next message starts. The server should send an
    error response and then close this connection.
    """


# ---------------------------------------------------------------------------
# Requests
# Each action maps to the fields it needs and their types. The server looks
# the action up here instead of using an if/elif chain, and adding a request
# is one new line.
# ---------------------------------------------------------------------------

REQUEST_FIELDS: dict[str, dict[str, type]] = {
    "list_boards": {},
    "get_board":   {"board": str},
    "claim":       {"board": str, "item_id": str, "user_id": str},
    "move":        {"board": str, "item_id": str, "stage": str},
    "add_comment": {"board": str, "item_id": str, "text": str},
    "add_item":    {"board": str, "item": dict},
}


def make_request(action: str, **fields: Any) -> dict:
    """Build a request dict, for example make_request("claim", board=..., ...)."""
    return {"action": action, **fields}


def validate_request(message: dict) -> tuple[str, dict]:
    """Check a request's shape and return (action, fields).

    Raises ProtocolError for an unknown action, a missing field, a field of
    the wrong type, or an extra field. This only checks the message's shape;
    Board still checks the rules (one owner, column limits).
    """
    action = message.get("action")
    if not isinstance(action, str) or action not in REQUEST_FIELDS:
        raise ProtocolError(f"unknown action: {action!r}")

    expected = REQUEST_FIELDS[action]
    fields = {k: v for k, v in message.items() if k != "action"}

    missing = [name for name in expected if name not in fields]
    if missing:
        raise ProtocolError(f"{action} is missing {', '.join(missing)}")

    extra = [name for name in fields if name not in expected]
    if extra:
        raise ProtocolError(f"{action} does not take {', '.join(extra)}")

    for name, kind in expected.items():
        if not isinstance(fields[name], kind):
            raise ProtocolError(f"{action}: {name} must be a {kind.__name__}")

    return action, fields


# ---------------------------------------------------------------------------
# Responses
# Success:  {"ok": true,  "data": ...}
# Failure:  {"ok": false, "error": "StageFullError", "message": "..."}
# "error" is the exception's class name, so the client can tell a full
# column from a double claim without parsing the message text.
# ---------------------------------------------------------------------------

def ok_response(data: Any = None) -> dict:
    return {"ok": True, "data": data}


def error_response(error: Exception) -> dict:
    return {"ok": False, "error": type(error).__name__, "message": str(error)}


def board_to_dict(board: Board) -> dict:
    """The same shape Board.save() writes, so a reply and a save file match.

    Uses only Board's public, read-only properties, so building a reply can
    never change the board.
    """
    return {
        "name": board.name,
        "users": [user.to_dict() for user in board.users],
        "stages": [stage.to_dict() for stage in board.stages],
        "items": [item.to_dict() for item in board.items],
    }


# ---------------------------------------------------------------------------
# Framing: one JSON object per line
# ---------------------------------------------------------------------------

def encode(message: dict) -> bytes:
    """dict -> one line of UTF-8 JSON ending in a newline."""
    data = json.dumps(message, separators=(",", ":")).encode(ENCODING) + b"\n"
    if len(data) > MAX_MESSAGE_BYTES:
        raise ProtocolError(f"message is larger than {MAX_MESSAGE_BYTES} bytes")
    return data


def decode(line: bytes) -> dict:
    """One line of bytes -> dict. Raises ProtocolError if it isn't a JSON object."""
    try:
        message = json.loads(line.decode(ENCODING))
    except UnicodeDecodeError as e:
        raise ProtocolError("message is not valid UTF-8") from e
    except json.JSONDecodeError as e:
        raise ProtocolError(f"message is not valid JSON: {e.msg}") from e
    if not isinstance(message, dict):
        raise ProtocolError("message must be a JSON object")
    return message


def send_message(sock: socket.socket, message: dict) -> None:
    """Send one message. sendall keeps writing until every byte is out."""
    sock.sendall(encode(message))


def read_message(stream: BinaryIO) -> dict | None:
    """Read the next message from sock.makefile("rb").

    Returns None when the other side closed the connection cleanly.
    Raises FramingError for an oversized or cut-off message (close the
    connection after replying) and ProtocolError for a malformed one (the
    connection can keep going).
    """
    # readline(limit) stops after limit bytes even with no newline, which is
    # how we notice a line that is too long without reading all of it
    line = stream.readline(MAX_MESSAGE_BYTES + 1)
    if line == b"":
        return None
    if len(line) > MAX_MESSAGE_BYTES:
        raise FramingError(f"message is larger than {MAX_MESSAGE_BYTES} bytes")
    if not line.endswith(b"\n"):
        raise FramingError("connection closed in the middle of a message")
    return decode(line)
