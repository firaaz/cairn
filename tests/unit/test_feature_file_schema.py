"""Phase 2 validation tests for SLICE-009 — feature file YAML schema.

Verifies intent.md V1 (feature file creation), V2 (always-create),
V3 (existing feature update), V7 (dropped slices).

Defines a validate_feature_file() function matching feature-slice-model D2 schema,
then tests it against valid and invalid synthetic data.

Pytest + stdlib + pyyaml.
"""

import copy
from datetime import date

import yaml


# --- Schema validator --------------------------------------------------------


def validate_feature_file(data: dict, filename_stem: str) -> list[str]:
    """Validate feature file YAML against feature-slice-model D2 schema.

    Returns a list of error strings. Empty list == valid.
    """
    errors: list[str] = []

    # Required top-level fields
    for field in ("id", "intent", "created"):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # id must match filename stem
    if "id" in data and data["id"] != filename_stem:
        errors.append(
            f"id '{data['id']}' does not match filename stem '{filename_stem}'"
        )

    # created must be a date
    if "created" in data:
        val = data["created"]
        if not isinstance(val, date):
            try:
                date.fromisoformat(str(val))
            except (ValueError, TypeError):
                errors.append(f"created '{val}' is not a valid YYYY-MM-DD date")

    # slices list validation (optional field)
    if "slices" in data:
        if not isinstance(data["slices"], list):
            errors.append("slices must be a list")
        else:
            for i, entry in enumerate(data["slices"]):
                if not isinstance(entry, dict):
                    errors.append(f"slices[{i}]: must be a mapping")
                    continue
                # Required per-entry fields
                if "id" not in entry:
                    errors.append(f"slices[{i}]: missing required field 'id'")
                if "added" not in entry:
                    errors.append(f"slices[{i}]: missing required field 'added'")
                # added must be a date
                if "added" in entry:
                    added_val = entry["added"]
                    if not isinstance(added_val, date):
                        try:
                            date.fromisoformat(str(added_val))
                        except (ValueError, TypeError):
                            errors.append(
                                f"slices[{i}]: added '{added_val}' is not a valid date"
                            )
                # status only legal value is "dropped"
                if "status" in entry and entry["status"] != "dropped":
                    errors.append(
                        f"slices[{i}]: status must be 'dropped', "
                        f"got '{entry['status']}'"
                    )
                # after must be a list if present
                if "after" in entry and not isinstance(entry["after"], list):
                    errors.append(f"slices[{i}]: after must be a list")

    return errors


def add_slice_entry(feature_data: dict, slice_entry: dict) -> dict:
    """Add a slice entry to an existing feature file's slices list.

    Returns a new dict (does not mutate the original).
    """
    result = copy.deepcopy(feature_data)
    if "slices" not in result:
        result["slices"] = []
    result["slices"].append(slice_entry)
    return result


# --- Fixtures ----------------------------------------------------------------


VALID_FEATURE = {
    "id": "feature-slice-model",
    "intent": "Structured decomposition for multi-slice work",
    "created": date(2026, 4, 14),
    "slices": [
        {
            "id": "implement-feature-files",
            "added": date(2026, 4, 14),
        },
    ],
}

VALID_MULTI_SLICE = {
    "id": "context-discipline",
    "intent": "Session-to-session context transfer protocol",
    "created": date(2026, 4, 10),
    "slices": [
        {
            "id": "handoff-protocol",
            "added": date(2026, 4, 10),
        },
        {
            "id": "catchup-tiers",
            "after": ["handoff-protocol"],
            "added": date(2026, 4, 11),
        },
    ],
}

VALID_WITH_DROPPED = {
    "id": "auth-rework",
    "intent": "Replace legacy auth middleware",
    "created": date(2026, 4, 12),
    "slices": [
        {
            "id": "auth-migration",
            "added": date(2026, 4, 12),
        },
        {
            "id": "auth-old-cleanup",
            "added": date(2026, 4, 12),
            "after": ["auth-migration"],
            "status": "dropped",
            "reason": "Legacy code already removed in auth-migration",
        },
    ],
}


# --- V1: Feature file creation — required fields ----------------------------


class TestRequiredFields:
    def test_valid_complete_feature_file(self):
        errors = validate_feature_file(VALID_FEATURE, "feature-slice-model")
        assert errors == [], f"Valid feature file rejected: {errors}"

    def test_missing_id(self):
        data = {k: v for k, v in VALID_FEATURE.items() if k != "id"}
        errors = validate_feature_file(data, "feature-slice-model")
        assert any("Missing required field: id" in e for e in errors)

    def test_missing_intent(self):
        data = {k: v for k, v in VALID_FEATURE.items() if k != "intent"}
        errors = validate_feature_file(data, "feature-slice-model")
        assert any("Missing required field: intent" in e for e in errors)

    def test_missing_created(self):
        data = {k: v for k, v in VALID_FEATURE.items() if k != "created"}
        errors = validate_feature_file(data, "feature-slice-model")
        assert any("Missing required field: created" in e for e in errors)

    def test_id_must_match_filename_stem(self):
        errors = validate_feature_file(VALID_FEATURE, "wrong-name")
        assert any("does not match filename stem" in e for e in errors)

    def test_created_must_be_valid_date(self):
        data = {**VALID_FEATURE, "created": "not-a-date"}
        errors = validate_feature_file(data, "feature-slice-model")
        assert any("not a valid" in e for e in errors)

    def test_slice_entry_requires_id(self):
        data = copy.deepcopy(VALID_FEATURE)
        data["slices"] = [{"added": date(2026, 4, 14)}]
        errors = validate_feature_file(data, "feature-slice-model")
        assert any("missing required field 'id'" in e for e in errors)

    def test_slice_entry_requires_added(self):
        data = copy.deepcopy(VALID_FEATURE)
        data["slices"] = [{"id": "some-slice"}]
        errors = validate_feature_file(data, "feature-slice-model")
        assert any("missing required field 'added'" in e for e in errors)


