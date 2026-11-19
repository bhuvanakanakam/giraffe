# Giraffe M2 protocol

**Author:** Bhuvana Kanakam (bkanakam) · **Status:** draft for the team to agree on · **Code:** `protocol.py`

This is the contract between `server.py` and `client.py`. Both sides use the helpers in `protocol.py`, so neither one calls `json` or builds byte strings directly. When the team agrees, this section moves into the README.

## Transport and framing

- **TCP sockets**, default `127.0.0.1:5050` (`protocol.DEFAULT_HOST`, `protocol.DEFAULT_PORT`).
- **One JSON object per line**, UTF-8, ending in `\n`. `json.dumps` turns any newline inside a string into the two characters `\n`, so a real newline byte only ever means "end of message".
- **Max 64 KB per message** (`protocol.MAX_MESSAGE_BYTES`), so one huge line can't use up the server's memory.
- The client sends one request and waits for one response before sending the next.

```python
# sending
protocol.send_message(sock, protocol.make_request("claim", board="Apartment 4B Chores",
                                                  item_id="c1", user_id="ayush"))
# receiving (stream = sock.makefile("rb"))
reply = protocol.read_message(stream)     # None means the other side closed the connection
```

## Requests

Every request has an `"action"` plus that action's fields, and nothing else. `protocol.validate_request()` checks this; an unknown action, a missing field, a wrong type or an extra field is a `ProtocolError`.

| Action | Fields | Changes state? | What the server does | `data` in the reply |
|---|---|---|---|---|
| `list_boards` | none | No | List the boards it holds | `["Apartment 4B Chores", "Amazon SDE Intern Referrals"]` |
| `get_board` | `board` | No | Find the board | The whole board, same shape as the save file (`protocol.board_to_dict`) |
| `claim` | `board`, `item_id`, `user_id` | Yes | `board.claim(item_id, user_id)`, then save | The updated item (`item.to_dict()`) |
| `move` | `board`, `item_id`, `stage` | Yes | `board.move(item_id, stage)`, then save | The updated item |
| `add_comment` | `board`, `item_id`, `text` | Yes | `board.add_comment(item_id, text)`, then save | The updated item |
| `add_item` | `board`, `item` (an object with `"kind"`) | Yes | `board.add_item(item_from_dict(item))`, then save | The new item |

Every field is a string except `item`, which is an object in the same format as an item in the save file:

```json
{"action": "add_item", "board": "Apartment 4B Chores",
 "item": {"kind": "chore", "item_id": "c4", "title": "Vacuum", "due_date": "2026-11-25", "stage": "Unclaimed"}}
```

## Responses

```json
{"ok": true,  "data": {"kind": "chore", "item_id": "c1", "owner": "ayush", "...": "..."}}
{"ok": false, "error": "AlreadyClaimedError", "message": "Item 'c1' already belongs to 'prithvi'"}
```

`error` is the exception's class name, so the client can tell a full column from a double claim without reading the message text. `protocol.ok_response(data)` and `protocol.error_response(exc)` build these.

## Errors the client can receive

| `error` | When | Comes from |
|---|---|---|
| `ProtocolError` | Not JSON, not an object, unknown action, missing, extra or wrong-type field | `protocol.py` |
| `FramingError` | Message over 64 KB, or the connection closed mid-message. **Server replies, then closes the connection** | `protocol.py` |
| `NotFoundError` | Unknown board, item, user or column | `board.py` |
| `AlreadyClaimedError` | Claiming an item that already has an owner | `board.py` |
| `StageFullError` | Moving or adding into a full column | `board.py` |
| `DuplicateIDError` | `add_item` with an ID that's taken | `board.py` |
| `InvalidItemError` | `add_item` with bad item data, or an unknown `kind` | `items.py` |
| `InvalidBoardError` | Empty comment, or the server couldn't save | `board.py` |

All of these inherit from `GiraffeError`.

## What each side must do

**Server (`server.py`)**

1. On start, load every board file with `load_board()`. A board is found by its name.
2. For each connection, loop on `read_message(stream)`. `None` means the client left.
3. Run `validate_request()`, look up the action, call the matching `Board` method.
4. After a request that changes state succeeds, save that board before replying. A change is confirmed only once it's saved.
5. Wrap steps 3 and 4 in `except GiraffeError as e:` and reply `error_response(e)`. One bad request never stops the server.
6. On `FramingError`, reply, then close that connection.
7. Optional depth: log every request (action, board, result).

**Client (`client.py`)**

1. Connect with `socket.create_connection((host, port), timeout=5)`.
2. Catch `ConnectionRefusedError` (server not running), `socket.timeout` (no reply) and `ConnectionResetError` / `None` from `read_message` (server went away). Print a clear message instead of a traceback.
3. Show `message` for any reply with `"ok": false`, and let the user keep going.
4. Optional depth: `--host` and `--port` flags with `argparse`.

## Why these choices

- **TCP with newline framing** over HTTP: it's what Week 4 taught, and it leads straight into M3's threaded server.
- **Requests checked against a table** (`REQUEST_FIELDS`) instead of if/elif, the same idea as `ITEM_KINDS`: adding a request is one line.
- **Errors by class name**: our exception family already names every rule, so the network layer reuses it.
- **Replies use the save file's shape**: one JSON format for files and messages, built from Board's read-only properties, so a reply can't change the board.
