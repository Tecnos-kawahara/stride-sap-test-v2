# 14. Evidence Packガイド - 品質証跡の管理方法

**所要時間**: 約15分

---

## 5分クイックリファレンス（PM向け）

**見る順番（この3つだけ）**:
1. **Gate / Decision**（合格・条件付き合格・不合格）
2. **Findings / Exceptions**（Critical/Highが残っていないか）
3. **Next Steps**（条件付きの場合、期限と責任者が明記されているか）

**判断の目安**:
- **合格**: 次工程へ進める
- **条件付き合格**: 期限と責任者が明記されていれば進める
- **不合格**: 重大リスクが未解決、または証跡不足

---

## このガイドで学ぶこと

1. Evidence Pack とは（PM向けの読み方を含む）
2. 必須の証跡
3. AI Provenance（AIの出自記録）
4. ゲート判定での使用
5. テンプレートの使い方

---

**サンプル参照**: `sdd-templates/specs/sample_feature` に Web-EDI の参考サンプルがあります（未承認/プレースホルダあり）。  
**注**: パスは例なので、自分の機能では `specs/<feature>` に置き換えます。

## 初心者向け: Evidence Packの作り方（最短3ステップ）

1. **plan.md** で `required_artifacts` と保存先を決める  
2. **evidence_pack.md** を作成し、項目ごとにURL/パスを記入  
3. **Gateの判断（合格/条件付き/不合格）** を最後に記録する

**補足**: Evidence Pack 自体は「リンク集 + 結論」です。  
ログやレポートの本体は別ファイル/URLに置き、ここから参照します。

## 1. Evidence Pack とは

### まず一言で言うと

Evidence Packは「**この案件を次の段階に進めてよいことを示す、証拠の束**」です。  
企画書や報告書ではなく、**合否を判断するための事実**を集めたものだと考えてください。

### PM向けの読み方（5分で判断する）

Evidence Pack は「この案件を次へ進めてよいか」を判断するための**証拠の束**です。PMは以下の3点だけ押さえれば十分です。

1. **Gate / Decision**: 合格・条件付き合格・不合格の結論
2. **Findings / Exceptions**: 重大な未解決（Critical/High）がないか
3. **Next Steps**: もし未解決がある場合、誰がいつ対応するか

**Critical/High の意味（PM向け）**:
- **Critical**: 今すぐ止めるべき重大リスク
- **High**: 早急に対応が必要な高リスク

### Evidence Pack の構成（どこを見ればよいか）

- **Gate**: 判定結果と責任者
- **Required Evidence**: 必須証跡が揃っているか
- **Findings / Exceptions**: 重大な問題と例外承認
- **Next Steps**: 条件付きの場合の対応計画

### どうして必要なのか（PM視点）

- **説明責任**: 「なぜ進めたのか」を後から説明できる
- **リスク可視化**: セキュリティや品質の重大問題が残っていないか明確になる
- **意思決定の標準化**: 人による判断のばらつきを減らせる

**Evidence Packがないと起きること**:
- 進めた理由が説明できず、監査や顧客説明で困る
- 重大リスクの見落としが起きやすい
- 判断が担当者の感覚に依存する

### 専門用語を言い換えると（PM向け）

| 用語 | ひと言で言うと | 例えるなら |
|------|----------------|------------|
| CI | 自動の動作確認 | 自動健康診断 |
| Test Reports | テスト結果の成績表 | 期末テストの結果 |
| SAST | コードの安全性検査 | 体内のX線検査 |
| SCA | 使用部品の安全性検査 | 部品のリコール確認 |
| Secrets Scan | 機密漏洩チェック | 鍵の置き忘れ確認 |
| AI Provenance | AIの生成履歴 | 料理のレシピと調理担当 |

**要するに**: 「動いたか」「安全か」「機密は漏れていないか」「AIの関与が透明か」を確認するための束です。

### 定義

**Evidence Pack** は、ゲート判定に必要な品質証跡をまとめたものです。

