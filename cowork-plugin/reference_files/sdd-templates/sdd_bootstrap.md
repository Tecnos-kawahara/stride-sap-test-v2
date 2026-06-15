# SDD Bootstrap — Claude Code Quick Start (v5.4.0-tecnos-stride)
# このファイル1つを読めば、SDD テンプレートで開発を開始できる。
# 詳細リファレンスは末尾の「参照先」で必要時に読む。
#
# 指示優先順位 (Opus 4.7 literal-follow):
#   1. このファイル (SDD 実行 SSoT)
#   2. memory/constitution.md + memory/tecnos_org_constraints.md (組織ルール)
#   3. CLAUDE.md (root, プロジェクト) — このファイルと矛盾する場合はこのファイルが優先
#   4. SDD_MANIFESTO.md (ツール非依存コア)
#   5. CLAUDE_WORKFLOW.md (Claude Code 固有補足のみ)
#   6. agent_docs/sdd_guidelines.md, agent_docs/commands.md (詳細リファレンス)
#   7. ユーザーレベル CLAUDE.md (汎用ルール) — SDD Phase Gate に矛盾する "Parallel/Batch" 指示は SDD 側優先

---

## 1. 実行モデル (v4.4 — AI Autonomous Execution)

| 役割 | 担当者 | やること |
|------|--------|---------|
| **実行者 (R)** | Claude Code | 全作業（init, 成果物作成, lint, テスト, Evidence, 自動修正） |
| **承認者 (A)** | 人間 | APPROVAL.md / WI-*.approval.md の編集、業務判断のみ |

- Phase 内のステップは**確認なしで連続実行**する
- 停止するのは **Gate 承認待ち（APPROVAL_PENDING / WI_APPROVAL_PENDING）のみ**
- lint FAIL（APPROVAL以外）→ **AI が自動修正して再実行**

### 自動修正の停止条件（loop bound — MANDATORY）

AI は以下の停止条件を守る。無限ループを避けるため、Opus 4.7 は literal に従うこと。

1. **lint 自動修正の上限**: 同一 feature に対して**最大 5 回**。5 回で PASS しなければ停止し、残エラーを人間に報告。
2. **同一エラーコードの繰返し**: 同じ `error_code` が**連続 3 回**現れたら停止。根本原因の再考を人間に相談（3-Strike Protocol）。
3. **業務判断要エラー**: `REQUIREMENT_AMBIGUOUS` / `DESIGN_DECISION_NEEDED` 等、自動修正不可のエラーは即座に停止、人間に質問。
4. **stride-lint 以外のツール**: `stride evaluate --review` は max_iters=3（内部実装）、`stride security` は 1 回で判定、`stride pr-check` は 1 回。いずれも AI がループしない。
5. **stride pr-check NOT_READY**: 同一 root に対して**最大 3 回**の自動修正。以降は人間に報告。

---

## 2. 絶対ルール (INVIOLABLE)

### SSoT ヒエラルキー
```
Intent (basic_design) → Specs (spec/plan) → Contracts (OpenAPI等) → Code
```
Code が Spec と乖離したら **Code がバグ**。Code を変更する前に Specs を更新すること。

### 禁止事項
1. **APPROVAL.md / EPIC_APPROVAL.md / WI-*.approval.md を AI が編集してはならない**
2. **Phase N+1 のファイルを Phase N 承認前に作成してはならない**
3. **承認済み成果物を変更するには change_log.md + 再承認が必須**
4. **Spec / Plan 変更時は即座に stride-lint を再実行**

### AI Action Boundary — 3分類 (v4.6 Execution Authority 準拠, literal)

| 分類 | 判定基準 | 代表アクション |
|------|---------|---------------|
| **MUST DO** | 承認不要・自律実行 | stride-lint 実行 / APPROVAL_PENDING 以外のエラー自動修正（§loop bound 準拠）/ placeholder 置換 / canonical YAML 修正 / 現在 Phase 許可ファイル作成 / 契約↔実装整合維持 / stride auto-continue の次ステップ実行 |
| **MUST ASK** | 人間の業務判断を待つ | 要件曖昧 / 複数の実装選択肢 / design_ref 未定義 / tecnos_org_constraints 禁止事項抵触の可能性 / autonomy_bias 引下げ / 例外（DR/Exceptions）の記録内容 / tier_mode_minimum 未満の mode 選択 |
| **MUST NOT DO** | 絶対禁止 | APPROVAL.md / EPIC_APPROVAL.md / WI-*.approval.md の編集 / Gate スキップ / ERP DB 直書き / 画面スクレイピング / 秘密情報コミット / 承認済み成果物の無記録変更 / Phase N+1 ファイルの先行作成 |

