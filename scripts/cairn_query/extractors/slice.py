"""SliceExtractor — parses `git log --grep='^slice: .* — complete$'` commits."""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

import yaml

from _root import project_root as _project_root
from cairn_query.extractors.base import ExtractedEdge, ExtractedNode
from cairn_query.models import Slice

# Pattern for the commit subject: "slice: <id> — complete"
_SUBJECT_RE = re.compile(r"^slice:\s+(.+?)\s+—\s+complete$")
# Slice ID must be hierarchical (matches models.SLICE_ID_RE)
_SLICE_ID_RE = re.compile(r"^[a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*$")


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=str(_project_root()),
    )
    return result.stdout


def _get_slice_yaml(sha: str) -> dict:
    """Try to read .claude/current-slice/slice.yaml from a commit."""
    content = _run_git("show", f"{sha}:.claude/current-slice/slice.yaml")
    if not content.strip():
        return {}
    try:
        data = yaml.safe_load(content)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _parse_date(val: object) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


def _to_str_list(val: object) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val if v]
    if isinstance(val, str):
        return [val] if val else []
    return []


class SliceExtractor:
    """Extract Slice entities from git log slice-close commits."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self._repo_root = repo_root

    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]:
        log_out = _run_git(
            "log",
            "--grep=^slice: .* — complete$",
            "--format=%H %s",
        )

        nodes: list[ExtractedNode] = []
        edges: list[ExtractedEdge] = []
        seen: set[str] = set()

        for line in log_out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) != 2:
                continue
            sha_full, subject = parts[0], parts[1]
            sha_short = sha_full[:7]

            m = _SUBJECT_RE.match(subject)
            if not m:
                continue
            slice_id = m.group(1).strip()

            # Skip legacy SLICE-NNN IDs and other non-hierarchical formats
            if not _SLICE_ID_RE.match(slice_id):
                continue

            if slice_id in seen:
                continue
            seen.add(slice_id)

            # Load metadata from the commit's slice.yaml
            yaml_data = _get_slice_yaml(sha_full)

            started = _parse_date(yaml_data.get("started")) or date(2000, 1, 1)
            completed = _parse_date(yaml_data.get("completed"))
            name = yaml_data.get("name") or slice_id
            inv_touched = _to_str_list(
                yaml_data.get("invariants-touched")
                or yaml_data.get("invariants_touched")
            )
            adrs_ref = _to_str_list(
                yaml_data.get("adrs-referenced") or yaml_data.get("adrs_referenced")
            )
            adrs_created = _to_str_list(
                yaml_data.get("adrs-created") or yaml_data.get("adrs_created")
            )
            envelope_paths = _to_str_list(
                yaml_data.get("envelope") or yaml_data.get("envelope_paths")
            )
            envelope_oos = _to_str_list(
                yaml_data.get("out-of-scope") or yaml_data.get("envelope_out_of_scope")
            )

            feature_id = slice_id.split("/")[0]

            try:
                sl = Slice(
                    id=slice_id,
                    name=name,
                    feature_id=feature_id,
                    status="complete",
                    started=started,
                    completed=completed,
                    invariants_touched=inv_touched,
                    adrs_referenced=adrs_ref,
                    adrs_created=adrs_created,
                    envelope_paths=envelope_paths,
                    envelope_out_of_scope=envelope_oos,
                    close_commit=sha_short,
                )
            except Exception:
                continue

            nodes.append(ExtractedNode(entity=sl))
            # PARENT edge: Slice → Feature
            edges.append(
                ExtractedEdge(
                    predicate="PARENT",
                    from_node_type="Slice",
                    from_id=slice_id,
                    to_node_type="Feature",
                    to_id=feature_id,
                )
            )

        return nodes, edges
