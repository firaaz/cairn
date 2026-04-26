"""Pydantic entity models for the cairn knowledge substrate.

One file holds all seven entity types because they share a discriminated-union
return type via `EntityType`. Splitting per entity would force cross-file
imports of the union, hurting readability.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


INV_ID_RE = r"^INV-\d{3}$"
SLICE_ID_RE = r"^[a-z][a-z0-9-]*\/[a-z0-9][a-z0-9-]*$"
LESSON_ID_RE = r"^L-\d{3}$"


class EntityType(str, Enum):
    INVARIANT = "invariant"
    DECISION = "decision"
    LESSON = "lesson"
    SPEC_SECTION = "spec_section"
    OP_RULE = "op_rule"
    FEATURE = "feature"
    SLICE = "slice"


class PathAnchor(BaseModel):
    path: str
    line: int | None = None


class Invariant(BaseModel):
    entity_type: Literal["invariant"] = "invariant"
    id: str = Field(pattern=INV_ID_RE)
    statement: str
    target: PathAnchor
    grep: str
    architecture_anchor: PathAnchor


class DecisionPoint(BaseModel):
    id: str
    slug: str
    body: str


class Decision(BaseModel):
    entity_type: Literal["decision"] = "decision"
    id: str
    name: str
    status: Literal["accepted", "superseded", "deferred", "draft"]
    firmness: Literal["firm", "provisional"]
    topic: str
    date: date
    invariants_touched: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: str | None = None
    decision_points: list[DecisionPoint] = Field(default_factory=list)
    body_anchor: PathAnchor


class Lesson(BaseModel):
    entity_type: Literal["lesson"] = "lesson"
    id: str = Field(pattern=LESSON_ID_RE)
    title: str
    discovered: date
    pattern: str
    instances: list[str] = Field(default_factory=list)
    rule: str
    anti_patterns: list[str] = Field(default_factory=list)
    body_anchor: PathAnchor


class SpecSection(BaseModel):
    entity_type: Literal["spec_section"] = "spec_section"
    id: str
    title: str
    body_anchor: PathAnchor


class OpRule(BaseModel):
    entity_type: Literal["op_rule"] = "op_rule"
    id: str
    statement: str
    scope: str
    body_anchor: PathAnchor


class Feature(BaseModel):
    entity_type: Literal["feature"] = "feature"
    id: str
    name: str
    intent: str
    shaped_from: str | None = None
    slice_ids: list[str] = Field(default_factory=list)


class Slice(BaseModel):
    entity_type: Literal["slice"] = "slice"
    id: str = Field(pattern=SLICE_ID_RE)
    name: str
    feature_id: str
    status: Literal["complete", "failed", "in-progress"]
    started: date
    completed: date | None = None
    invariants_touched: list[str] = Field(default_factory=list)
    adrs_referenced: list[str] = Field(default_factory=list)
    adrs_created: list[str] = Field(default_factory=list)
    envelope_paths: list[str] = Field(default_factory=list)
    envelope_out_of_scope: list[str] = Field(default_factory=list)
    close_commit: str


Entity = Annotated[
    Union[Invariant, Decision, Lesson, SpecSection, OpRule, Feature, Slice],
    Field(discriminator="entity_type"),
]