### 絶対禁止アクション（literal 判定用 — Opus 4.7 が迷わないよう列挙）

AI は以下のいずれかを**実行前に必ず停止**する:
- `Edit`/`Write` の `file_path` が `APPROVAL.md`, `EPIC_APPROVAL.md`, `WI-*.approval.md` のいずれか
- `memory/constitution.md`, `memory/tecnos_org_constraints.md` の `meta.version` / `last_reviewed_at` の編集（組織オーナー承認要）
- 承認済み Gate に対応する成果物（表参照: §4 の Phase 表の Gate 列）の編集で `change_log.md` の更新なし
- `specs/<feature>/state/state.yaml` の `status: done` → `in_progress` への後退（承認プロセス逸脱）

### 承認依頼フォーマット
```
Gate X の承認をお願いします。
APPROVAL.md の「Gate X: <Gate Name>」セクションで:
  1. チェックボックスを [x] に変更
  2. 承認者名と日付を記入
してください。
```

---

## 3. Feature ライフサイクル（全自動フロー）

```
stride init <feature> --detect [--scale starter|standard|enterprise]
  │
  ▼ Phase 1: Design (自律実行)
  basic_design.md + process.bpmn → stride lint → stride evaluate → ⛔ Gate 1,2 承認待ち
  │
  ▼ Phase 2: Specify (自律実行)
  spec.md + plan.md + contracts/ → stride lint → stride evaluate → ⛔ Gate 3,4 承認待ち
  │
  ▼ Phase 3: Tasking (自律実行)
  tasks.md + tests/ → stride lint → stride evaluate → ⛔ Gate 5 承認待ち
  │
  ▼ Phase 4: Execute (WI単位で自律実行)
  WI定義 → wi_readiness → Run実装 → walkthrough → stride lint
  → ⛔ WI承認待ち → 次WI...
  │
  ▼ Final
  evidence_pack → ops pack → stride pr-check → ⛔ Final Gate 承認待ち → PR作成
```

### Intake-First 対話モード
「Intake-First で始めて」「質問形式で聞き取って」と指示された場合:
1. `stride intake <feature>` で intake テンプレート作成
2. 各セクションを**1つずつ対話で質問**: Who/What/Why → Scope → 関連システム → 業務フロー → 未解決の質問 → 制約
3. 回答をもとに `basic_design_intake.md` を自動記入
4. intake から `basic_design.md` を生成 → Design Phase に合流

---

## 4. Phase 別：成果物 + 品質基準

### Phase 1: Design
| 成果物 | 品質基準 |
|--------|---------|
| basic_design.md | traceability 1行+, integration flow 1つ+, delivery_model + RACI+ 定義済, blocking questions 解決済 |
| process.bpmn | Camunda 8.8 形式, basic_design のフローと整合, incoming/outgoing 必須, XOR に default or conditionExpression, DI完全性（§4-BPMN 参照、advanced は docs/bpmn_quick_reference.md / docs/camunda_bpmn_practice_guide.md）|
| epic_flow.bpmn (EPIC のみ) | collaboration + participant 2+, messageFlow に documentation, 各 participant は vertical swimlane (`isHorizontal="false"`), §4-BPMN 参照 |
| APPROVAL.md | AI が作成（ただし編集は人間のみ） |

- `stride init <feature> --detect` でスキャフォールド
- `memory/artifact_registry.md` の存在確認
- プレースホルダ（FEAT-XXX 等）を全置換
- `stride lint specs/<feature>/` → PASS まで自動修正（最大 5 回、以降停止して報告） → Gate 1,2 承認依頼

---

### §4-BPMN — BPMN Creation MUST-DO (MANDATORY, literal-follow 用)

**BPMN ファイル（process.bpmn / epic_flow.bpmn）は以下の手順で作成する。毎回ゼロから書いてはならない。**

#### Step 1 — テンプレートを literal にコピー

