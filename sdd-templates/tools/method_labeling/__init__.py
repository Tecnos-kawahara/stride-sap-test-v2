"""Method Labeling helper modules — Tecnos-STRIDE Feature ① (FEAT-METHODSSOTEXTERNALIZATION).

This package provides plane / visibility / return_policy classification of Method
content (sdd-templates/templates/, policies/, skills/, hooks/, validators/, memory/,
cowork-plugin/reference_files/) and emits a method-store.lock.json snapshot that
conforms to specs/method_ssot_externalization/contracts/method-store-schema.json.

Public modules:
    frontmatter — YAML frontmatter parsing / patching
    classifier  — path -> (plane, visibility, return_policy) via ruleset
    sha         — git short-sha computation per file

Public entry points (in sdd-templates/tools/, not this package):
    plane_label_completeness_checker.py — check coverage 100%
    ip_boundary_checker.py              — detect public exposure of internal content
    method_labels_checker.py            — combined CI checker
    method_labels_suggester.py          — AI-side suggestion stub (rule-based)
    internal_marker_consistency_checker.py — scan INTERNAL_* tag balance
    attribution_validator.py            — verify BABOK / 4-layer / value-driven fair-use
    method_version_injector.py          — inject method_version into newly-generated specs
    method_label_migrator.py            — migrate v0 -> v1 frontmatter
    method_audit.py                     — top-level audit + emit method-store.lock.json
"""

__version__ = "1.0.0"
__all__ = ["frontmatter", "classifier", "sha"]