# --- V2: Always-create — single-slice features accepted ----------------------


class TestAlwaysCreate:
    def test_single_slice_feature_accepted(self):
        """Even single-slice features produce a feature file — no 'too small'
        rejection path (feature-slice-model D3)."""
        errors = validate_feature_file(VALID_FEATURE, "feature-slice-model")
        assert errors == []

    def test_feature_without_slices_accepted(self):
        """Feature file without slices list is valid (e.g., during brainstorming
        before first slice starts — feature-slice-model D2)."""
        data = {
            "id": "brainstorm-only",
            "intent": "Exploring a new capability",
            "created": date(2026, 4, 14),
        }
        errors = validate_feature_file(data, "brainstorm-only")
        assert errors == []


# --- V3: Existing feature update — add slice preserves existing entries ------


class TestExistingFeatureUpdate:
    def test_add_slice_preserves_existing(self):
        """Adding a new slice entry must not destroy existing entries."""
        original = copy.deepcopy(VALID_MULTI_SLICE)
        original_slice_ids = [s["id"] for s in original["slices"]]

        new_entry = {
            "id": "token-budget-check",
            "after": ["catchup-tiers"],
            "added": date(2026, 4, 12),
        }
        updated = add_slice_entry(original, new_entry)

        # Original entries preserved
        updated_ids = [s["id"] for s in updated["slices"]]
        for orig_id in original_slice_ids:
            assert orig_id in updated_ids, f"Slice '{orig_id}' lost during update"

        # New entry present
        assert "token-budget-check" in updated_ids

        # Original not mutated
        assert len(original["slices"]) == len(VALID_MULTI_SLICE["slices"])

    def test_add_slice_to_feature_without_slices(self):
        """Adding first slice to a feature file that had no slices list."""
        data = {
            "id": "new-feature",
            "intent": "Something new",
            "created": date(2026, 4, 14),
        }
        entry = {"id": "first-slice", "added": date(2026, 4, 14)}
        updated = add_slice_entry(data, entry)
        assert len(updated["slices"]) == 1
        assert updated["slices"][0]["id"] == "first-slice"
        errors = validate_feature_file(updated, "new-feature")
        assert errors == []

    def test_updated_feature_still_validates(self):
        new_entry = {
            "id": "third-slice",
            "added": date(2026, 4, 13),
        }
        updated = add_slice_entry(VALID_MULTI_SLICE, new_entry)
        errors = validate_feature_file(updated, "context-discipline")
        assert errors == [], f"Updated feature file invalid: {errors}"


# --- V7: Dropped slices preserved --------------------------------------------


class TestDroppedSlices:
    def test_dropped_slice_accepted(self):
        """A slice entry with status: dropped and reason is valid."""
        errors = validate_feature_file(VALID_WITH_DROPPED, "auth-rework")
        assert errors == []

    def test_dropped_slice_preserved_after_update(self):
        """Adding a new slice must not remove dropped entries."""
        new_entry = {
            "id": "auth-v2",
            "after": ["auth-migration"],
            "added": date(2026, 4, 13),
        }
        updated = add_slice_entry(VALID_WITH_DROPPED, new_entry)
        dropped = [s for s in updated["slices"] if s.get("status") == "dropped"]
        assert len(dropped) == 1
        assert dropped[0]["id"] == "auth-old-cleanup"
        assert dropped[0]["reason"] == "Legacy code already removed in auth-migration"

    def test_invalid_status_rejected(self):
        """Only 'dropped' is a legal status value."""
        data = copy.deepcopy(VALID_FEATURE)
        data["slices"][0]["status"] = "completed"
        errors = validate_feature_file(data, "feature-slice-model")
        assert any("status must be 'dropped'" in e for e in errors)

    def test_after_field_must_be_list(self):
        data = copy.deepcopy(VALID_FEATURE)
        data["slices"][0]["after"] = "not-a-list"
        errors = validate_feature_file(data, "feature-slice-model")
        assert any("after must be a list" in e for e in errors)


# --- YAML round-trip smoke test ----------------------------------------------


class TestYamlRoundTrip:
    def test_valid_feature_survives_yaml_roundtrip(self):
        """Feature file serialized to YAML and parsed back must still validate."""
        dumped = yaml.dump(VALID_FEATURE, default_flow_style=False)
        loaded = yaml.safe_load(dumped)
        errors = validate_feature_file(loaded, "feature-slice-model")
        assert errors == [], f"Round-trip validation failed: {errors}"

    def test_dropped_feature_survives_yaml_roundtrip(self):
        dumped = yaml.dump(VALID_WITH_DROPPED, default_flow_style=False)
        loaded = yaml.safe_load(dumped)
        errors = validate_feature_file(loaded, "auth-rework")
        assert errors == [], f"Round-trip validation failed: {errors}"
