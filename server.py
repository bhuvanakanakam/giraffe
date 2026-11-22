"""
server.py - Network server for Giraffe.

Author:  Ayush Jain (ayushjain_01)
Team:    404NotFound (Ayush Jain, Bhuvana Kanakam, Prithvi Sunilkumar)
Course:  95-895 Python Systems Fundamentals, Fall 2026, Mini 2
Part of: M2 Networked

What lives here:
  - BoardStore: board loading, request handling, and saves
  - RequestHandler: JSON requests and replies over TCP
  - GiraffeServer: one client connection at a time

AI Use: ChatGPT helped draft the server and test request handling.
Cited in the README.
"""

from __future__ import annotations

import argparse
import logging
import socketserver
from copy import deepcopy
from pathlib import Path

import protocol
from board import Board, load_board
from errors import (
    DuplicateIDError,
    GiraffeError,
    InvalidBoardError,
    InvalidItemError,
    NotFoundError,
)
from items import item_from_dict


DATA_DIRECTORY = Path(__file__).resolve().parent / "data"


# ---------------------------------------------------------------------------
# Loading boards and handling requests
# ---------------------------------------------------------------------------

class BoardStore:
    """Own the loaded boards and remember the file each board came from."""

    def __init__(self, data_directory: Path) -> None:
        self.boards: dict[str, Board] = {}
        self.paths: dict[str, Path] = {}
        # Keep the original path so we can save each board back to its own file.
        for path in sorted(data_directory.glob("*.json")):
            board = load_board(str(path))
            if board.name in self.boards:
                raise DuplicateIDError(f"Duplicate board name: {board.name!r}")
            self.boards[board.name] = board
            self.paths[board.name] = path

    def handle_request(self, message: dict) -> dict:
        """Validate a request and return the data for its success reply."""
        action, fields = protocol.validate_request(message)
        if action == "list_boards":
            return protocol.ok_response(list(self.boards))

        name = fields["board"]
        if name not in self.boards:
            raise NotFoundError(f"Board {name!r} does not exist")
        board = self.boards[name]
        if action == "get_board":
            return protocol.ok_response(protocol.board_to_dict(board))

        # Change a copy first. If saving fails, the next client should still
        # see the old board.
        updated = deepcopy(board)
        if action == "add_item":
            item_data = fields["item"]
            # Check the text fields before handing the dict to item_from_dict().
            # A list in "kind", for example, would break the item lookup.
            if not isinstance(item_data.get("description", ""), str):
                raise InvalidItemError("item description must be text")
            for field in ("kind", "stage", "owner"):
                value = item_data.get(field)
                if value is not None and not isinstance(value, str):
                    raise InvalidItemError(f"item {field} must be text")
            item = item_from_dict(item_data)
            updated.add_item(item)
            item_id = item.item_id
        else:
            item_id = fields["item_id"]
            if action == "claim":
                updated.claim(item_id, fields["user_id"])
            elif action == "move":
                updated.move(item_id, fields["stage"])
            elif action == "add_comment":
                updated.add_comment(item_id, fields["text"])

        response = protocol.ok_response(updated.get_item(item_id).to_dict())
        # The reply has to fit in one protocol message. Check that before
        # saving so we don't write a change and then send back a size error.
        protocol.encode(response)
        try:
            updated.save(str(self.paths[name]))
        except OSError as error:
            raise InvalidBoardError("Could not save board") from error
        # The save worked, so use the updated board for the next request.
        self.boards[name] = updated
        return response


# ---------------------------------------------------------------------------
# TCP connections and replies
# ---------------------------------------------------------------------------

class RequestHandler(socketserver.StreamRequestHandler):
    """Read and answer one JSON line at a time for the connected client."""

    def handle(self) -> None:
        try:
            self.serve_requests()
        except OSError as error:
            logging.info("Connection from %s ended: %s", self.client_address, error)

    def serve_requests(self) -> None:
        while True:
            close_connection = False
            action = "<unreadable>"
            try:
                try:
                    message = protocol.read_message(self.rfile)
                except (ValueError, RecursionError) as error:
                    raise protocol.ProtocolError("message is not valid JSON") from error
                if message is None:
                    return
                requested_action = message.get("action")
                if (isinstance(requested_action, str)
                        and requested_action in protocol.REQUEST_FIELDS):
                    action = requested_action
                response = self.server.store.handle_request(message)
                payload = protocol.encode(response)
            except GiraffeError as error:
                # A bad JSON line is already out of the stream. A framing
                # error means we don't know where the next line starts.
                close_connection = isinstance(error, protocol.FramingError)
                response = protocol.error_response(error)
                try:
                    payload = protocol.encode(response)
                except protocol.ProtocolError:
                    # A long field can make the error reply too big as well.
                    response["message"] = "The request was rejected"
                    payload = protocol.encode(response)

            logging.info("%s %s: %s", self.client_address, action,
                         "ok" if response["ok"] else response["error"])
            self.request.sendall(payload)
            if close_connection:
                return


class GiraffeServer(socketserver.TCPServer):
    """Serve one client at a time with a single shared board store."""

    def __init__(self, address: tuple[str, int], store: BoardStore) -> None:
        self.store = store
        super().__init__(address, RequestHandler)


# ---------------------------------------------------------------------------
# Running the server
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Giraffe TCP server")
    parser.add_argument("--host", default=protocol.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=protocol.DEFAULT_PORT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        store = BoardStore(DATA_DIRECTORY)
        with GiraffeServer((args.host, args.port), store) as server:
            host, port = server.server_address
            logging.info("Listening on %s:%s with %s boards",
                         host, port, len(store.boards))
            server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped")
    except (GiraffeError, OSError, OverflowError, UnicodeError) as error:
        parser.exit(1, f"Could not start Giraffe server: {error}\n")


if __name__ == "__main__":
    main()
