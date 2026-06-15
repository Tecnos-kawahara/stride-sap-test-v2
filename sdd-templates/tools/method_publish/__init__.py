"""method_publish — Tecnos-STRIDE Method Store publishing pipeline.

Implements FEAT-METHODSTOREPUBLISHING (Feature ②).
Provides:
  preview  / validate / diff   — pre-publish checks (G-01)
  snapshot_builder / cosign_signer / oci_publisher / publish — staging/stable publish (G-02, G-03)
  rollback / drift_detector    — incident response (G-04)
  release_notes_generator      — auto RELEASE_NOTES.md (G-03, CT-FILE-02)
  tenant_policy_validator      — sdd_tenant_policy schema validation (G-05, CT-FILE-03)
  ci_helpers (separate package) — gitops_pr_creator + slack_notifier
"""

__version__ = "1.1.0"
__feature__ = "FEAT-METHODSTOREPUBLISHING"

DEFAULT_REGISTRY = "ghcr.io/tecnos-japan-cbp/sdd-method-store"
DEFAULT_CHANNELS = ("edge", "staging", "stable")
DEFAULT_AUTO_UPGRADE = ("none", "patch", "minor")
COSIGN_FULCIO = "https://fulcio.sigstore.dev"
COSIGN_REKOR = "https://rekor.sigstore.dev"

EXIT_OK = 0
EXIT_VALIDATION_FAILURE = 1
EXIT_USAGE_ERROR = 2
# Per CT-CLI-02 contract、exit code 3 は subcommand 別に異なる意味を持つ:
#   - preview / validate / diff:  3 = path not found (root not found)
#   - publish:                     3 = auth failure (GITHUB_TOKEN scope 不足等)
#   - rollback:                    3 = GitOps PR auto-create failure
# 同 integer に複数の symbolic constant を割り当てているのは contract 仕様準拠の意図的な設計。
# F2 follow-up #19.3 (2026-05-08) で operator confusion 回避のためコメント追加。
EXIT_PATH_NOT_FOUND = 3   # used by preview / validate / diff (root not found)
EXIT_AUTH_FAILURE = 3     # used by publish (auth/credentials) / rollback (PR creation)
EXIT_SIGSTORE_OUTAGE = 4