```
┌─────────────────────────────────────────────────┐
│              Evidence Pack                       │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ CI Results   │  │ Test Reports │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ SAST Report  │  │ SCA Report   │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ Secrets Scan │  │ AI Provenance│             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 目的

1. **客観的なゲート判定** - 主観ではなく証拠に基づく判断
2. **監査対応** - 後から「なぜ通過したか」を説明可能
3. **AIの透明性** - AI生成物の出自を記録

---

## 2. 必須の証跡

### 2.1 証跡一覧

**読み方**: この一覧はSE/PGが記録します。PMは「見るポイント」だけ確認すればOKです。

| 証跡 | ひと言で言うと | PM向けの意味 | 見るポイント | 必須 |
|------|----------------|------------------|-------------|------|
| `ci_results` | 自動の動作確認 | 再現可能な実行ができたか | 成功/失敗、ログURL | ○ |
| `test_reports` | テストの成績表 | 仕様どおりに動くか | 合格数/失敗数、重要テストの結果 | ○ |
| `sast` | コードの安全検査 | コード品質・脆弱性 | Critical/High がゼロか | ○ |
| `sca` | 部品の安全検査 | 依存ライブラリのリスク | Critical/High がゼロか、例外承認 | ○ |
| `secrets_scan` | 機密漏洩チェック | 機密が混ざっていないか | secrets_found = 0 | ○ |
| `ai_provenance` | AIの生成履歴 | AI利用の透明性 | 誰が承認したか、provider/surface/model/effort/CVP の記録 | ○ |

**補足**: 以下のYAMLはSE/PGが記録します。PMは**結果と例外承認**だけ見れば十分です。

### 2.2 ci_results

```yaml
ci_results:
  pipeline_id: "pipeline-12345"
  run_date: "2025-01-15T10:30:00Z"
  status: "success"
  duration_seconds: 180
  stages:
    - name: "build"
      status: "success"
    - name: "test"
      status: "success"
    - name: "lint"
      status: "success"
  log_url: "https://ci.example.com/logs/12345"
```

**PMの見るべき値**: `status` が `success` か、ログURLがあるか。

### 2.3 test_reports

```yaml
test_reports:
  unit:
    total: 50
    passed: 50
    failed: 0
    skipped: 0
    coverage_pct: 85.2
  integration:
    total: 10
    passed: 10
    failed: 0
  e2e:
    total: 5
    passed: 5
    failed: 0
  report_paths:
    - "tests/reports/junit.xml"
    - "tests/reports/coverage.html"
    - "tests/reports/e2e/index.html"
```

**PMの見るべき値**: `failed` が 0 か、重要テスト（integration/e2e）の結果が出ているか。

### 2.4 sast（静的解析）

```yaml
sast:
  tool: "sast-tool"
  scan_date: "2025-01-15"
  findings:
    critical: 0
    high: 0
    medium: 2
    low: 5
  exceptions:
    - id: "SAST-001"
      severity: "medium"
      reason: "False positive - validated input"
      approved_by: "Tech Lead"
  report_url: "https://sonar.example.com/project/12345"
```

**PMの見るべき値**: `critical` と `high` が 0 か、例外の承認者がいるか。

### 2.5 sca（依存関係スキャン）

```yaml
sca:
  tool: "Snyk"
  scan_date: "2025-01-15"
  vulnerabilities:
    critical: 0
    high: 0
    medium: 1
    low: 3
  license_violations: 0
  forbidden_licenses_found: []
  exceptions:
    - package: "example-lib@1.2.3"
      vulnerability: "CVE-2024-12345"
      severity: "medium"
      reason: "Not exploitable in our usage"
      mitigation: "Will upgrade in next sprint"
      approved_by: "Security Lead"
```

**PMの見るべき値**: `critical` と `high` が 0 か、例外に承認者がいるか。

### 2.6 secrets_scan

```yaml
secrets_scan:
  tool: "Gitleaks"
  scan_date: "2025-01-15"
  findings:
    secrets_found: 0
    false_positives: 2
  exceptions:
    - file: "tests/fixtures/mock_token.txt"
      reason: "Test fixture, not a real secret"
```

**PMの見るべき値**: `secrets_found` が 0 か。

---

## 3. AI Provenance（AIの出自記録）

### 3.1 なぜ必要か

AIが生成したコードや仕様は、その**出自（Provenance）**を記録する必要があります。

- どのモデルで生成したか
- どのプロンプトを使用したか
- 入力データは何だったか
- 最終的に誰が承認したか（責任は人間にある）

**PM向けの理解**:  
AIが関与した成果物は「誰が責任を負うか」が曖昧になりがちです。  
Evidence Packでは、**生成経緯と承認者**を明示することで責任をはっきりさせます。

### 3.2 記録項目

```yaml
ai_provenance:
  provider: "Anthropic"
  surface: "claude-code"
  model_id: "claude-opus-4-7"
  model_version: "2026-04-16"
  prompt_version: "{{TEMPLATE_VERSION}}"
  inputs_hash: "sha256:abc123..."
  execution_settings:
    effort_level: "xhigh"
    reasoning_mode: "adaptive"
    thinking_display: "summarized"
    max_output_tokens: 65536
  budget_controls:
    task_budget_enabled: false
    task_budget_tokens: 0
    beta_headers: []
    tokenizer_notes: "2026-04-18 に Opus 4.7 tokenizer で再計測"
  deployment_controls:
    provider_target: "Claude Code"
    organization_scope: "org:tecnos-example"
    cyber_safeguards_reviewed: true
    cvp_status: "not_required"
  generated_files:
    - path: "sdd-templates/specs/sample_feature/spec.md"
      hash: "sha256:def456..."
  human_reviewed: true
  reviewer: "山田太郎"
  review_date: "2026-04-18"
