from server.pipeline import clamp_prompt, PROMPT_SUFFIX


class FakeTokenizer:
    """Whitespace tokenizer standing in for CLIP's BPE."""
    class _Out:
        def __init__(self, ids):
            self.input_ids = ids

    def __call__(self, text, add_special_tokens=True):
        return self._Out(text.split())

    def decode(self, ids):
        return " ".join(ids)


def test_short_prompt_passes_through():
    tok = FakeTokenizer()
    out = clamp_prompt("a red sword", "suffix words", [tok], budget=75)
    assert out == "a red sword" + "suffix words"


def test_long_prompt_is_clipped_but_suffix_survives():
    tok = FakeTokenizer()
    prompt = " ".join(f"w{i}" for i in range(100))
    suffix = " s1 s2 s3"
    out = clamp_prompt(prompt, suffix, [tok], budget=75)
    assert out.endswith(suffix)          # style suffix always reaches CLIP
    assert len(out.split()) <= 75        # total fits the token budget
    assert out.startswith("w0 w1")       # user's leading words kept


def test_real_suffix_fits_default_budget():
    tok = FakeTokenizer()
    out = clamp_prompt("x " * 200, PROMPT_SUFFIX, [tok])
    assert out.endswith(PROMPT_SUFFIX)
