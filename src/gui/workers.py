"""Background work helpers: the buttplug/asyncio bridge, plus the Qt
equivalent of the old Tk build's `root.after(0, callback, *args)` pattern
for marshaling a background thread's result onto the GUI thread.
"""
from __future__ import annotations

import asyncio
import threading
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot


class AsyncBridge:
    """Runs an asyncio event loop on a background thread so the Qt main
    loop never blocks on I/O. Ported unchanged from the Tk build - this
    class never had a Tk dependency to begin with."""

    def __init__(self):
        """Create a fresh event loop and immediately start a daemon thread running it forever (see _run)."""
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Thread target: make `self.loop` this thread's event loop and run it forever (until stop() is called)."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro):
        """
        Schedule a coroutine to run on the bridge's loop from any thread
        (typically the Qt main thread, from a button handler) and return a
        concurrent.futures.Future for it. Callers attach a callback with
        `.add_done_callback(...)`, or just use the module-level `submit()`
        helper below, which marshals the result back to the Qt main thread
        automatically.
        """
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop(self):
        """Stop the background event loop - call once, on app shutdown."""
        self.loop.call_soon_threadsafe(self.loop.stop)


class MainThreadRelay(QObject):
    """
    Marshals a background-thread callback onto the Qt main thread - the Qt
    equivalent of Tk's `root.after(0, callback, *args)`. A Qt signal
    emitted from a non-GUI thread and connected with the default
    (auto/queued) connection type is delivered via the receiver's own
    event loop, which is exactly the thread-safety guarantee this needs;
    a plain Python callback invoked directly from a background thread
    would not be safe to touch widgets from.

    One instance is created by MainWindow and passed down to every tab -
    same lifetime as AsyncBridge.
    """

    _relay = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._relay.connect(self._invoke)

    @Slot(object)
    def _invoke(self, func: Callable[[], None]):
        func()

    def call(self, func: Callable, *args, **kwargs) -> None:
        """Schedule func(*args, **kwargs) to run on the Qt main thread - safe to call from any thread."""
        self._relay.emit(lambda: func(*args, **kwargs))


def submit(bridge: AsyncBridge, relay: MainThreadRelay, coro, on_done: Callable):
    """
    Submit a coroutine to the bridge and marshal its result back to the Qt
    main thread via on_done(future) once it completes - the Qt equivalent
    of the Tk build's:
        fut = bridge.submit(coro)
        fut.add_done_callback(lambda f: root.after(0, on_done, f))

    `on_done` receives the concurrent.futures.Future; call `.result()` on
    it to get the coroutine's return value or re-raise its exception, same
    as every call site did under Tk.
    """
    fut = bridge.submit(coro)
    fut.add_done_callback(lambda f: relay.call(on_done, f))
    return fut


def run_in_thread(relay: MainThreadRelay, fn: Callable, on_done: Callable, *args, **kwargs):
    """
    Run fn(*args, **kwargs) on a daemon thread, then marshal its return
    value to on_done on the Qt main thread - the Qt equivalent of the Tk
    build's one-off `threading.Thread(target=worker, daemon=True).start()`
    + `root.after(0, on_done, result)` pattern (update checks, artwork
    fetches - blocking I/O that doesn't go through AsyncBridge).
    """
    def _target():
        result = fn(*args, **kwargs)
        relay.call(on_done, result)

    threading.Thread(target=_target, daemon=True).start()
