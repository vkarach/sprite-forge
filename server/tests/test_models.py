import pytest
from server import models


@pytest.fixture(autouse=True)
def clean_manager():
    models.reset()
    yield
    models.reset()


class Counter:
    def __init__(self):
        self.made = 0

    def factory(self):
        self.made += 1
        return object()


def test_get_caches_resident_model():
    c = Counter()
    models.register("a", c.factory)
    first = models.get("a")
    assert models.get("a") is first
    assert c.made == 1


def test_switch_drops_old_and_loads_new():
    a, b = Counter(), Counter()
    models.register("a", a.factory)
    models.register("b", b.factory)
    obj_a = models.get("a")
    obj_b = models.get("b")
    assert obj_b is not obj_a
    assert (a.made, b.made) == (1, 1)
    # switching back constructs "a" again (old instance was dropped)
    models.get("a")
    assert a.made == 2


def test_stage_callback_reports_loading():
    stages = []
    models.register("a", Counter().factory)
    models.get("a", on_stage=stages.append)
    assert any("Loading" in s for s in stages)


def test_failed_load_leaves_manager_empty():
    models.register("bad", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    ok = Counter()
    models.register("ok", ok.factory)
    with pytest.raises(RuntimeError):
        models.get("bad")
    # manager is clean: a later get works and constructs fresh
    assert models.get("ok") is not None
    assert ok.made == 1


def test_unknown_name_raises_keyerror():
    with pytest.raises(KeyError):
        models.get("nope")
