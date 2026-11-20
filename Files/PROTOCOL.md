# M2 build checklist: server.py and client.py

**Written by:** Bhuvana Kanakam · **Protocol:** see the README, section "Protocol (M2)" · **Code to use:** `protocol.py`

The protocol (framing, requests, replies, errors) is documented once, in the README. This file is the to-do list for the two parts still to build. Tick each box in your PR description.

## server.py (Ayush)

- [ ] **Load state at startup.** Load every `*.json` file in `data/` with `load_board(path)`. Keep a dict `{board.name: (board, path)}` so you can find a board by name and know which file to save it to. `data/` already has the two demo boards.
- [ ] **Listen** with `socket.create_server((host, port))` on `protocol.DEFAULT_HOST` / `DEFAULT_PORT`. One client at a time is fine for M2.
- [ ] **Per connection:** `stream = conn.makefile("rb")`, then loop `message = protocol.read_message(stream)`. `None` means the client left, so close and wait for the next one.
- [ ] **Per request:** `action, fields = protocol.validate_request(message)`, then call a handler for that action. Use a dict `{"claim": handle_claim, ...}` keyed like `protocol.REQUEST_FIELDS`, not if/elif.
- [ ] **Unknown board name** → `raise NotFoundError(f"Board {name!r} does not exist")`.
- [ ] **Save before replying.** After `claim`, `move`, `add_comment` or `add_item` succeeds, call `board.save(path)`, then reply. `list_boards` and `get_board` don't save.
- [ ] **Replies:** `protocol.ok_response(item.to_dict())` for item actions (use `board.get_item(item_id)` after the change), `protocol.board_to_dict(board)` for `get_board`, a list of names for `list_boards`.
- [ ] **Errors:** wrap the request handling in `except GiraffeError as e: send_message(conn, error_response(e))`. This also catches `ProtocolError`.
- [ ] **`except FramingError`** (put it before `except GiraffeError`): reply, then close that connection.
- [ ] **Never crash on one client:** catch `ConnectionResetError` / `BrokenPipeError` around the per-connection loop and move on to the next client.
- [ ] Optional depth: `argparse` for `--host` / `--port`, and `logging` of every request (action, board, ok or error name).

## client.py (Prithvi)

- [ ] **Connect** with `socket.create_connection((host, port), timeout=5)` and `stream = sock.makefile("rb")`.
- [ ] **Send** with `protocol.send_message(sock, protocol.make_request("claim", board=..., item_id=..., user_id=...))`, then `reply = protocol.read_message(stream)`.
- [ ] **Show results:** if `reply["ok"]`, print the item or board; otherwise print `Rejected: {reply["message"]}` and let the user keep going.
- [ ] **Connection problems, no tracebacks:**
  - `ConnectionRefusedError` → "Server is not running at host:port"
  - `socket.timeout` → "Server did not answer in time"
  - `read_message` returns `None`, or `ConnectionResetError` → "Server closed the connection"
- [ ] **Menu:** reuse the flow from `demo.py`'s interactive mode (pick a board, then claim / move / comment), but every action becomes a request. Board lists come from `list_boards` and `get_board`.
- [ ] Optional depth: `argparse` for `--host` / `--port`.

## board.py `save()` (Prithvi, Sean's M1 feedback)

- [ ] **Keep the old file if a save is interrupted.** Write the JSON to `path + ".tmp"` in the same folder, then `os.replace(tmp, path)`. `os.replace` swaps the file in one step, so the file on disk is always either the old board or the new one, never half of each. Delete the `.tmp` file if writing fails. M3 requires this too.
- [ ] **README:** one sentence on what `save()` guarantees: "A save either fully replaces the board file or leaves the previous version untouched."

## Before we merge (everyone)

- [ ] Fill your TODO rows in the README's M2 concept map and "Who built what" table, with line numbers from your final code.
- [ ] Write your concept map file in `Files/Concept_Maps/` (copy the layout of `protocol.md`).
- [ ] `python -m unittest discover tests` passes, and the run steps in the README work from a fresh clone.
