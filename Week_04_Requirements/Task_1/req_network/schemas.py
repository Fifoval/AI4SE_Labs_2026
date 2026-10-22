"""Pydantic schemas for structured LLM outputs.

All fields are required (no defaults) so the schemas are valid for OpenAI strict
JSON-schema mode; "none" values are expressed as empty strings / lists.
"""
from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["Must", "Should", "Could"]


# --- extractor ---------------------------------------------------------------
class ExtractedItem(BaseModel):
    name: str = Field(description="Short descriptive name, 3-8 words, Title Case.")
    statement: str = Field(description="One or two sentences: 'The system shall ...'.")
    quote: str = Field(description="Verbatim snippet (max ~30 words) from the text supporting the item.")
    priority_hint: Priority = Field(description="Priority implied by the wording of the source.")
    status: Literal["valid", "nonsensical", "out_of_scope"] = Field(
        description="'valid' for a genuine requirement of the described software; "
                    "'nonsensical' / 'out_of_scope' for requests that sound like requirements "
                    "but are impossible, absurd or unrelated to the software.")
    discard_reason: str = Field(description="Why it is not valid; empty string when status is 'valid'.")


class ExtractionResult(BaseModel):
    items: list[ExtractedItem]


# --- structurer (taxonomy + glossary) -----------------------------------------
class Area(BaseModel):
    code: str = Field(description="2-4 uppercase letters, e.g. INV, SEC.")
    name: str
    description: str


class Assignment(BaseModel):
    cid: str
    area_code: str


class GlossaryTerm(BaseModel):
    term: str = Field(description="Preferred term to be used in all requirements.")
    definition: str
    synonyms_to_avoid: list[str]


class StructurePlan(BaseModel):
    areas: list[Area]
    glossary: list[GlossaryTerm]


class AssignmentBatch(BaseModel):
    assignments: list[Assignment]


# --- consolidator ------------------------------------------------------------
class ConsolidatedRequirement(BaseModel):
    name: str = Field(description="Short descriptive name, 3-8 words, Title Case.")
    description: str = Field(description="One paragraph (3-6 sentences) explaining the requirement.")
    candidate_ids: list[str] = Field(description="All candidate ids merged into this requirement.")
    priority: Priority
    priority_rationale: str = Field(description="One sentence justifying the priority.")


class DiscardedGroup(BaseModel):
    name: str
    candidate_ids: list[str]
    reason: str


class ConsolidationResult(BaseModel):
    requirements: list[ConsolidatedRequirement]
    discarded: list[DiscardedGroup]


# --- conflict detector / arbiter -----------------------------------------------
class Issue(BaseModel):
    kind: Literal["conflict", "duplicate", "tension"]
    requirement_ids: list[str] = Field(description="Exactly two requirement ids.")
    explanation: str


class IssueList(BaseModel):
    issues: list[Issue]


class ArbiterDecision(BaseModel):
    genuine_conflict: bool = Field(description="True only if both requirements cannot be "
                                               "satisfied together under any reasonable reading.")
    winner_id: str = Field(description="Requirement to keep if genuine_conflict, else empty.")
    reason: str = Field(description="If genuine: why the winner is kept. If not: how the two "
                                    "can coexist and what stakeholders should clarify.")


class DuplicateCheck(BaseModel):
    genuine_duplicate: bool = Field(description="True only if merging loses nothing: every "
                                                "specific detail of each requirement is already "
                                                "stated in the other one.")
    reason: str


class FusedRequirement(BaseModel):
    name: str = Field(description="Short descriptive name, 3-8 words, Title Case.")
    description: str = Field(description="One paragraph that states every specific detail of "
                                         "both input requirements.")


# --- critic -------------------------------------------------------------------
class CriticIssue(BaseModel):
    kind: Literal["rewrite", "duplicate", "conflict"]
    area_code: str
    requirement_ids: list[str]
    problem: str
    fix_instruction: str


class CriticReport(BaseModel):
    passed: bool
    summary: str
    issues: list[CriticIssue]