| 作る成果物 | どのテンプレートをコピーするか | 配置先 |
|-----------|------------------------------|--------|
| `process.bpmn` (FEAT) | `sdd-templates/templates/process_bpmn_template.bpmn` | `specs/<feature>/process.bpmn` |
| `epic_flow.bpmn` (EPIC) | `sdd-templates/templates/epic_flow_template.bpmn` | `epics/<EPIC>/epic_flow.bpmn` |

`stride init <feature>` が自動でコピーする。存在しない場合のみ手動コピー (`cp`)。**ゼロから書くな。**

#### Step 2 — プレースホルダを全置換

- `BPMN-PROC-XXX` → `BPMN-PROC-<FEATID>` (FEAT の場合)
- `EPIC-XXX` → `EPIC-<ID>` (EPIC の場合)
- `XXX_feature_name` → `<feature>` (targetNamespace)
- `{{プロセス名}}`, `{{ユーザータスク名}}`, `{{条件式}}` 等の `{{...}}` は業務内容に合わせて全て埋める
- 未置換は `stride lint` が `BPMN_PLACEHOLDER_PRESENT` 警告を出す

#### Step 3 — ノード/フローを増減（テンプレートの構造は維持）

テンプレートの**ID 命名スキームを継承**する:

| 種別 | FEAT (`process.bpmn`) の ID スキーム | EPIC (`epic_flow.bpmn`) の ID スキーム |
|------|-------------------------------------|---------------------------------------|
| Process | `BPMN-PROC-<FEATID>` | `Process_A`, `Process_B` (participant 別) |
| Task | `BPMN-TASK-001`, `BPMN-TASK-002`, ... | `Task_<Participant>_<Role>` (例: `Task_A_Send`) |
| Gateway | `BPMN-GW-001`, ... | 同上（必要時） |
| Event | `BPMN-EVT-001`, ... | `Start_<Participant>`, `End_<Participant>` |
| SequenceFlow | `BPMN-FLOW-001`, ... | `Flow_<Participant>_NNN` (例: `Flow_A_001`) |
| MessageFlow | — | `MsgFlow_<From>to<To>` |
| BPMNShape | `Shape_TASK_001`, `Shape_GW_001`, ... | `<NodeID>_di` (例: `Task_A_Send_di`) |
| BPMNEdge | `Edge_FLOW_001`, ... | `<FlowID>_di` |

**FEAT と EPIC でスキームは異なる — 混ぜるな。** FEAT = `BPMN-*`、EPIC = `<Name>_<Role>`。

#### Step 4 — Hard Requirements（literal チェック）

BPMN ファイルは以下を**全て**満たすこと。`stride lint` が機械検証する。

**FEAT (`process.bpmn`) の必須:**
1. [ ] namespaces に `zeebe`, `modeler`, `xsi` を含む
2. [ ] `modeler:executionPlatform="Camunda Cloud"` + `executionPlatformVersion="8.8.x"`
3. [ ] `<bpmn:process isExecutable="true">` （必須）
4. [ ] 全 flow node に `<bpmn:incoming>` / `<bpmn:outgoing>` 要素（startEvent は outgoing のみ、endEvent は incoming のみ）
5. [ ] `<bpmn:serviceTask>` は `<zeebe:taskDefinition type="...">` を持つ
6. [ ] `<bpmn:exclusiveGateway>` (2+ outgoing) は `default="<flow-id>"` または全 outgoing に `<bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">` を持つ
7. [ ] `<bpmn:conditionExpression>` は `=` で開始する FEEL 式、空文字禁止
8. [ ] `<bpmn:sequenceFlow>` の `sourceRef` / `targetRef` は実在する node ID を指す
9. [ ] `<bpmn:boundaryEvent>` は `attachedToRef="<task-id>"` を持つ
10. [ ] `<bpmn:timeDuration>` は ISO-8601 (`PT1H`, `P1D` 等)
11. [ ] `<bpmndi:BPMNDiagram>` → `<bpmndi:BPMNPlane>` → 全 flow node に `<bpmndi:BPMNShape>`、全 sequenceFlow に `<bpmndi:BPMNEdge>` が存在
12. [ ] BPMNPlane の `bpmnElement` は process または collaboration の id を指す
13. [ ] participant shape は `isHorizontal="false"` (vertical swimlane 強制)
14. [ ] `<bpmn:documentation>` を process / userTask / serviceTask / 条件付き gateway / 条件付き sequenceFlow に記入

