"""Premise-grounding assertion (cairn-thin-substrate-direction D2.5 keystone).

A contract/intent clause that cites a source must quote it verbatim; the
validator diffs the quoted text against the live source, so a stale,
fabricated, or drifted premise breaks the build. This is the rent-collector
for the one scope nothing else checks — the claim — and the mechanical defense
against the slice-#25 wrong-premise failure (no layer reads source to challenge
a premise).

Exercised through the public `_run_assertion` dispatcher so the test also pins
the type wiring. Before implementation, an unknown type falls through to
``return None`` — so the discriminating ``*_fails`` cases fail correctly (a
stale premise that should break the build silently passes).
"""

from validate_architecture import _run_assertion


def _assertion(premises: list[dict]) -> dict:
    return {"type": "premise-grounding", "premises": premises}


def test_grounded_premise_passes(tmp_path):
    (tmp_path / "src.py").write_text("def resolve_root():\n    return Path.cwd()\n")
    result = _run_assertion(
        tmp_path,
        "INV-TEST",
        _assertion([{"source": "src.py", "quote": "def resolve_root():"}]),
    )
    assert result is None


def test_stale_premise_fails(tmp_path):
    # The cited source no longer contains the quoted premise — slice-#25 catch.
    (tmp_path / "src.py").write_text("def resolve_root(start):\n    return start\n")
    result = _run_assertion(
        tmp_path,
        "INV-TEST",
        _assertion([{"source": "src.py", "quote": "def resolve_root():"}]),
    )
    assert result is not None
    assert "INV-TEST" in result
    assert "src.py" in result


def test_missing_source_fails(tmp_path):
    result = _run_assertion(
        tmp_path,
        "INV-TEST",
        _assertion([{"source": "gone.py", "quote": "anything"}]),
    )
    assert result is not None
    assert "gone.py" in result


def test_multiple_premises_one_stale_fails(tmp_path):
    (tmp_path / "a.py").write_text("ALPHA = 1\n")
    (tmp_path / "b.py").write_text("BETA = 2\n")
    result = _run_assertion(
        tmp_path,
        "INV-TEST",
        _assertion(
            [
                {"source": "a.py", "quote": "ALPHA = 1"},
                {"source": "b.py", "quote": "BETA = 99"},  # stale
            ]
        ),
    )
    assert result is not None
    assert "b.py" in result


def test_all_premises_grounded_passes(tmp_path):
    (tmp_path / "a.py").write_text("ALPHA = 1\n")
    (tmp_path / "b.py").write_text("BETA = 2\n")
    result = _run_assertion(
        tmp_path,
        "INV-TEST",
        _assertion(
            [
                {"source": "a.py", "quote": "ALPHA = 1"},
                {"source": "b.py", "quote": "BETA = 2"},
            ]
        ),
    )
    assert result is None
