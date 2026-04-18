"""Phase 2 validation tests for SLICE-003 — progressive disclosure (S1–S5).

Verifies intent.md structural tests: slash commands in commands/claude-code/
conform to the progressive disclosure pattern (≤500-token lite files with
optional .full.md siblings).

Contract-conformance tests against static artifacts.
Pytest + stdlib; tiktoken optional (falls back to char/word heuristic).
"""

import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
COMMANDS_DIR = CAIRN_ROOT / "commands" / "claude-code"

TOKEN_BUDGET = 500


# --- Token counting --------------------------------------------------------


def count_tokens(text: str) -> int:
    """Estimate token count balancing accuracy, speed, and resource usage.

    Primary: tiktoken cl100k_base (closest public proxy to Claude's tokenizer).
    Fallback: max of char-based (~4 chars/token) and word-based (~1.3 tokens/word)
    estimates, biased toward the higher value for safety margin.
    """
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        pass
    char_estimate = len(text) / 4.0
    word_estimate = len(text.split()) * 1.3
    return int(max(char_estimate, word_estimate))


# --- File discovery --------------------------------------------------------


def lite_files() -> list[Path]:
    """All non-.full.md markdown files in commands/claude-code/."""
    return sorted(
        p for p in COMMANDS_DIR.glob("*.md") if not p.name.endswith(".full.md")
    )


# --- Diagram detection (generalized beyond Graphviz per R3 resolution) -----

DIAGRAM_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Graphviz
    (re.compile(r"\bdigraph\b"), "Graphviz 'digraph' keyword"),
    (re.compile(r"\bdot\s*\{"), "Graphviz 'dot {' block"),
    (re.compile(r"\bsubgraph\b"), "Graphviz 'subgraph' keyword"),
    (re.compile(r"\bstrict\s+(di)?graph\b"), "Graphviz strict graph"),
    # Mermaid
    (re.compile(r"\bgraph\s+(TD|LR|RL|BT|TB)\b"), "Mermaid graph directive"),
    (re.compile(r"\bsequenceDiagram\b"), "Mermaid sequenceDiagram"),
    (re.compile(r"\bclassDiagram\b"), "Mermaid classDiagram"),
    (re.compile(r"\bflowchart\s+(TD|LR|RL|BT|TB)\b"), "Mermaid flowchart"),
    (re.compile(r"\bstateDiagram\b"), "Mermaid stateDiagram"),
    (re.compile(r"\berDiagram\b"), "Mermaid erDiagram"),
    # PlantUML
    (re.compile(r"@startuml"), "PlantUML @startuml"),
    (re.compile(r"@enduml"), "PlantUML @enduml"),
    # Fenced diagram code blocks
    (
        re.compile(r"```\s*(?:dot|mermaid|plantuml|graphviz|ditaa|asciiart)\b"),
        "Diagram fenced code block",
    ),
    # Box-drawing characters (U+2500–U+257F)
    (re.compile(r"[\u2500-\u257f]"), "Box-drawing character"),
    # ASCII art structural patterns
    (re.compile(r"^\s*\+[-=]{3,}\+", re.MULTILINE), "ASCII art box border (+---+)"),
    (
        re.compile(r"^\s*[-=]{4,}>\s*$", re.MULTILINE),
        "ASCII arrow line (---->)",
    ),
    (
        re.compile(r"^\s*<[-=]{4,}\s*$", re.MULTILINE),
        "ASCII arrow line (<----)",
    ),
    # D3-style / SVG-like embedded diagrams
    (re.compile(r"\bdoublecircle\b"), "Graphviz/D3 shape keyword"),
]

# Subjective predicates banned from ## Load full sections
SUBJECTIVE_TRIGGERS = [
    "if confused",
    "if unsure",
    "if needed",
    "if appropriate",
    "if helpful",
    "when in doubt",
    "if you think",
    "if it seems",
    "if you feel",
]


# --- S1: Lite files ≤ 500 tokens ------------------------------------------