**EPIC (`epic_flow.bpmn`) の必須:**
1. [ ] `<bpmn:collaboration>` を必ず持つ（process のみでは NG）
2. [ ] `<bpmn:participant>` が 2+、各 participant に `processRef="<process-id>"`
3. [ ] 各 `<bpmn:process>` は participant の processRef から参照される
4. [ ] 各 `<bpmn:messageFlow>` に `<bpmn:documentation>` を記入（ペイロード/SLA）
5. [ ] BPMNPlane の `bpmnElement` は collaboration id を指す
6. [ ] 各 participant shape は `isHorizontal="false"` (vertical swimlane)
7. [ ] 内部 process の flow node にも `incoming/outgoing`、BPMNShape/Edge を完全に記述
8. [ ] `EPIC-XXX` プレースホルダは全て置換

#### Step 5 — `basic_design.md` との連動

`basic_design.md` の `bpmn_descriptions.elements[].bpmn_id` は `process.bpmn` 内の実 ID と**完全一致**させる。AIが別IDを振ると traceability が破綻する。

EPIC の場合は `epic_design.md` の `epic_flow_descriptions` と `epic_flow.bpmn` の messageFlow ID を一致させる。

#### Step 6 — 検証

```bash
sdd-templates/bin/stride lint specs/<feature>/
```

- `BPMN_VALIDATION_FAILED` が出たら修正（loop bound §1 準拠、最大5回）
- `BPMN_PLACEHOLDER_PRESENT` warning は必ず解消
- `BPMN_DOCUMENTATION_MISSING` warning は記入推奨

#### 絶対禁止（BPMN literal 判定用）

- テンプレートをコピーせずにゼロから書く
- FEAT で EPIC スキーム（`Task_A_Send`）を使う、または EPIC で FEAT スキーム（`BPMN-TASK-001`）を使う
- `<bpmn:incoming>` / `<bpmn:outgoing>` の省略
- BPMNShape / BPMNEdge の省略（「DI は optional」と解釈するのは誤り）
- `xsi:type="bpmn:tFormalExpression"` を省いた conditionExpression
- XOR で default も conditionExpression もない
- participant shape の `isHorizontal="true"` or 未指定（vertical 強制）

詳細は `docs/bpmn_quick_reference.md`（1-page）→ `sdd-templates/policies/bpmn_generator_rules.md`（Tecnos 適用ルール全仕様、§21 OMG 実行セマンティクス + §22 Connection Rules + §23 Coverage + §24 Tecnos override 含む）→ `docs/camunda_bpmn_dictionary_complete.md`（OMG BPMN 2.0 + Camunda 8.9 全要素辞書、深堀り用）の順で参照。

### Phase 2: Specify
| 成果物 | 品質基準 |
|--------|---------|
| spec.md | AC 3つ+, NFR (integration/data/security 各1+), spec_as_code パスあり |
| plan.md | coverage_policy 定義, テストが全AC/CT カバー, evidence_pack 定義 |
| contracts/ | OpenAPI等, Spec と整合 |
| tests/scenarios.yaml | AC をカバーする E2E シナリオ |

- gate flags を設定
- `e2e` タグは critical user journeys のみに適用
- `stride lint specs/<feature>/` → PASS まで自動修正（最大 5 回、以降停止して報告） → Gate 3,4 承認依頼

### Phase 3: Tasking
| 成果物 | 品質基準 |
|--------|---------|
| tasks.md | 全 task に plan_refs（stable ID のみ）, e2e タスクあり（e2e AC 存在時） |

- `tasks_gate_check.tasks_ready_for_code = true` 設定
- `stride lint specs/<feature>/` → PASS まで自動修正（最大 5 回、以降停止して報告） → Gate 5 承認依頼

### Phase 4: Execute
WI/Run 単位で実行。詳細はセクション 6 参照。

---

## 4b. Completeness Principle — 湖を沸かせ (Profile-Aware 数値基準, v5.4)

AIにとって追加の完成度コストはほぼゼロ。「動いた」で止めず「全ACを満たす」まで実装する。

**「湖 (boil)」判定閾値 — Profile 別（両方満たすとき湖、AND logic）:**

