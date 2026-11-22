"""
client.py - the program a person runs to use Giraffe over the network.

Author:  Prithvi Sunilkumar
Team:    404NotFound (Ayush Jain, Bhuvana Kanakam, Prithvi Sunilkumar)
Course:  95-895 Python Systems Fundamentals, Fall 2026, Mini 2
Part of: M2 Networked

What lives here:
  - GiraffeClient: one TCP connection to the server; sends a request and
    waits for its reply
  - ServerConnectionError: raised when the server is down, too slow, or
    drops the connection, so the menu can print a clear message
  - The same menu as demo.py's interactive mode, but every action is a
    request to the server instead of a call on a local Board

The client never changes a board itself and never reads the save files.
All JSON goes through protocol.py.

Run with: python client.py [--host HOST] [--port PORT]
(start the server first: python server.py)

AI use: I used Claude to help draft this file. I reviewed and ran every
line and can explain all of it. Cited in the README.
"""

from __future__ import annotations

import argparse
import socket

import protocol

TIMEOUT_SECONDS = 5


class ServerConnectionError(ConnectionError):
    """Raised when the client can't reach the server or loses it.

    It is a ConnectionError (the lecture's family for refused, reset and
    closed connections), not a Giraffe domain error: the client only knows
    the protocol, never the board or item classes.
    """


# ---------------------------------------------------------------------------
# The connection
# ---------------------------------------------------------------------------

class GiraffeClient:
    """One connection to the Giraffe server.

    Every low-level socket problem is turned into a ServerConnectionError
    with a message a person can understand, so the menu never shows a
    traceback.
    """

    def __init__(self, host: str = protocol.DEFAULT_HOST,
                 port: int = protocol.DEFAULT_PORT,
                 timeout: float = TIMEOUT_SECONDS) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None
        self._stream = None

    def connect(self) -> None:
        try:
            self._sock = socket.create_connection((self.host, self.port),
                                                  timeout=self.timeout)
        except ConnectionRefusedError as e:
            raise ServerConnectionError(
                f"Server is not running at {self.host}:{self.port}") from e
        except socket.timeout as e:
            raise ServerConnectionError(
                f"Server at {self.host}:{self.port} did not answer in time") from e
        except OSError as e:
            raise ServerConnectionError(
                f"Could not connect to {self.host}:{self.port}: {e}") from e
        # makefile gives us readline(), which protocol.read_message needs
        self._stream = self._sock.makefile("rb")

    def request(self, action: str, **fields) -> dict:
        """Send one request and return the server's reply dict.

        A rejected request (like a full column) is a normal reply with
        "ok": False. Only connection problems raise.
        """
        if self._sock is None:
            raise ServerConnectionError("Not connected to the server")
        try:
            protocol.send_message(self._sock, protocol.make_request(action, **fields))
            reply = protocol.read_message(self._stream)
        except socket.timeout as e:
            # The reply may still arrive later and would be read as the
            # answer to the next request, so this connection can't be reused.
            self.close()
            raise ServerConnectionError("Server did not answer in time") from e
        except (OSError, protocol.FramingError) as e:
            # ConnectionResetError, BrokenPipeError and friends are all
            # OSErrors; FramingError means the reply was cut off midway.
            self.close()
            raise ServerConnectionError("Server closed the connection") from e
        except protocol.ProtocolError as e:
            self.close()
            raise ServerConnectionError(f"Server sent a bad reply: {e}") from e

        if reply is None:  # the server hung up cleanly
            self.close()
            raise ServerConnectionError("Server closed the connection")
        return reply

    def close(self) -> None:
        for resource in (self._stream, self._sock):
            if resource is not None:
                try:
                    resource.close()
                except OSError:
                    pass
        self._stream = None
        self._sock = None


# ---------------------------------------------------------------------------
# Showing replies
# ---------------------------------------------------------------------------

# Fields every item has. Anything else in an item's JSON (points, due_date,
# company, applicant) is specific to its kind.
COMMON_FIELDS = ("kind", "item_id", "title", "description", "stage", "owner", "history")


def describe_item(item: dict) -> str:
    """One line for an item from a reply, built only from its JSON.

    The client never imports the item classes, so it shows each kind's own
    fields generically instead of checking the kind with if/elif. A new
    kind of item needs no change here.
    """
    extras = ", ".join(f"{key}: {value}" for key, value in item.items()
                       if key not in COMMON_FIELDS)
    extras = f" ({extras})" if extras else ""
    owner = item.get("owner") or "unassigned"
    return (f"[{item.get('kind')}] {item.get('item_id')} {item.get('title')}"
            f"{extras} | {item.get('stage')} | {owner}")


