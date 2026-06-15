# ⚠️ OBSOLETE - For Reference Only

> **このディレクトリは v2.1.0 以降では使用されません。**
> 実装やテンプレートには `sdd-templates/` や `memory/` の現行ファイルを使用してください。

## 移行先

| v1.0 ファイル | v2.1.0 移行先 |
|---------------|---------------|
| `policies/mode_policy.yaml` | `memory/erp_addon_mode_policy.yaml` |
| `policies/risk_taxonomy.yaml` | `memory/erp_addon_risk_taxonomy.yaml` |
| `sdd-templates/*.md` | `sdd-templates/templates/` |
| `manual/*.md` | `manual/16_*.md`, `manual/17_*.md`, `manual/18_*.md` |

## 重要な変更点 (v1.0 → v2.1.0)

1. **Ops Pack**: v1.0 では conditional → v2.1.0 では ERP Addon 全体で必須
2. **Post-run 承認**: v1.0 では confirm/validate のみ → v2.1.0 では全モードで必須
3. **Spec Links**: v2.1.0 でファイル存在チェック追加

---

# SDD-Template-ERP-Addon (Tecnos Japan) - Archive

Purpose
- ERPアドオン（既存ERPへの拡張/改修）を、Spec中心で安全に高速実行できるようにする「テンプレート＋統制（Gate）＋実行追跡（Run/State/Mode）」パッケージ。
- 既存の Gate 1〜Final を温存しつつ、FIRE相当の Work Item / Run / Walkthrough / State / Mode を取り込む。

Concept
- Macro（フェーズ統制）: Gate 1〜Final（basic_design → bpmn → spec → plan → tasks → evidence）
- Micro（実行統制）: Work Item（変更単位）ごとに Mode（autopilot/confirm/validate）を付与し、Run（実行）を残す

Flow Portfolio
- SIMPLE: 仕様生成・引継ぎ（execution trackingなし）
- FIRE: 実行追跡＋可変チェックポイント（標準レーン）
- AI-DLC: 複雑ドメイン/監査向け（Operations成果物を強制するレーン）

See: manual/erp_addon_playbook.md