| Profile | 行数上限 | ファイル数上限 |
|---------|---------|---------------|
| enterprise-erp | +200 行 | +5 ファイル |
| saas-integration | +150 行 | +4 ファイル |
| prototype | +100 行 | +3 ファイル |

**判定の優先順位（literal-follow — 上から順に評価して最初に該当した時点で確定）:**

1. **risk_flags の新規追加**（`authz/sod/pii/accounting_calc/db_schema/data_migration`）→ **即「海」**（他の判定より優先、Profile 不問）
2. **承認済み成果物の変更**（basic_design / spec / plan / tasks）→ **即「海」**
3. **新規 AC / 新規契約 / 新規 NFR の創出** → **即「海」**
4. **行数・ファイル数の Profile 閾値チェック** — 上表の両方を満たすなら「湖」、いずれか超過なら「海」
5. 上記すべて通過 → 「湖」として即実装

**「海 (flag)」判定 — いずれか該当なら Phase 分割提案:**
1. risk_flags 新規追加（Profile 不問）
2. 承認済み成果物の変更
3. 新規 AC / 新規契約 / 新規 NFR の創出
4. 上表の Profile 別上限を超過

**判定フロー:**
```
エッジケース発見 → 上の優先順位で上から評価
  risk_flags 新規? ──yes→ 海（即）
  承認済み変更?   ──yes→ 海（即）
  新規 AC/CT/NFR? ──yes→ 海（即）
  行数・ファイル数 Profile 閾値超? ──yes→ 海
  すべて no → 湖 → 即実装

海判定 → `implementation-details/change_log.md` に記録
       → 人間に Phase 分割 or 再承認を相談
       → 承認を得てから実装
```

この原則は次セクションのチェックリストと組み合わせて運用する。

**Profile 解決ルール**（参照: `shared/policies/profile_policy.yaml`）:
1. `basic_design.md` の `basic_design.profile`（SSoT）
2. `state.yaml` の top-level `profile`（flat schema、キャッシュ）
3. いずれも未定義なら `enterprise-erp` をデフォルト

---

## 5. タスク完了チェックリスト (MANDATORY, v5.4 Profile-Aware Reporting)

タスクを「完了」と報告する前に、以下 **Step 1-5 を全 Profile で必ず実行**する。
機械検証は Profile を跨いで同一。Profile が切り替えるのは**人間向けレポートのフォーマットだけ**。
（Opus 4.7 は literal に実行 — 各ステップの「done 条件」を明記）

### 5.0 Profile-Dependent Reporting Matrix

| Profile | Reporting Format | Applicability |
|---------|------------------|---------------|
| `enterprise-erp` | 5-step full report（§5.1 のテンプレ） | 全 WI |
| `saas-integration` | 5-step for critical tier / 1-line for others | `basic_design.coverage_tier == "critical"` の WI のみ 5-step、それ以外は §5.2 の 1-line |
| `prototype` | 1-line summary（§5.2） | 全 WI |

**機械検証は全 Profile で同一**: 下記 **Step 1-5** の全実行が必須。
Profile は「人間向けレポートの冗長さ」のみを切替。Gate 通過条件は不変：

- **Step 1** — AC coverage（`spec_refs → AC-*` の全キーワード充足確認）
- **Step 2** — NFR（performance / security / data / integration）
- **Step 3** — scenarios.yaml（SCN-* の `expected[i]` 検証）
- **Step 4** — `stride lint` PASS（exit 0）
- **Step 5** — `stride pr-check` PR_READY（7/7 base checks、exit 0）

`AC + NFR + pr-check` の三要素に縮める説明は禁止。Step 3（scenarios）と Step 4（stride-lint）は省略不可。

| # | ステップ | done 条件（機械検証可能） | 報告文中の必須行（5-step report 用） |
|---|---------|-------------------------|-----------------|
| 1 | **spec_refs の全 AC を再読** | 該当タスクの `plan_refs` → `spec_refs` → AC-* をすべて列挙し、各 AC に書かれたキーワードを抽出 | `AC-XXX-001: ✅ <抽出したキーワード> 全充足` |
| 2 | **plan.md の関連 NFR 確認** | 該当タスクに関連する NFR（performance / security / data / integration）を列挙 | `NFR: performance ✅, security ✅, data ✅, integration ✅`（該当無しは `N/A + 理由`） |
| 3 | **tests/scenarios.yaml の該当シナリオ全 expected 検証** | 該当 `SCN-*` を特定し、各 `expected[i]` を検証 | `SCN-001: expected[0]✅ expected[1]✅ ...` |
| 4 | **stride-lint PASS** | `stride lint specs/<feature>/` が exit 0 を返す | `stride-lint: PASS (errors=0, warnings=<N>)` |
| 5 | **stride pr-check PR_READY** | `stride pr-check <project_root>` が exit 0 を返す | `stride pr-check: PR_READY (7/7 checks passed)` |