```

**PMの見るべき値**: `reviewer` / `human_reviewed` が埋まっているか、必要に応じて `deployment_controls.cvp_status` が妥当か。

**運用メモ**: セキュリティ調査・脆弱性検証のような Anthropic 利用ワークロードでは、`deployment_controls.cvp_status` と `cyber_safeguards_reviewed` を必ず記録します。

### 3.3 入力ハッシュ

```yaml
inputs:
  basic_design_hash: "sha256:abc123def456..."
  process_bpmn_hash: "sha256:789ghi012..."
  org_constraints_hash: "sha256:345jkl678..."
```

**目的**: 同じ入力から同じ出力が得られることを検証可能にする  
（入力ハッシュは「入力の指紋」だと考えると分かりやすいです）

---

## 4. ゲート判定での使用

### 4.0 なぜゲート判定が必要か（PM向け）

ゲート判定は「**次の工程に進んでよいか**」を決める公式な判断です。  
Evidence Packがあることで、**感覚ではなく証拠に基づいて**判断できます。

### 4.1 Evidence Pack によるゲート判定

```
┌─────────────────────────────────────────────────┐
│                 Gate Decision                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  Evidence Pack の全項目が揃っている？             │
│       │                                          │
│       ├─ ci_results: ✅                          │
│       ├─ test_reports: ✅                        │
│       ├─ sast: ✅                                │
│       ├─ sca: ✅                                 │
│       ├─ secrets_scan: ✅                        │
│       └─ ai_provenance: ✅                       │
│                                                  │
│  Critical/High の未解決 findings がない？         │
│       └─ ✅                                      │
│                                                  │
│  ───────────────────────────                     │
│  Result: ✅ 合格                                  │
└─────────────────────────────────────────────────┘
```

### 4.2 判定基準

| 判定 | 条件 |
|------|------|
| 合格 | 全証跡が揃い、Critical/High findings がゼロ |
| 条件付き合格 | 全証跡が揃い、Medium以下は例外として承認済み |
| 不合格 | 証跡が不足、または未解決のCritical/High がある |

### 4.3 PM向け判断のコツ

- **合格**: 次工程へ進めてよい（例外なし）
- **条件付き合格**: 次工程に進むが、期限と責任者を必ず確認
- **不合格**: 重要な未解決があるため、先に解消が必要

### 4.4 条件付き合格の具体例

**ケース1: 中リスクの脆弱性があり、対策期限が決まっている**

- 事象: SCAでMediumが1件検出、直近で修正予定
- 条件: 期限と担当者を明記し、次Gateまでに解消
- 判断: 条件付き合格

**ケース2: E2Eの一部が不安定だが、影響範囲が限定的**

- 事象: E2E 1件がflake判定、重要フローではない
- 条件: triage記録と修正タスクを追加
- 判断: 条件付き合格

**ケース3: AI出自記録は揃っているが、承認者名が未記入**

- 事象: ai_provenanceのreviewerが空欄
- 条件: 承認者の記載を完了する
- 判断: 条件付き合格

### 4.5 不合格の典型例

**ケース1: Critical/Highが未解決**

- 事象: SASTでHighが残っている
- 理由: 重大リスクが残ったままでは進めない
- 判断: 不合格

**ケース2: 必須証跡が不足**

- 事象: test_reportsが未提出、CI結果が確認できない
- 理由: 合否を判断する根拠が欠けている
- 判断: 不合格

**ケース3: 例外承認が未記録**

- 事象: Mediumの脆弱性はあるが、例外承認がない
- 理由: 例外はPM判断の記録が必須
- 判断: 不合格

### 4.6 合格の典型例

**ケース1: 重大リスクなし、証跡が揃っている**

- 事象: ci/test/sast/sca/secrets/ai_provenance が全て揃い、Critical/Highゼロ
- 理由: 合否判断に必要な根拠が揃っている
- 判断: 合格

**ケース2: 例外があるが、すべて承認済み**

- 事象: Mediumがあるが例外承認が記録済み、期限と担当が明記
- 理由: PM判断としての記録が完備
- 判断: 合格

### 4.7 OK/NGサンプル（PM向け）

**OKの例（合格）**

```
Gate: Release Gate
Decision: 合格
Findings: Critical 0 / High 0
Next Steps: なし
```

**NGの例（不合格）**

```
Gate: Release Gate
Decision: 不合格
Findings: High 1（未解決）
Next Steps: 期限/責任者が未記入
```

---

## 5. テンプレートの使い方

### 5.1 テンプレートの場所

```
sdd-templates/templates/evidence_pack_template.md
```

### 5.2 テンプレートの構造

```yaml
---
artifact: "evidence_pack"
template_id: "TPL-EVID-TECNOS-001"
feature_id: "FEAT-XXX"
evidence_pack_id: "EVID-XXX"
version: "{{TEMPLATE_VERSION}}"      # stride initで自動設定
status: "draft"
owners:
  - { name: "QA Lead", role: "Quality" }
  - { name: "Tech Lead", role: "Tech Lead" }
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

