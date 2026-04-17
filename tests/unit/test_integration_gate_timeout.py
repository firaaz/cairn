"""Phase 2 validation tests for integration-gate/configurable-pytest-timeout.

Realizes the 10 verification checks from intent.md:

    1. CAIRN_PYTEST_TIMEOUT=300 → _run_step4b passes timeout=300
    2. CAIRN_RUFF_TIMEOUT=10 → _run_step4a passes timeout=10
    3. No env var → pytest timeout=120
    4. No env var → ruff timeout=60
    5. Empty string → default (both)
    6. Non-numeric → default
    7. "0" → default
    8. "-5" → default
    9. Silent fallback — invalid values produce no new stdout/stderr output
   10. Existing exit-code assertions still pass (covered by test_integration_gate.py)

Mocking posture (per approach.md): patch integration_gate.subprocess.run
directly and assert on the captured timeout= kwarg. Matches intent's minimal-
change contract — only behavior change is the timeout= kwarg on subprocess.run.

Phase 2 (Skeptic) posture: these tests MUST FAIL today. _run_step4a/b pass
hardcoded timeouts (60 and 120 respectively), so the env-override tests fail.
Phase 3 Builder will add env-var parsing to make them green without touching
the test file.
"""

import subprocess
from unittest.mock import patch

import pytest

import integration_gate


# --- Helpers ----------------------------------------------------------------


def _ok_result() -> subprocess.CompletedProcess:
    """Return a mocked CompletedProcess with returncode=0 and empty streams."""
    return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")


# --- Pytest timeout override (_run_step4b) ----------------------------------


class TestPytestTimeoutOverride:
    """CAIRN_PYTEST_TIMEOUT controls subprocess.run timeout for _run_step4b."""

    def test_env_override_applies(self, monkeypatch, tmp_path):
        """Check 1: CAIRN_PYTEST_TIMEOUT=300 → subprocess.run timeout=300."""
        monkeypatch.setenv("CAIRN_PYTEST_TIMEOUT", "300")
        with patch(
            "integration_gate.subprocess.run", return_value=_ok_result()
        ) as mock_run:
            integration_gate._run_step4b(tmp_path)
        assert mock_run.call_args.kwargs["timeout"] == 300

    def test_default_when_unset(self, monkeypatch, tmp_path):
        """Check 3: unset env → timeout=120 (cairn-self default preserved)."""
        monkeypatch.delenv("CAIRN_PYTEST_TIMEOUT", raising=False)
        with patch(
            "integration_gate.subprocess.run", return_value=_ok_result()
        ) as mock_run:
            integration_gate._run_step4b(tmp_path)
        assert mock_run.call_args.kwargs["timeout"] == 120

    @pytest.mark.parametrize(
        "bad_value",
        ["", "abc", "0", "-5", "1.5"],
        ids=["empty", "non_numeric", "zero", "negative", "float"],
    )
    def test_invalid_falls_back_to_default(self, monkeypatch, tmp_path, bad_value):
        """Checks 5-8 + float: invalid env → default 120."""
        monkeypatch.setenv("CAIRN_PYTEST_TIMEOUT", bad_value)
        with patch(
            "integration_gate.subprocess.run", return_value=_ok_result()
        ) as mock_run:
            integration_gate._run_step4b(tmp_path)
        assert mock_run.call_args.kwargs["timeout"] == 120


# --- Ruff timeout override (_run_step4a) ------------------------------------


class TestRuffTimeoutOverride:
    """CAIRN_RUFF_TIMEOUT controls subprocess.run timeout for _run_step4a."""

    def test_env_override_applies(self, monkeypatch, tmp_path):
        """Check 2: CAIRN_RUFF_TIMEOUT=10 → subprocess.run timeout=10."""
        monkeypatch.setenv("CAIRN_RUFF_TIMEOUT", "10")
        with patch(
            "integration_gate.subprocess.run", return_value=_ok_result()
        ) as mock_run:
            integration_gate._run_step4a(tmp_path)
        assert mock_run.call_args.kwargs["timeout"] == 10

    def test_default_when_unset(self, monkeypatch, tmp_path):
        """Check 4: unset env → timeout=60 (cairn-self default preserved)."""
        monkeypatch.delenv("CAIRN_RUFF_TIMEOUT", raising=False)
        with patch(
            "integration_gate.subprocess.run", return_value=_ok_result()
        ) as mock_run:
            integration_gate._run_step4a(tmp_path)
        assert mock_run.call_args.kwargs["timeout"] == 60

    @pytest.mark.parametrize(
        "bad_value",
        ["", "abc", "0", "-5", "1.5"],
        ids=["empty", "non_numeric", "zero", "negative", "float"],
    )
    def test_invalid_falls_back_to_default(self, monkeypatch, tmp_path, bad_value):
        """Ruff-side parity: invalid env → default 60."""
        monkeypatch.setenv("CAIRN_RUFF_TIMEOUT", bad_value)
        with patch(
            "integration_gate.subprocess.run", return_value=_ok_result()
        ) as mock_run:
            integration_gate._run_step4a(tmp_path)
        assert mock_run.call_args.kwargs["timeout"] == 60


# --- Silent fallback (check 9) ----------------------------------------------


class TestSilentFallback:
    """Check 9: invalid env values produce no new stdout/stderr output.

    Byte-identity contract per intent.md:61 — message text and captured
    streams must be character-identical to the baseline (unset env) run
    when the env var is invalid. No config-warning lines, no stderr noise.
    """

    @pytest.mark.parametrize(
        "env_name,bad_value,func_name",
        [
            ("CAIRN_PYTEST_TIMEOUT", "abc", "_run_step4b"),
            ("CAIRN_PYTEST_TIMEOUT", "-5", "_run_step4b"),
            ("CAIRN_PYTEST_TIMEOUT", "0", "_run_step4b"),
            ("CAIRN_RUFF_TIMEOUT", "abc", "_run_step4a"),
            ("CAIRN_RUFF_TIMEOUT", "-5", "_run_step4a"),
            ("CAIRN_RUFF_TIMEOUT", "0", "_run_step4a"),
        ],
    )
    def test_invalid_env_produces_no_new_output(
        self, monkeypatch, tmp_path, capsys, env_name, bad_value, func_name
    ):
        func = getattr(integration_gate, func_name)

        # Baseline: env unset
        monkeypatch.delenv(env_name, raising=False)
        with patch("integration_gate.subprocess.run", return_value=_ok_result()):
            _, baseline_msg = func(tmp_path)
        baseline_streams = capsys.readouterr()

        # Invalid env
        monkeypatch.setenv(env_name, bad_value)
        with patch("integration_gate.subprocess.run", return_value=_ok_result()):
            _, invalid_msg = func(tmp_path)
        invalid_streams = capsys.readouterr()

        assert invalid_msg == baseline_msg, (
            f"Message differs between baseline and invalid-env run.\n"
            f"baseline: {baseline_msg!r}\ninvalid:  {invalid_msg!r}"
        )
        assert invalid_streams.out == baseline_streams.out, (
            f"stdout differs on invalid env.\n"
            f"baseline: {baseline_streams.out!r}\n"
            f"invalid:  {invalid_streams.out!r}"
        )
        assert invalid_streams.err == baseline_streams.err, (
            f"stderr differs on invalid env.\n"
            f"baseline: {baseline_streams.err!r}\n"
            f"invalid:  {invalid_streams.err!r}"
        )
