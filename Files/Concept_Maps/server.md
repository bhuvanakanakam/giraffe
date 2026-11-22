# Concept map: server.py

**Author:** Ayush Jain  
**Team:** 404NotFound  
**Milestone:** M2 Networked  
**Files:** `server.py`, with `protocol.py` and `board.py`  
**AI assistance:** ChatGPT helped draft the server, test request handling, and write this concept map.

`server.py` loads the boards from `data/` and serves one TCP client at a time. Each request goes through the shared protocol. The server uses the existing board methods to check rules and saves changes before replying with success.

## Summary table

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| M2-R1 · TCP server | server.py: 159–164, 171–183 | `TCPServer` listens on the configured address and gives each connection to `RequestHandler`. Every connection uses the same board store. |
| M2-R2 · Server owns the state | server.py: 48–57, 179 | `BoardStore` loads every board with `load_board()` at startup and remembers its original file by board name. |
| M2-R2 · Save before replying | server.py: 72–107 | The server changes a copy, saves it, then puts the updated board into the store. A failed save leaves the original board available for the next request. |
| M2-R3 · One JSON object per line | server.py: 123–156 | `protocol.read_message()` reads a full line. `protocol.encode()` adds a newline to each reply before the server sends it. |
| M2-R4 · Six request types | server.py: 59–97 | The shared protocol checks the action and fields. The server handles `list_boards`, `get_board`, `claim`, `move`, `add_comment`, and `add_item`. The README lists their fields and reply formats. |
| M2-R5 · JSON serialization | server.py: 61–70, 97–100, 129–150 | The protocol and domain helpers turn messages, boards, and items into the JSON shapes the client expects. |
| M2-R6 · Errors and disconnects | server.py: 117–156 | A bad request gets an error reply. A malformed JSON line leaves the connection open. A framing error closes that connection after the reply, and the listener can accept another client. |
| M2-R7 · Reuse M1 rules | server.py: 69–102 | `Board` still decides whether a claim, move, comment, or new item is valid. The server handles the network and decides when to save. |

## Optional depth

| Concept | Where (file: lines) | Why it is needed here |
|---|---|---|
| `--host` and `--port` | server.py: 171–176 | The server and client default to the same address from `protocol.py`. |
| Request/response logging | server.py: 129–166, 186–187 | The existing logging setup writes `[timestamp] message` entries with separate `REQUEST` and `RESPONSE` lines. Both include the client address and action; the response entry records the success outcome, error name, or send error, and is written after the reply is sent when sending succeeds. |

## Each concept in detail

### 1. Reading and changing a board

`list_boards` returns the loaded board names. `get_board` returns a board in the same shape as its save file. A change starts from a copy of the current board, runs through the relevant `Board` method, and builds a reply with the updated item.

### 2. Saving before the client sees success

The server checks that the reply fits in one message. It then calls `Board.save()` with the original file path. After the save succeeds, the server uses the updated board for the next request and sends the success reply. If the server restarts, `load_board()` reads the saved change back in.

### 3. Keeping the server running

A complete line with invalid JSON gets an error reply, and the handler can read the next line. A line that is too long or cut off gets a framing error reply and ends that connection. If the client disconnects while the server is replying, the handler logs the connection error and returns so the listener can take the next connection.
