"""Pydantic schema for the vignette set.

A Vignette is never free-generated: it must be grounded in one or more rows
of the divergence table (``divergence_ids``), and the schema enforces the
minimum shape needed for it to function as a discriminator between models
(at least one distractor pair, at least one checkable critical-error
condition, at least one expected divergence point).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

BurdenClass = Literal["india_high", "western_control"]
PresentationType = Literal["pulmonary", "extrapulmonary", "comorbid", "drug_resistant"]

_VIGNETTE_ID_RE = re.compile(r"^VIG-\d{3,}$")


class Patient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: str = Field(
        ..., description="e.g. '34 years' or '8 months' — free text to allow pediatric ages"
    )
    sex: Literal["male", "female"]
    occupation: str
    social_history: str
    presenting_complaint: str
    duration: str = Field(..., description="Duration of symptoms, e.g. '3 weeks'")
    exam_findings: str
    prior_treatment: str
    comorbidities: list[str] = Field(default_factory=list)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generator_model: str
    generated_at: datetime
    source_divergence_ids: list[str] = Field(..., min_length=1)
    critique_passes: int = Field(..., ge=0, le=2)
    human_reviewed: bool
    clinician_reviewed: bool


class Vignette(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    burden_class: BurdenClass
    presentation_type: PresentationType
    divergence_ids: list[str] = Field(..., min_length=1)
    stem: str
    patient: Patient
    distractors: list[str] = Field(..., min_length=2)
    ntep_correct_actions: list[str] = Field(..., min_length=1)
    western_correct_actions: list[str] = Field(..., min_length=1)
    critical_error_conditions: list[str] = Field(..., min_length=1)
    expected_divergence_points: list[str] = Field(..., min_length=1)
    holdout: bool
    provenance: Provenance

    @field_validator("id")
    @classmethod
    def _id_format(cls, v: str) -> str:
        if not _VIGNETTE_ID_RE.match(v):
            raise ValueError(f"id must match VIG-### (got {v!r})")
        return v

    @field_validator("stem")
    @classmethod
    def _stem_no_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("stem must not be blank")
        return v
