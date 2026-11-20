# Concept map: protocol.py

**Author:** Bhuvana Kanakam (bkanakam)
**Team:** 404NotFound
**Milestone:** M2 Networked
**File:** `protocol.py` (188 lines), tested by `tests/test_protocol.py` (214 lines)
**AI assistance:** Claude helped structure this file, its tests and this concept map. I reviewed and tested all of it and can explain every line.

`protocol.py` is the message format the server and the client share. It decides where one message ends and the next begins, which requests exist and what fields each needs, what a reply looks like, and how a board is turned into JSON. `server.py` and `client.py` both import it, so neither one calls `json` or builds bytes itself.

Requirement numbers (M2-R1 to M2-R7) follow the M2 section of the project guide. Line numbers match the version submitted with M2.

---

## Summary table

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| M2-R3 · Message framing: one JSON object per line | protocol.py: 31-38, 145-150, 166-168 | TCP is a stream of bytes with no message boundaries, so we end every message with `\n`. `json.dumps` writes a newline inside text as the two characters `\n`, so a real newline byte can only mean "end of message", even when a comment has several lines. `sendall` keeps writing until every byte is out. |
| M2-R3 · Reading one message at a time | protocol.py: 171-188 | `read_message()` reads up to the next newline. An empty read means the other side closed the connection cleanly, so it returns `None` instead of raising. |
| M2-R3 · Size limit | protocol.py: 35, 148-149, 181-185 | Without a limit, one client could send a line with no newline and make the server keep reading forever. `readline(limit)` stops at 64 KB, so we can reject it without reading the rest. |
| M2-R4 · The list of requests, in code | protocol.py: 67-74 | `REQUEST_FIELDS` names every action and the fields and types it needs. The README's protocol table is written from it, so the documentation and the code can't drift apart. |
| M2-R4 · Checking a request's shape | protocol.py: 82-108 | `validate_request()` rejects an unknown action, a missing field, an extra field or a wrong type before the server touches the board. It looks the action up in `REQUEST_FIELDS` instead of using if/elif, the same idea as `ITEM_KINDS` in items.py, so adding a request is one line. |
| M2-R5 · JSON in one clear place | protocol.py: 119-124, 127-138, 145-163 | Every conversion between Python objects and JSON for the network is in this file: `encode` / `decode` for messages, `ok_response` / `error_response` for replies, `board_to_dict` for boards. The server and client never call `json` directly. |
| M2-R5 · Replies use the save file's format | protocol.py: 127-138 | `board_to_dict()` returns the same shape `Board.save()` writes, so the team learns one JSON format. It reads only Board's read-only properties, which return copies, so building a reply can never change the board. |
| M2-R6 · Errors become replies, not crashes | protocol.py: 41-48, 123-124 | `ProtocolError` inherits from `GiraffeError`, so the server catches a malformed request and a broken board rule with the same `except GiraffeError` and answers both with `error_response()`. The reply's `"error"` is the exception's class name (for example `StageFullError`), so the client can react to the kind of failure without reading the message text. |
| M2-R6 · Bad input never crashes the reader | protocol.py: 153-163 | Bad UTF-8, broken JSON, and JSON that isn't an object (like `[1, 2]`) all become `ProtocolError`. The bad line was read completely, so the connection can keep going. |
| M2-R6 · Knowing when to drop a connection | protocol.py: 51-57, 183-187 | After an oversized or cut-off message, the leftover bytes are still in the socket and the next message's start can't be found. `FramingError` tells the server to reply and then close that connection, instead of misreading everything that follows. |
| M2-R7 · Networking kept out of the domain classes | protocol.py: whole file | `board.py`, `items.py` and `errors.py` are reused from M1 with no socket or network code added. `protocol.py` only reads `Board` through its public methods, and the domain rules stay in `Board`. |
| M2-R2 · Server can trust what it loads | items.py: 152-156, 180-192 | The server loads its state from JSON at startup, so a damaged file must not load quietly. A saved `"history": "oops"` used to become `['o', 'o', 'p', 's']`; now `load_board()` raises `InvalidItemError`. Added from Sean's M1 feedback. |

