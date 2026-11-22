# Concept map: client.py and the safe save

**Author:** Prithvi Sunilkumar
**Team:** 404NotFound
**Milestone:** M2 Networked
**Files:** `client.py` (285 lines), `board.py` `save()` (lines 287-320), tested by `tests/test_client.py` (174 lines)
**AI assistance:** Claude helped draft `client.py`, the safe save, the tests and this concept map. I reviewed and ran all of it and can explain every line.

`client.py` is the program a person runs to use Giraffe over the network. It shows the same menu as `demo.py`'s interactive mode, but every action becomes a request to the server. The client never changes a board and never touches the save files. It also handles a server that is down, slow, or hangs up, printing one clear line instead of a traceback.

The safe save is Sean's M1 feedback: `Board.save()` now writes to a temporary file and swaps it in, so a crash mid-save can't destroy the board.

Requirement numbers (M2-R1 to M2-R7) follow the M2 section of the project guide. Line numbers match the version submitted with M2.

---

## Summary table

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| M2-R1 · TCP client | client.py: 67-111 | `socket.create_connection` opens one connection with a 5-second timeout. `request()` sends a message with `protocol.send_message` and waits for its reply with `read_message` before the next one, so replies can't get mixed up. |
| M2-R1 · Menu as requests | client.py: 200-244 | Board names come from `list_boards`, the board from `get_board`, and claim / move / comment are requests. The client never calls `Board` methods; only the server changes boards. |
| M2-R1 · No if/elif on the menu choice | client.py: 176-197, 236-244 | `MENU_ACTIONS` maps each menu number to a function that asks for its inputs and returns `(action, fields)`. Adding an action is one line, the same idea as `ITEM_KINDS` and `REQUEST_FIELDS`. |
| M2-R2 · A crash during save keeps the old file | board.py: 305-320 | `save()` writes the JSON to `path + ".tmp"`, forces it to disk with `fsync`, then calls `os.replace`, which swaps the file in one step. The file on disk is always the whole old board or the whole new one. If writing fails, the temp file is deleted and `InvalidBoardError` is raised. |
| M2-R5 · JSON only through protocol.py | client.py: 92-93, 130-166 | The client never calls `json`. It builds requests with `make_request`, and replies arrive as dicts from `read_message`. |
| M2-R6 · Clear messages, not crashes | client.py: 37-43, 67-111, 269-276 | Each socket problem becomes a `ServerConnectionError` with a message a person can understand: "Server is not running", "did not answer in time", or "closed the connection". `main()` prints it on one line and exits. |
| M2-R6 · Rejections are normal replies | client.py: 161-166 | A broken rule comes back as `{"ok": false, ...}`, so the client prints `Rejected: ...` and the user keeps going. Only connection or protocol failures raise `ServerConnectionError`. |
| M2-R7 · Client only knows the protocol | client.py: 32, 37-43, 130-145 | Lecture 6's `reg_client.py` "never imports registrar.py": it only knows the protocol. Ours never imports `board.py`, `items.py` or `errors.py`. `describe_item()` prints each item straight from its JSON and shows kind-specific fields (points, due_date, company) generically, so there is no if/elif on kind and a new item kind needs no client change. A test checks the imports. |

## Optional depth

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| `--host` / `--port` flags | client.py: 256-260 | `argparse` lets the client reach a server on another machine or port. Defaults come from `protocol.py`, so client and server agree. |
| Tests | tests/test_client.py: 45-174 | 7 tests: a save leaves no temp file, a failed save keeps the old file, and the client against fake servers that answer, reject, are not running, are too slow, or hang up, plus a check that the client imports no domain module. Run `python -m unittest discover tests`. |
| Exception family | client.py: 37-43 | `ServerConnectionError` inherits from `ConnectionError`, the lecture's family for refused, reset and closed connections. It is not a `GiraffeError`, because it is about the network, not a board rule. |

---

## Each concept in detail

### 1. One request, one reply (lines 80-108)

```python
protocol.send_message(self._sock, protocol.make_request(action, **fields))
reply = protocol.read_message(self._stream)
```

The client sends one line and waits for one line back. A rejected request is still a normal reply (`"ok": false`), so `request()` returns it. It only raises when the connection itself is broken.

### 2. What can go wrong with the connection

| Problem | What Python raises | What the user sees |
|---|---|---|
| Server not started | `ConnectionRefusedError` | `Error: Server is not running at 127.0.0.1:5050` |
| Server takes over 5 seconds | `socket.timeout` | `Error: Server did not answer in time` |
| Server hangs up | `read_message` returns `None`, or `ConnectionResetError` | `Error: Server closed the connection` |
| Reply cut off midway | `FramingError` | `Error: Server closed the connection` |

After a timeout the client closes the connection. If the late reply arrived afterwards, it would be read as the answer to the next request.

### 3. The menu without if/elif (lines 156-177)

```python
MENU_ACTIONS = {
    "1": ("Claim item", ask_claim),
    "2": ("Move item", ask_move),
    "3": ("Add comment", ask_comment),
}
...
_, ask = MENU_ACTIONS[choice]
action, fields = ask(board)
show_result(client.request(action, board=name, **fields))
```

### 4. The safe save (board.py: 305-320)

```python
tmp_path = f"{path}.tmp"
with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(text)
    f.flush()
    os.fsync(f.fileno())
os.replace(tmp_path, path)
```

| Crash happens… | File on disk afterwards |
|---|---|
| Before or while writing the temp file | The old board, untouched |
| After `os.replace` | The new board, complete |

There is no moment where the real file is half written. **A save either fully replaces the board file or leaves the previous version untouched.**

---

## Which files client.py uses

| File | What client.py uses |
|---|---|
| `protocol.py` (Bhuvana) | `make_request`, `send_message`, `read_message`, `ProtocolError`, `FramingError`, `DEFAULT_HOST`, `DEFAULT_PORT` |
| `server.py` (Ayush) | The other end of the connection |

Nothing imports `client.py` except `tests/test_client.py`.

---

## Check-in talking points

1. **What does the client do?** It shows the menu and turns each choice into a request. Only the server changes boards.
2. **Why is a rejection not an exception in the client?** The server answered fine; it just said no. The user should see why and keep going.
3. **What happens if the server is down?** `ConnectionRefusedError` becomes "Server is not running at host:port", and the client exits cleanly.
4. **Why close the connection after a timeout?** A late reply would be mistaken for the answer to the next request.
5. **Why temp file + `os.replace`?** Writing straight to the real file and crashing halfway would leave a broken board that the server can't load. `os.replace` swaps in one step, so the file is always whole.
6. **Why doesn't the client import the item classes?** It should only know the protocol, like the lecture's client. The server could be rewritten in another language and this client would still work.