### 5.1 5-step full report（enterprise-erp 全 WI / saas-integration の critical tier WI）

**固定テンプレート（必ずこの順で記載）:**
```
## Task Completion Report: T-XXX-XXX

### Step 1 — AC coverage
AC-XXX-001: ✅ <kw1, kw2, ...>
AC-XXX-002: ✅ ...

### Step 2 — NFR
performance: ✅ / security: ✅ / data: ✅ / integration: ✅

### Step 3 — scenarios.yaml
SCN-001: expected[0]✅ expected[1]✅ ...

### Step 4 — stride-lint
PASS (errors=0, warnings=N)

### Step 5 — stride pr-check
PR_READY (stride-lint ✅ / spec:drift ✅ / tests ✅ / coverage ✅ / walkthrough ✅ / evidence ✅ / TODO ✅)
```

### 5.2 1-line summary format（saas-integration の non-critical / prototype 全 WI）

**canonical 1-line format（literal 一致必須）:**
```
✅ T-XXX-001: AC-* 全充足 / NFR OK / stride-lint PASS / pr-check PR_READY (coverage: <tier>)
```

**task-level 1-line の合成ロジック（AI の責務 — Step 1-5 全実行が前提）:**

1. AI は §5 Step 1、2、3 を実行し AC / NFR / scenarios 検証結果を保持
2. AI は §5 Step 4 で `stride lint` を実行し lint PASS を確認
3. AI は §5 Step 5 で `stride pr-check --summary-line` を実行し project-level summary を取得
4. AI は canonical format で 1 行を合成出力（前段の Step 1-5 全て PASS のとき）:
   ```
   ✅ T-XXX-001: AC-* 全充足 / NFR OK / stride-lint PASS / pr-check PR_READY (coverage: <tier>)
   ```

**最終 1-line sample の分解（literal 一致確認用）:**

| 部分 | 出所 | 対応 bootstrap Step |
|------|------|---------------------|
| `✅` | AI が PR_READY 時に付与 | — |
| `T-XXX-001` | AI の task 文脈 | — |
| `AC-* 全充足` | AI が保持する Step 1 検証結果 | Step 1 |
| `NFR OK` | AI が保持する Step 2 検証結果 | Step 2 |
| `stride-lint PASS` | Step 4 の `stride lint` 実行結果 | Step 4 |
| `pr-check PR_READY` | Step 5 の `--summary-line` から抽出（PR_READY フラグ部分） | Step 5 |
| `(coverage: <tier>)` | AI が `basic_design.coverage_tier` から補完 | — |

**責務境界（v5.4 重要）:**
- `stride pr-check --summary-line` は **project-level** の 1 行（7 base checks + optional mutation）だけを提供する
- Task-level の `T-XXX-001` / `AC-*` / `NFR` / `stride-lint PASS` / `(coverage: <tier>)` は AI が Step 1-5 の結果と task 文脈から合成する
- Step 3（scenarios）と Step 4（stride-lint）の実行を省略して合成することは禁止（1-line 表記では「AC-* 全充足」と「stride-lint PASS」の中に畳み込まれている）

### 5.3 Blocking rule（全 Profile 共通）

- **§5 Step 1-5 のいずれかが欠落・未充足なら「完了」と報告してはならない**（Profile に関わらず）
- `stride pr-check` が PR_READY でなければ、フォーマットに関わらず「完了」報告不可
- 機械検証は全 Profile で同一（stride-lint + pr-check）。報告の冗長さのみ Profile で切替
- 「1-line だから機械検証を省略」という解釈は禁止
- 「動いた」≠「完了」。AC の全要素を満たして初めて完了

---

## 6. Execute Phase: WI/Run 実行モデル

