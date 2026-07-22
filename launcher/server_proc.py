"""Running the server subprocess and reading its state."""
import asyncio
import json
import pathlib
import re
import socket
import subprocess
import sys
import threading

import websockets

from server.config import HOST

MAX_LINES = 500
_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
# no console window when a windowed exe spawns the server
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def clean_line(raw: str) -> str:
    # tqdm redraws its bar with \r; the log keeps only the final state
    return _ANSI.sub("", raw.split("\r")[-1]).rstrip()


def venv_python(root: pathlib.Path) -> pathlib.Path | None:
    candidate = pathlib.Path(root) / ".venv" / "Scripts" / "python.exe"
    return candidate if candidate.exists() else None


def port_is_free(port: int, host: str = HOST) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.5)
        return probe.connect_ex((host, port)) != 0


def pick_port(preferred: int) -> int:
    for candidate in range(preferred, preferred + 20):
        if port_is_free(candidate):
            return candidate
    return preferred


def probe(port: int, timeout: float = 2.0) -> dict:
    """The same ping the panel sends, so both agree on the state."""
    async def ask():
        url = f"ws://{HOST}:{port}"
        async with websockets.connect(url, open_timeout=timeout,
                                      ping_interval=None) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            raw = await asyncio.wait_for(ws.recv(), timeout)
            return json.loads(raw)

    offline = {"state": "offline", "progress": 0.0, "stage": None}
    try:
        pong = asyncio.run(ask())
    except Exception:
        return offline
    if not isinstance(pong, dict) or pong.get("type") != "pong":
        return offline
    ready = pong.get("model", "ready") == "ready"
    return {"state": "ready" if ready else "loading",
            "progress": float(pong.get("progress") or 0.0),
            "stage": pong.get("stage")}


class ServerProcess:
    def __init__(self, root, port: int, on_log):
        self.root = pathlib.Path(root)
        self.port = port
        self.on_log = on_log
        self.lines: list[str] = []
        self.proc: subprocess.Popen | None = None
        found = venv_python(self.root)
        self.python = str(found) if found else sys.executable
        self.args = ["-u", "-m", "server.main"]

    def start(self) -> None:
        if self.is_alive():
            return
        self.proc = subprocess.Popen(
            [self.python, *self.args], cwd=str(self.root),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            creationflags=_NO_WINDOW)
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        proc = self.proc
        if not proc or not proc.stdout:
            return
        for raw in proc.stdout:
            line = clean_line(raw)
            if not line:
                continue
            self.lines.append(line)
            del self.lines[:-MAX_LINES]
            self.on_log(line)

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def wait_for_exit(self, timeout: float = 10) -> None:
        if self.proc:
            self.proc.wait(timeout=timeout)

    def stop(self) -> None:
        if not self.is_alive():
            return
        proc = self.proc
        assert proc
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
