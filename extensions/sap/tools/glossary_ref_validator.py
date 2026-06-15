"""
glossary_ref_validator.py
参照仕様: 03_lint §3-3

domain_terms_ref の参照先存在確認 + インライン定義検出。
"""

from pathlib import Path

from basic_design_completeness_validator import (
    ValidationError, ValidationResult, ValidatorContext
)


def validate_glossary_ref(
    context: ValidatorContext,
) -> ValidationResult:
    result = ValidationResult()
    if not context.spec:
        return result

    spec = context.spec
    spec_file = str(context.feature_dir / "spec.md")

    # R1: domain_terms_ref path exists
    ref_path = spec.get("domain_terms_ref")
    if ref_path and isinstance(ref_path, str):
        full_path = context.feature_dir.parent.parent / ref_path
        if not full_path.exists():
            result.errors.append(ValidationError(
                code="GLOSSARY_REF_MISSING",
                message=f"domain_terms_ref: '{ref_path}' が存在しません。パスを確認してください",
                severity="ERROR", file=spec_file,
                suggestion=f"Check that {ref_path} exists or update the path",
            ))

    # R2: inline definition detection
    inline_terms = spec.get("domain_terms")
    if inline_terms and isinstance(inline_terms, (list, dict)) and len(inline_terms) > 0:
        result.warnings.append(ValidationError(
            code="GLOSSARY_INLINE_DEFINITION",
            message="domain_terms がインラインで定義されています。memory/glossary.md への集約を推奨します",
            severity="WARNING", file=spec_file,
            suggestion="Move domain_terms to memory/glossary.md and use domain_terms_ref",
        ))

    return result