def show_board(board: dict) -> None:
    """Print a board reply grouped by column, like Board.describe()."""
    print(f"\nBoard: {board['name']}")
    for stage in board["stages"]:
        items = [data for data in board["items"] if data.get("stage") == stage["name"]]
        limit = "unlimited" if stage["limit"] is None else stage["limit"]
        print(f"\n{stage['name']} ({len(items)}/{limit})")
        if not items:
            print("  (empty)")
        for item in items:
            print(f"  {describe_item(item)}")


def show_result(reply: dict) -> None:
    """Print an item reply, or why the server rejected the request."""
    if reply.get("ok"):
        print("OK:", describe_item(reply["data"]))
    else:
        print("Rejected:", reply.get("message", "unknown error"))


# ---------------------------------------------------------------------------
# Menu actions
# Each one asks for its inputs and returns (action, fields) for a request.
# A dict maps the menu number to the action, the same idea as ITEM_KINDS
# and REQUEST_FIELDS, so there is no if/elif on the choice.
# ---------------------------------------------------------------------------

def ask_claim(board: dict) -> tuple[str, dict]:
    item_id = input("Item ID: ").strip()
    print("Users:", ", ".join(user["user_id"] for user in board["users"]))
    return "claim", {"item_id": item_id, "user_id": input("User ID: ").strip()}


def ask_move(board: dict) -> tuple[str, dict]:
    item_id = input("Item ID: ").strip()
    print("Stages:", ", ".join(stage["name"] for stage in board["stages"]))
    return "move", {"item_id": item_id, "stage": input("Destination stage: ").strip()}


def ask_comment(board: dict) -> tuple[str, dict]:
    item_id = input("Item ID: ").strip()
    return "add_comment", {"item_id": item_id, "text": input("Comment: ").strip()}


MENU_ACTIONS = {
    "1": ("Claim item", ask_claim),
    "2": ("Move item", ask_move),
    "3": ("Add comment", ask_comment),
}


def choose_board(client: GiraffeClient) -> str | None:
    """Ask the server for its boards and let the user pick one by number."""
    reply = client.request("list_boards")
    if not reply.get("ok"):
        print("Rejected:", reply.get("message"))
        return None
    names = reply["data"]

    print("\n=== Choose a board ===")
    for number, name in enumerate(names, start=1):
        print(f"{number}. {name}")
    print("0. Quit")
    choice = input("Board: ").strip()
    if choice == "0":
        return None
    if not choice.isdigit() or not 1 <= int(choice) <= len(names):
        print(f"Please enter a number from 0 to {len(names)}.")
        return ""
    return names[int(choice) - 1]


def use_board(client: GiraffeClient, name: str) -> None:
    """Show one board and send the user's actions until they go back."""
    while True:
        reply = client.request("get_board", board=name)
        if not reply.get("ok"):
            print("Rejected:", reply.get("message"))
            return
        board = reply["data"]
        show_board(board)

        print()
        for number, (label, _) in MENU_ACTIONS.items():
            print(f"{number}. {label}")
        print("0. Choose another board")
        choice = input("Action: ").strip()
        if choice == "0":
            return
        if choice not in MENU_ACTIONS:
            print("Please enter 1, 2, 3, or 0.")
            continue

        _, ask = MENU_ACTIONS[choice]
        action, fields = ask(board)
        show_result(client.request(action, board=name, **fields))


def run(client: GiraffeClient) -> None:
    while True:
        name = choose_board(client)
        if name is None:
            return
        if name:
            use_board(client, name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Giraffe client")
    parser.add_argument("--host", default=protocol.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=protocol.DEFAULT_PORT)
    args = parser.parse_args(argv)

    client = GiraffeClient(args.host, args.port)
    try:
        client.connect()
        print(f"Connected to {args.host}:{args.port}")
        run(client)
        print("Goodbye!")
        return 0
    except ServerConnectionError as e:
        # Down, too slow, or dropped: one clear line, no traceback.
        print(f"Error: {e}")
        return 1
    except (KeyError, TypeError) as e:
        # A reply was valid JSON but not the shape the protocol promises.
        print(f"Error: server sent a reply the client could not read: {e!r}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