## Optional depth

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| Default host and port in one place | protocol.py: 37-38 | Server and client import the same defaults, so they can't disagree. The `--host` / `--port` flags in server.py and client.py fall back to these. |
| Tests for the protocol | tests/test_protocol.py: 38-214 | 20 tests cover framing (multi-line text, two messages back to back, clean close, cut-off and oversized lines), every request and every rejection, both reply shapes, the history fix, and a real round trip over a TCP socket on localhost. Run with `python -m unittest discover tests`. |
| Type hints | protocol.py: throughout | Every function states what it takes and returns, which makes the contract with server.py and client.py clear. |

---

## Each concept in detail

### 1. Framing (lines 31-38, 145-188)

```python
data = json.dumps(message, separators=(",", ":")).encode(ENCODING) + b"\n"
```

```
{"action":"add_comment","board":"Chores","item_id":"c1","text":"line one\nline two"}\n
```

The `\n` inside the comment is two characters, a backslash and an `n`. The only real newline byte is the last one, which ends the message. `tests/test_protocol.py` checks this with a multi-line comment.

| What `read_message()` sees | What it does |
|---|---|
| A full line | Returns the message as a dict |
| Nothing (`b""`) | Returns `None`: the other side closed cleanly |
| More than 64 KB with no newline | Raises `FramingError`: reply, then close |
| Bytes but no newline, then the connection ends | Raises `FramingError`: the message was cut off |
| A full line that isn't a JSON object | Raises `ProtocolError`: reply, keep the connection |

### 2. Requests as a table (lines 67-108)

```python
REQUEST_FIELDS = {
    "list_boards": {},
    "get_board":   {"board": str},
    "claim":       {"board": str, "item_id": str, "user_id": str},
    "move":        {"board": str, "item_id": str, "stage": str},
    "add_comment": {"board": str, "item_id": str, "text": str},
    "add_item":    {"board": str, "item": dict},
}
```

`validate_request()` only checks the shape of a request. Whether the claim is allowed (is the item free? is the user a member?) is still Board's job. Keeping the two apart means the network layer never duplicates a board rule.

### 3. Replies (lines 119-138)

```json
{"ok": true,  "data": {"kind": "chore", "item_id": "c1", "owner": "ayush", "...": "..."}}
{"ok": false, "error": "AlreadyClaimedError", "message": "Item 'c1' already belongs to 'prithvi'"}
```

`"ok"` is checked first, so the client never has to guess whether `data` is there.

### 4. The error family (lines 41-57)

```
GiraffeError
├── ProtocolError      bad message, connection continues
│   └── FramingError   broken message boundaries, close the connection
├── StageFullError, AlreadyClaimedError, NotFoundError, ...   (errors.py)
```

---

## Which files use protocol.py

| Used by | What they call |
|---|---|
| `server.py` (Ayush) | `read_message`, `validate_request`, `ok_response`, `error_response`, `board_to_dict`, `send_message`, `ProtocolError`, `FramingError`, `DEFAULT_HOST`, `DEFAULT_PORT` |
| `client.py` (Prithvi) | `make_request`, `send_message`, `read_message`, `DEFAULT_HOST`, `DEFAULT_PORT` |
| `tests/test_protocol.py` (Bhuvana) | everything above |

`protocol.py` uses `board.Board` (for `board_to_dict`) and `errors.GiraffeError`.

---

## Check-in talking points

1. **Why newline framing?** TCP has no message boundaries. A newline is simple to read with `readline`, and JSON never puts a real newline inside a message.
2. **Why a size limit?** So one client sending a line with no newline can't make the server read forever.
3. **Why a table of requests instead of if/elif?** Adding a request is one line, and the README table comes straight from it.
4. **Why is `ProtocolError` a `GiraffeError`?** One `except GiraffeError` in the server turns any failure, bad message or broken rule, into an error reply.
5. **Why both `ProtocolError` and `FramingError`?** After bad JSON the connection is still in sync. After a too-long or cut-off line it isn't, so the server must close it.
6. **Where does JSON happen?** Only in this file. Server and client never call `json`.
