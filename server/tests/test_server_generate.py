import asyncio
import json
import threading
import pytest
import websockets
from PIL import Image

import server.main as srv
from server.protocol import image_to_b64

HOST, PORT = "127.0.0.1", 8798


class FakePipeline:
    def txt2img(self, prompt, variants=4, on_progress=None):
        if on_progress:
            on_progress(0.5)
        return [Image.new("RGBA", (1024, 1024), (255, 0, 0, 255))
                for _ in range(variants)]

    def img2img(self, prompt, image, strength=0.6, variants=4,
                on_progress=None):
        return [image.resize((1024, 1024))] * variants

    def inpaint(self, prompt, image, mask, variants=4, on_progress=None):
        return [image.resize((1024, 1024))] * variants


@pytest.fixture()
def server_thread(monkeypatch):
    monkeypatch.setattr(srv, "PIPELINE_FACTORY", FakePipeline)
    monkeypatch.setattr(srv, "_pipeline", None)
    loop = asyncio.new_event_loop()
    stop = loop.create_future()
    ready = threading.Event()

    def run():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(srv.serve(HOST, PORT, stop, on_ready=ready.set))

    t = threading.Thread(target=run, daemon=True)
    t.start()
    assert ready.wait(5)
    yield
    loop.call_soon_threadsafe(stop.set_result, None)
    t.join(timeout=5)


def test_generate_returns_progress_then_result(server_thread):
    async def go():
        async with websockets.connect(f"ws://{HOST}:{PORT}",
                                      max_size=64 * 2**20) as ws:
            await ws.send(json.dumps({
                "id": "g1", "mode": "generate", "prompt": "sword",
                "target_size": [32, 32], "variants": 2, "frames": [],
            }))
            msgs = []
            while True:
                msg = json.loads(await ws.recv())
                msgs.append(msg)
                if msg["type"] in ("result", "error"):
                    return msgs
    msgs = asyncio.run(go())
    assert msgs[-1]["type"] == "result"
    assert len(msgs[-1]["images"]) == 2
    assert any(m["type"] == "progress" for m in msgs)


def test_edit_roundtrip(server_thread):
    src = Image.new("RGBA", (16, 16), (0, 200, 0, 255))
    async def go():
        async with websockets.connect(f"ws://{HOST}:{PORT}",
                                      max_size=64 * 2**20) as ws:
            await ws.send(json.dumps({
                "id": "e1", "mode": "edit", "prompt": "greener",
                "target_size": [16, 16], "variants": 1,
                "frames": [{"image": image_to_b64(src), "mask": None}],
            }))
            while True:
                msg = json.loads(await ws.recv())
                if msg["type"] in ("result", "error"):
                    return msg
    msg = asyncio.run(go())
    assert msg["type"] == "result" and len(msg["images"]) == 1
