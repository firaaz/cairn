"""Shared quote-vs-source matcher: whitespace-normalize + comment-strip tolerance.

Pins the tolerance contract both the validator assertion and the (later) CLI
gate route through, so the two callers cannot diverge on what counts as
"grounded". RED before lib.premise_match exists: the import fails.
"""

from lib.premise_match import grounded, normalize


def test_indent_reflow_grounds():
    source = "    def f():\n        return 1"
    assert grounded(source, "def f():", ".py") is True


def test_comment_edit_grounds():
    assert grounded("x = 1  # old", "x = 1  # new", ".py") is True


def test_token_change_does_not_ground():
    assert grounded("x = 2", "x = 1", ".py") is False


def test_markdown_block_comment_stripped():
    assert grounded("text <!-- note -->", "text", ".md") is True


def test_comment_only_quote_does_not_ground():
    assert grounded("# just a comment", "# just a comment", ".py") is False


def test_blank_quote_does_not_ground():
    assert grounded("anything", "   ", ".py") is False


def test_unknown_ext_only_whitespace_normalizes():
    assert grounded("a # b", "a # b", ".txt") is True


def test_normalize_strips_py_comment():
    assert normalize("x = 1  # trailing", ".py") == "x = 1"


def test_normalize_keeps_mid_token_hash():
    assert normalize("url#anchor", ".py") == "url#anchor"


def test_normalize_collapses_whitespace():
    assert normalize("  a\n\t b   c  ", "") == "a b c"