### Work Item (WI) フロー (連番 — literal 実行用)
```
 1. WI 定義作成（risk_flags → mode 自動判定）
 2. wi_readiness_checker.py → PASS 確認（FAIL なら Run 開始禁止）
 3. mode == confirm/validate なら事前承認を人間に依頼（⛔ 停止）
 4. 人間承認後、RUN ディレクトリ作成: specs/<feature>/runs/<WI-ID>/RUN-YYYYMMDD-HHMM/
 5. sdd_planning_bridge.py init <feature_dir> <WI-ID> — .planning/ 作成（SDD 文脈付き）
 5b. [optional v5.3] stride linear init <feature_dir> <WI-ID>
     — LINEAR_API_KEY 設定時、Linear Issue を作成/再利用し state.yaml に linear_issue_id を記録
     — STRIDE_LINEAR_AUTO=1 なら step 5 から自動呼出し
 6. 実装（2-Action Rule: 検索/ブラウズ 2 回ごとに findings.md 更新 / 3-Strike Protocol: 同エラー 3 回で根本再考）
 7. stride-lint 実行 → FAIL は §loop bound に従い自動修正（最大 5 回）
 8. sdd_planning_bridge.py sync <feature_dir> — lint FAIL を plan.md Errors に反映
 9. walkthrough.md 作成（テンプレート: walkthrough_template.md）
10. sdd_planning_bridge.py evidence <feature_dir> <WI-ID> — Planning Evidence を walkthrough.md に挿入
10b. [optional v5.3] stride linear sync <run_dir>
     — Run の findings + walkthrough + test_results + lessons を Linear Issue にコメント投下
     — STRIDE_LINEAR_AUTO=1 なら step 10 から自動呼出し
11. test_results.md 作成（coverage_tier が standard/critical なら必須）
12. sdd_planning_bridge.py learn <feature_dir> <WI-ID> → 候補確認 → --apply で lessons.md に反映
13. /planning:archive 実行 — lessons.md をグローバル知識 (~/.claude/knowledge/) に保存
14. stride-lint 最終実行（PASS 必須）→ §5 タスク完了チェックリスト実施
15. WI 承認依頼（⛔ 停止）— 人間が WI-*.approval.md を編集するまで次 WI に進まない
16. 人間承認後、state.yaml の該当 WI を status: done に更新
16b. [optional v5.3] stride linear close <feature_dir> <WI-ID>
     — 人間承認を受けて Linear Issue を Done 遷移（明示実行、自動化はしない — 承認と独立した人間判断領域）
```

### Mode 判定（リスクに応じた儀式量）
| Mode | 条件 | Pre-run | Post-run |
|------|------|---------|----------|
| autopilot | ui_only, message_only, test_only, logging_only | なし | walkthrough, CI, ops |
| confirm | new_api, contract_change, performance_sensitive | plan_review | walkthrough, CI, ops |
| validate | authz, sod, pii, accounting_calc, db_schema, data_migration | design_diff + plan_review | walkthrough, CI, ops |

### Autonomy Bias
`state.yaml` の `autonomy_bias` (autonomous/balanced/controlled) で Mode をシフト。
ただし `tier_mode_minimum` を下回ることは不可（critical tier は最低 confirm）。

### Run Resume
既存 RUN がある場合、`run_resume_detector.py` で再開ポイントを自動検出。
再開はユーザー確認後のみ（自動再開禁止）。

---

## 7. 品質ゲートコマンド

### 必須（全 Phase 共通）
```bash
# Lint（Phase 完了のたびに自動実行）
sdd-templates/bin/stride lint specs/<feature>/

# PR Readiness（Final 前に実行）— 7チェック統合
sdd-templates/bin/stride pr-check <project_root>
```

### PostToolUse Guard（自動）
Write/Edit 後に `post_edit_guard.py` が自動実行される（`sdd-templates/hooks/settings.json` で設定）。
specs/ 内のファイルに対して軽量チェック（YAML構文, canonical YAML, coverage_policy, plan_refs）を行い、
問題があれば stderr に警告を出力する。開発をブロックしない（fail-open）。

### 初期化
```bash
# Feature 初期化（brownfield 自動検出 + monorepo 設定）
sdd-templates/bin/stride init <feature> --detect
sdd-templates/bin/stride init <feature> --detect --scale standard  # or enterprise

# Intake-First
sdd-templates/bin/stride intake <feature>
```

