# Security and Privacy Guidelines
# Goal: keep trust boundaries explicit and preserve auditability.

## 1) Non-negotiables
- Follow `memory/tecnos_org_constraints.md` and `memory/constitution.md`.
- Do not bypass integration contracts or audit logging.
- No direct DB writes to ERP or system-of-record data without explicit approval.
- Never commit secrets; document required vars in `.env.example`.

## 2) Data governance
- Identify data classes and retention in `basic_design.md` and `spec.md`.
- Ensure correlation IDs and audit trails for external integrations.
- Mask or avoid logging sensitive data.

## 3) Access control and SoD
- Define approver vs executor separation where applicable.
- Record authorization rules in `spec_as_code` (authz_matrix).

## 4) AI and provenance
- Record provider/surface, model, prompt, input hash, and execution settings in the Evidence Pack.
- For Anthropic-based security workflows, also record cyber safeguards review status and CVP applicability.
- Do not use exploratory agents in CI gates.
- Stop and ask if a request violates org constraints.

## 5) High-impact triggers (review required)
- New integrations or contract changes (CT-*).
- Security or privacy requirement changes.
- Evidence Pack scope changes.

## 6) LLM / AI agent trust boundaries

> Inspired by gstack /cso and /review checks (garrytan/gstack, MIT License)

AI エージェントや LLM を機能仕様として統合する場合、以下の trust boundary を明示すること。

### Input validation
- ユーザー入力や外部入力をそのまま system prompt / tool input に流さない
- Prompt injection を想定し、信頼できない入力を分離・サニタイズする
- エージェント間通信や内部APIには認証をかける

### Output verification
- LLM / エージェント出力を検証なしに業務DBへ保存しない
- 金額計算・在庫評価・承認判定などの業務クリティカルな値に、LLM出力をそのまま使わない
- 構造化出力は schema validation 等で検証する

### Required spec fields
- trusted / untrusted boundary
- input validation strategy
- output verification strategy
- fallback / human escalation

### Important note
- Evidence Pack の provenance 記録（`record_model_id`, `record_execution_settings` など）だけでは AI 統合機能とはみなさない
- 実際に model output が業務フローに影響する場合にのみ trust boundary を要求する

### stride security
- `stride security --audit` で SEC-006 として確認される
- AI/LLM統合があるのに trust boundary が未定義の場合、FAIL になる

## 7) Anthropic Security Workflow Note
- 正当な脆弱性調査・攻撃シミュレーションでも、Anthropic 側の cyber safeguards により遮断される前提で計画する
- どの provider target / organization scope で実行したかを Evidence Pack に記録する
- CVP が使えない provider 経路では、事前に代替経路か人間承認を確保する
- ブロックを単なる「モデル不調」と扱わず、運用ガードとして扱う