# Gate Evidence Pack

## Gate
- Gate-ID: Plan Gate / Tasks Gate / Release Gate
- Decision: 合格 | 条件付き合格 | 不合格

## Required Evidence
- CI results (unit/integration/e2e): [URL or path]
- SAST report: [URL or path]
- SCA report (license/vuln): [URL or path]
- Secrets scan: [URL or path]
- AI provenance (model/prompt/input hash): [記録]

## Findings
- Open issues: [未解決の問題があれば記載]
- Exceptions: [例外として承認された項目]

## Next Steps
- Task: [次のアクション]
- Owner: [担当者]
- Due: [期限]
```

**PMの見方**: Gate / Findings / Next Steps の3箇所だけ読めば十分です。

**PMの見るべき値**:
- Gate Decision が明記されているか
- Findings に Critical/High が残っていないか
- Next Steps に期限と責任者があるか

### 5.3 使用手順

1. テンプレートをコピー
   ```bash
   cp sdd-templates/templates/evidence_pack_template.md \
      specs/my_feature/implementation-details/evidence_pack.md
   ```

2. IDを置換
   ```bash
   sed -i '' 's/FEAT-XXX/FEAT-001/g' specs/my_feature/implementation-details/evidence_pack.md
   ```

3. 各セクションを埋める

4. Gate-ID と Decision を記録

---

## 6. plan.md での定義

Evidence Pack は `plan.md` の `test_strategy.evidence_pack` で定義します。

```yaml
test_strategy:
  evidence_pack:
    required_artifacts:
      - "ci_results"
      - "test_reports"
      - "sast"
      - "sca"
      - "secrets_scan"
      - "ai_provenance"
    storage:
      path: "sdd-templates/specs/sample_feature/implementation-details/evidence_pack.md"
    provenance:
      record_provider_surface: true
      record_model_id: true
      record_model_version: true
      record_prompt_version: true
      record_inputs_hash: true
      record_execution_settings: true
      record_budget_controls: true
      record_tokenizer_notes: true
      record_cyber_safeguards_status: true
```

---

## 7. Evidence Metrics（v4.2）

### 7.1 metrics_trend セクション

v4.2 から、Evidence Pack に **metrics_trend** セクションが追加されました。CI で自動収集したメトリクスをトレンドとして記録します。

```yaml
metrics_trend:
  coverage_trend:
    - { date: "2026-02-01", pct: 78.5 }
    - { date: "2026-02-14", pct: 82.3 }
  test_time_trend:
    - { date: "2026-02-01", seconds: 45 }
    - { date: "2026-02-14", seconds: 38 }
  cache_hit_rate: 0.73
  gate_lead_time_hours: 4.5
  spec_drift_count: 0
```

**PM の見るべき値**:
- `coverage_trend` が上昇傾向か
- `spec_drift_count` がゼロか（契約⇔実装の乖離なし）
- `gate_lead_time_hours` が過度に長くないか

**収集方法**（Enterprise CI で自動）:

```bash
python3 sdd-templates/tools/evidence_metrics_collector.py . --json
```

詳細は [Appendix E: Turborepo Monorepo リファレンス](23_turborepo_monorepo.md) を参照。

---

## 8. 保持期間

```yaml
storage:
  retention_days: 180  # 180日間保持
  path_hint: "specs/<feature>/implementation-details/"
```

**推奨**: 監査要件に応じて保持期間を設定（通常180日〜7年）

**PM視点**: 保持期間は「監査に耐える期間」を意味するため、リスク許容度に合わせて設定する。

---

## チェックリスト

### PM向け（最小チェック）

- [ ] Gate Decision が明記されている
- [ ] Critical/High の未解決がない（または例外承認済み）
- [ ] 条件付きの場合、期限と責任者が明記されている

### SE/PG向け

- [ ] plan.md に evidence_pack を定義した
- [ ] evidence_pack.md を作成した
- [ ] ci_results を記録した
- [ ] test_reports を記録した
- [ ] sast を記録した
- [ ] sca を記録した
- [ ] secrets_scan を記録した
- [ ] ai_provenance を記録した
- [ ] Gate Decision を記録した

---

## 次のステップ

→ [08. ID規約リファレンス](appendix_a_id_conventions.md)

---

> SDD Templates Manual - 07. Evidence Pack Guide