### Phase Gate
```bash
# Phase 状態確認
sdd-templates/bin/stride phase-status specs/<feature>/

# 次ステップ取得（Auto-Continue）
sdd-templates/bin/stride auto-continue specs/<feature>/
```

### Execute Phase
```bash
# WI 実行準備チェック
python3 sdd-templates/tools/wi_readiness_checker.py specs/<feature>/ <WI-ID>

# Run 再開検出
python3 sdd-templates/tools/run_resume_detector.py specs/<feature>/runs/<WI-ID>/RUN-*/

# Spec Drift 検出
python3 sdd-templates/tools/spec_drift_detector.py <project_root>

# Evidence Metrics 収集
python3 sdd-templates/tools/evidence_metrics_collector.py <project_root>
```

---

## 8. ファイル構造 & 命名規約

### Feature ディレクトリ
```
specs/<feature>/
  basic_design.md          # Phase 1
  process.bpmn             # Phase 1
  APPROVAL.md              # Phase 1（人間のみ編集）
  spec.md                  # Phase 2
  plan.md                  # Phase 2
  contracts/               # Phase 2（OpenAPI等）
  tests/scenarios.yaml     # Phase 2
  tasks.md                 # Phase 3
  implementation-details/  # 全 Phase
    evidence_pack.md
    change_log.md
  work_items/              # Phase 4（Gate 5 後）
  runs/                    # Phase 4
  state/state.yaml         # Phase 4
  ops/                     # Phase 4（ERP addon 必須）
```

### Epic ディレクトリ
```
epics/<EPIC>/
  epic_design.md           # Epic 設計
  epic_flow.bpmn           # Epic overview BPMN（collaboration + pool、planning 用）
  feature_breakdown.md     # Feature 分割
  EPIC_APPROVAL.md         # Epic 承認（人間のみ編集）
  EPIC_PROGRESS_REPORT.md  # 進捗レポート
  DEPENDENCY_MANIFEST.yaml # チーム間依存
  OPS_PACK_REGISTRY.yaml   # Ops Pack 管理
```

> **EPIC BPMN vs FEAT BPMN**: EPIC は `epic_flow.bpmn`（overview/planning 用、collaboration + pool）。FEAT は `process.bpmn`（feature gate 対象、executable BPMN）。

### Canonical YAML ブロック
各成果物の先頭に Canonical YAML セクションがある。`stride-lint` はこのブロックを抽出する。
- basic_design.md: `# 0. Canonical Basic Design (YAML)`
- spec.md: `# 0. Canonical Spec (YAML)`
- plan.md: `# 0. Canonical Plan (YAML)`
- tasks.md: `# 1. Canonical Tasks (YAML)`

### 命名規約
- spec ファイル: snake_case（basic_design.md, spec.md 等）
- テストファイル: `specs/<feature>/tests/` に格納（ルートの tests/ ではない）
- プレースホルダ: FEAT-XXX, FEATXXX, XXX_feature_name → 初期化時に全置換

---

## 9. 出力ルール

- 固定幅 ASCII テーブルを使わない
- 選択肢: `N - **Option**: Description`
- ステータス: `PASS / FAIL / WARN / SKIP` のみ
- 進捗: `[n/N]` 形式

---

## 10. セキュリティ基本ルール

- `memory/tecnos_org_constraints.md` に違反する場合は**即停止して確認**
- ERP / system-of-record への直接 DB 書き込み禁止
- シークレットをコミットしない（.env.example にドキュメント化）
- 監査ログと相関 ID を統合フローに含める

---

## 11. 詳細リファレンス（必要時のみ読む）

| ドキュメント | 読むタイミング |
|-------------|---------------|
| `agent_docs/commands.md` | 全コマンド一覧が必要なとき |
| `agent_docs/testing.md` | Execute Phase でテスト実装時 |
| `agent_docs/security.md` | セキュリティ設計時 |
| `agent_docs/conventions.md` | ID 規約・命名の詳細 |
| `memory/constitution.md` | 組織ガバナンスルール参照時 |
| `memory/tecnos_org_constraints.md` | ERP/監査/セキュリティ制約の詳細 |
| `SDD_MANIFESTO.md` | ツール非依存のコアルール全文 |
| `CLAUDE_WORKFLOW.md` | Claude Code 固有の設定詳細 |

---

> SDD Templates v5.4.0-tecnos-stride — Bootstrap for Claude Code