def test_s1_lite_files_within_token_budget():
    """S1 — every non-.full.md file in commands/claude-code/ ≤ 500 tokens."""
    files = lite_files()
    assert files, "no lite files found in commands/claude-code/"

    over_budget: list[tuple[str, int]] = []
    for path in files:
        tokens = count_tokens(path.read_text())
        if tokens > TOKEN_BUDGET:
            over_budget.append((path.name, tokens))

    assert not over_budget, "lite files over 500-token budget: " + ", ".join(
        f"{name} ({t} tokens)" for name, t in over_budget
    )


# --- S2: Every lite file has ## Load full section --------------------------


def test_s2_lite_files_have_load_full_section():
    """S2 — every lite file contains a `## Load full` section."""
    files = lite_files()
    assert files, "no lite files found in commands/claude-code/"

    missing = [p.name for p in files if "## Load full" not in p.read_text()]
    assert not missing, f"lite files missing `## Load full` section: {missing}"


# --- S3: Load full predicates resolve --------------------------------------


def test_s3_load_full_predicates_resolve():
    """S3 — every predicate under ## Load full points at an existing
    .full.md file OR says 'no full form'."""
    files = lite_files()
    assert files, "no lite files found in commands/claude-code/"

    broken: list[str] = []
    for path in files:
        text = path.read_text()
        section_match = re.search(
            r"## Load full\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL
        )
        if section_match is None:
            continue  # S2 catches missing sections

        section = section_match.group(1)

        if re.search(r"no full form", section, re.IGNORECASE):
            full_path = path.with_name(path.stem + ".full.md")
            if full_path.exists():
                broken.append(
                    f"{path.name}: says 'no full form' but {full_path.name} exists"
                )
            continue

        full_refs = re.findall(r"(\S+\.full\.md)", section)
        if not full_refs:
            broken.append(
                f"{path.name}: ## Load full has no .full.md reference and no 'no full form'"
            )
            continue

        for ref in full_refs:
            ref_path = COMMANDS_DIR / ref
            if not ref_path.exists():
                broken.append(f"{path.name}: references {ref} but file does not exist")

    assert not broken, "S3 violations:\n" + "\n".join(f"  - {b}" for b in broken)


def test_s3_no_subjective_load_triggers():
    """S3 supplement — load triggers must be discrete predicates evaluable
    from visible state, never subjective states."""
    files = lite_files()
    assert files, "no lite files found in commands/claude-code/"

    violations: list[str] = []
    for path in files:
        text = path.read_text()
        section_match = re.search(
            r"## Load full\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL
        )
        if section_match is None:
            continue

        section = section_match.group(1).lower()
        for trigger in SUBJECTIVE_TRIGGERS:
            if trigger in section:
                violations.append(f"{path.name}: subjective trigger '{trigger}'")

    assert not violations, (
        "Subjective load triggers found (must be discrete predicates):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


# --- S4: No diagram content in lite files ----------------------------------


def test_s4_no_diagram_content_in_lite_files():
    """S4 — no lite file contains Graphviz, Mermaid, PlantUML, box-drawing
    characters, ASCII art, or diagram fenced code blocks."""
    files = lite_files()
    assert files, "no lite files found in commands/claude-code/"

    violations: list[str] = []
    for path in files:
        text = path.read_text()
        for pattern, description in DIAGRAM_PATTERNS:
            match = pattern.search(text)
            if match:
                violations.append(
                    f"{path.name}: {description} (matched: {match.group()!r})"
                )

    assert not violations, "S4 diagram content violations:\n" + "\n".join(
        f"  - {v}" for v in violations
    )


# --- S5: No H3+ headers in lite files -------------------------------------


def test_s5_no_deep_headers_in_lite_files():
    """S5 — no lite file contains H3 (###) or deeper headers."""
    files = lite_files()
    assert files, "no lite files found in commands/claude-code/"

    violations: list[str] = []
    for path in files:
        text = path.read_text()
        deep_headers = re.findall(r"^(#{3,}\s+.+)$", text, re.MULTILINE)
        if deep_headers:
            violations.append(
                f"{path.name}: {len(deep_headers)} deep header(s), "
                f"first: {deep_headers[0]!r}"
            )

    assert not violations, "S5 deep header violations:\n" + "\n".join(
        f"  - {v}" for v in violations
    )
