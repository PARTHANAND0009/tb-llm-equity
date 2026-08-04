"""Scoring rubric (RULE 2 — FROZEN RUBRIC).

Once results exist for a given RUBRIC_VERSION, that version's contents are
immutable. A change to scoring logic or dimensions requires bumping
RUBRIC_VERSION and re-scoring all arms under the new version. Never edit the
rubric for a version that already has results attached to it.

Not yet implemented: dimensions and scoring functions are added when
experiment work begins.
"""

RUBRIC_VERSION = "v0"
