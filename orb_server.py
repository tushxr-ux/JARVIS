"""
orb_server.py — Tiny WebSocket server that bridges JARVIS state to the Eclipse orb.
Uses only stdlib (asyncio + websockets if available, else falls back to silent no-op).
Port: 7474
Protocol: newline-delimited JSON  {"state":"LISTENING","amp":0.42}
"""
import asyncio
import json
import threading
from typing import Optional

_clients: set = set()
_loop: Optional[asyncio.AbstractEventLoop] = None
_available = False

try:
    import websockets  # type: ignore
    _available = True
except ImportError:
    pass


async def _handler(ws):
    _clients.add(ws)
    try:
        await ws.wait_closed()
    finally:
        _clients.discard(ws)


async def _serve():
    global _loop
    _loop = asyncio.get_event_loop()
    async with websockets.serve(_handler, "localhost", 7474):
        await asyncio.Future()   # run forever


def _run_server():
    asyncio.run(_serve())


def start():
    """Call once at startup to launch the WS server in a background daemon thread."""
    if not _available:
        return
    t = threading.Thread(target=_run_server, daemon=True)
    t.start()


def push(state: str, amp: float = 0.0):
    """Thread-safe: push state + amplitude to all connected orb clients."""
    if not _available or not _clients:
        return
    msg = json.dumps({"state": state, "amp": round(amp, 3)})
    # Fire-and-forget from any thread — schedule on the server event loop
    if _loop and not _loop.is_closed():
        asyncio.run_coroutine_threadsafe(_broadcast(msg), _loop)


async def _broadcast(msg: str):
    dead = set()
    for ws in list(_clients):
        try:
            await ws.send(msg)
        except Exception:
            dead.add(ws)
    _clients.difference_update(dead)
