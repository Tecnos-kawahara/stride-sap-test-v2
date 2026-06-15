"""Path-based plane / visibility / return_policy classifier.

Loads `shared/policies/plane_classification_ruleset_v1.yaml` and applies the first
matching pattern (glob style) to a given path. Returns the rule + a confidence
score (1.0 for exact glob match, lower for the catch-all default).
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_RULESET_PATH = "shared/policies/plane_classification_ruleset_v1.yaml"


@dataclass
class Classification:
    rule_id: str
    plane: str
    visibility: str
    return_policy: dict[str, str]
    confidence: float
    rationale: str
    element_type: str


class Classifier:
    def __init__(self, ruleset_path: Path | str = DEFAULT_RULESET_PATH):
        self.ruleset_path = Path(ruleset_path)
        with self.ruleset_path.open("r", encoding="utf-8") as fh:
            self._ruleset = yaml.safe_load(fh) or {}
        self._path_rules: list[dict[str, Any]] = self._ruleset.get("path_rules", [])
        self._type_inference: list[dict[str, Any]] = self._ruleset.get("type_inference", [])
        self._thresholds = self._ruleset.get("confidence_thresholds", {})

    def classify(self, rel_path: str) -> Classification:
        normalized = rel_path.lstrip("./").replace("\\", "/")
        matched_rule = None
        for rule in self._path_rules:
            if fnmatch.fnmatch(normalized, rule["pattern"]):
                matched_rule = rule
                break
        if matched_rule is None:
            matched_rule = self._path_rules[-1]  # RULE-DEFAULT

        confidence = 0.5 if matched_rule["id"] == "RULE-DEFAULT" else 0.95
        element_type = self._infer_type(normalized)

        return Classification(
            rule_id=matched_rule["id"],
            plane=matched_rule["plane"],
            visibility=matched_rule["visibility"],
            return_policy=matched_rule["return_policy"],
            confidence=confidence,
            rationale=matched_rule.get("rationale", ""),
            element_type=element_type,
        )

    def _infer_type(self, rel_path: str) -> str:
        for entry in self._type_inference:
            if fnmatch.fnmatch(rel_path, entry["pattern"]):
                return entry["type"]
        return "reference"

    @property
    def thresholds(self) -> dict[str, float]:
        return dict(self._thresholds)
