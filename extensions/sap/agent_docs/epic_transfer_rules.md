# Epic 転写ルール — 機能群仕様書 YAML → STRIDE Epic 構造

> **compaction 後は本ファイルを再読すること。**

## 概要

SAP 仕様書エディタで作成された機能群仕様書 YAML（`function-group-spec/v2`）を STRIDE の Epic 構造に転写するためのルール。

転写先は `stride epic init <EPIC_ID>` で生成された空テンプレート（`epics/<EPIC_ID>/`）。
転写後に `stride epic validate <EPIC_ID>` を実行し、E1 バリデーションをパスすること。

---

## 前提条件

| # | 条件 | 確認方法 |
|---|------|---------|
| 1 | `stride epic init <EPIC_ID>` が実行済み | `epics/<EPIC_ID>/epic_design.md` が存在する |
| 2 | 機能群仕様書 YAML が準備済み | `docs/yaml/<GROUP_ID>/<GROUP_ID>.group.yaml` が存在する |
| 3 | YAML に `ownership`、`coverageTier`、`sharedContracts` が含まれている | yaml 内にキーが存在する |

**上記が 1 つでも未完了の場合、転写を開始してはならない。**

- `ownership`、`coverageTier`、`sharedContracts` が YAML に存在しない場合は、仕様書ツール側の対応完了を待つか、人間にこれらの情報を確認して手動で補完する
- `stride epic init` を実行せずに epic_design.md を作成すると、EPIC_APPROVAL.md やディレクトリ構成が欠落し、`stride epic validate` が正常に動作しない

---

## Epic ID の決定

### STRIDE 標準の ID 制約

```
Epic ID: ^EPIC-[A-Z]{3,}$
```

**英大文字のみ、数字不可。** 例: `EPIC-ORDER`, `EPIC-EDILOT`, `EPIC-FIARAP`

### SAP 機能群 ID からの変換

SAP の機能群 ID（例: `FG-SD005-003`）は数字を含むため、そのまま Epic ID に変換できない。
以下の手順で Epic ID を決定する:

1. **機能群名（groupName）から意味のある英字略称を導出**する
2. 人間に提案して承認を得る

| 機能群 ID | 機能群名 | 提案 Epic ID | 導出根拠 |
|-----------|---------|-------------|---------|
| `FG-SD005-003` | EDI入庫/ロットトレース | `EPIC-EDILOT` | EDI + LOT(trace) |
| `FG-FI001-001` | 売掛金管理 | `EPIC-FIARAP` | FI + AR + AP |

**AI は Epic ID を独断で決定してはならない。必ず人間に提案して承認を得ること。**

### 機能群 ID の追跡

転写元の機能群 ID を epic_design.md 内で追跡できるよう、`epic.meta` に以下を追加する:

```yaml
epic:
  meta:
    epic_id: "EPIC-EDILOT"
    sap_group_id: "FG-SD005-003"      # ← 転写元の機能群 ID
    sap_group_yaml: "docs/yaml/FG-SD005-003/FG-SD005-003.group.yaml"
```

---

## 転写手順

### Step E-1: Epic ディレクトリの初期化

```bash
stride epic init <EPIC_ID>
```

### Step E-2: 機能群 YAML の読み込みと転写

**ツール**: `extensions/sap/tools/epic_transfer.py`

```bash
python3 extensions/sap/tools/epic_transfer.py \
  --yaml docs/yaml/FG-SD005-003/FG-SD005-003.group.yaml \
  --epic-dir epics/EPIC-EDILOT/ \
  --epic-id EPIC-EDILOT
```

ツールが以下を実行する:
1. 機能群 YAML を読み込み
2. マッピングテーブル（後述）に従い epic_design.md の YAML ブロックを生成
3. feature_breakdown.md の YAML ブロックを生成
4. 既存テンプレートのプレースホルダ部分を転写データで置換

### Step E-3: 手動補完

ツールが生成した結果には、機能群 YAML に対応データがなく空となっている項目がある。
以下を人間または AI が補完する:

| 項目 | 補完方法 |
|------|---------|
| `ownership.sponsor` | 人間に確認 |
| `scope.value_stream` | AI が SAP モジュール（SD/FI/MM 等）から推定し、人間に確認 |
| `scope.strategic_alignment` | 人間に確認 |
| `scope.out_of_scope` | AI が businessSpec から推定可能な範囲で提案 |
| `features[].dependencies` | `interFunctionConnections` から推定、不足分は人間に確認 |
| `milestones` | 人間に確認 |
| `risks` | AI がビジネス要件から推定し、人間に確認 |

### Step E-4: バリデーション

```bash
stride epic validate <EPIC_ID>
```

E1 Gate の検証項目:
- `epic_design.md` が存在するか
- `epic_id` が `^EPIC-[A-Z]{3,}$` に一致するか（プレースホルダでないか）
- `ownership.epic_lead` が設定されているか
- `ownership.teams[]` が定義されているか
- 各 `team_id` が `^TEAM-[A-Z]{1,3}$` に一致するか
- 各 Feature の `coverage_tier` が有効値か

### Step E-5: 承認依頼

全バリデーション PASS 後、人間に EPIC_APPROVAL.md の Gate E1 承認を依頼する。

**EPIC_APPROVAL.md を AI が編集することは絶対禁止。**

---

## マッピングテーブル: 機能群 YAML → epic_design.md

### meta

| 機能群 YAML | epic_design.md | 変換 |
|------------|----------------|------|
| `meta.groupId` | `epic.meta.sap_group_id` | そのまま（追跡用） |
| — | `epic.meta.epic_id` | Step E-1 で決定した ID |
| `meta.groupName` | `epic.meta.title` | そのまま |
| — | `epic.meta.version` | `"1.0.0"` |
| `meta.status` | `epic.meta.status` | そのまま |
| `meta.updated` | `epic.meta.created_at` / `updated_at` | そのまま |

### ownership

| 機能群 YAML | epic_design.md | 変換 |
|------------|----------------|------|
| — | `epic.ownership.sponsor` | 空文字（手動補完） |
| `ownership.epicLead` | `epic.ownership.epic_lead` | そのまま |
| `ownership.teams[].teamId` | `epic.ownership.teams[].team_id` | そのまま |
| `ownership.teams[].name` | `epic.ownership.teams[].name` | そのまま |
| `ownership.teams[].lead` | `epic.ownership.teams[].lead` | そのまま |
| `ownership.teams[].features[]` | `epic.ownership.teams[].features[]` | そのまま |

### scope（businessSpec → scope）

| 機能群 YAML | epic_design.md | 変換 |
|------------|----------------|------|
| `businessSpec.context.who` | `epic.scope.business_context.who` | そのまま |
| `businessSpec.context.what` | `epic.scope.business_context.what` | そのまま |
| `businessSpec.context.why.目的` + `why.背景` | `epic.scope.business_context.why` | 結合 |
| — | `epic.scope.value_stream` | 空文字（手動補完） |

### features（functionRoster → features）

| 機能群 YAML | epic_design.md | 変換 |
|------------|----------------|------|
| `functionRoster[].featureId` | `epic.features[].feature_id` | そのまま |
| `functionRoster[].name` | `epic.features[].name` | そのまま |
| `functionRoster[].coverageTier` | `epic.features[].coverage_tier` | そのまま（未指定時 `standard`） |
| — | `epic.features[].team_id` | `ownership.teams[].features[]` から逆引き |
| — | `epic.features[].priority` | 配列インデックス + 1 |
| `functionRoster[].name` | `epic.features[].description` | name を使用 |

**team_id の逆引き**: `ownership.teams[].features[]` に含まれる featureId を検索し、該当するチームの team_id を設定する。

### shared_contracts（sharedContracts → shared_contracts）

| 機能群 YAML | epic_design.md | 変換 |
|------------|----------------|------|
| `sharedContracts[].contractId` | `epic.shared_contracts[].contract_id` | そのまま |
| `sharedContracts[].name` | `epic.shared_contracts[].name` | そのまま |
| `sharedContracts[].type` | `epic.shared_contracts[].type` | そのまま |
| `sharedContracts[].ownerTeam` | `epic.shared_contracts[].owner_team` | そのまま |
| `sharedContracts[].ownerFeature` | `epic.shared_contracts[].owner_feature` | そのまま |
| `sharedContracts[].consumers[]` | `epic.shared_contracts[].consumers[]` | そのまま |

### cross_team_dependencies

| 機能群 YAML | epic_design.md | 変換 |
|------------|----------------|------|
| `functionStructure.interFunctionConnections[]` | `epic.cross_team_dependencies[]` | 各接続を DEP-NNN に変換 |

### epic_gate_check（自動計算）

| フィールド | 計算方法 |
|-----------|---------|
| `total_features` | `len(functionRoster)` |
| `critical_features` | `coverageTier == "critical"` の件数 |
| `standard_features` | `coverageTier == "standard"` の件数 |
| `all_features_have_team` | 全 feature に team_id が割り当てられているか |
| `shared_contracts_defined` | `sharedContracts` が 1 件以上か |

---

## マッピングテーブル: 機能群 YAML → feature_breakdown.md

| 機能群 YAML | feature_breakdown.md | 変換 |
|------------|---------------------|------|
| `functionRoster[].featureId` | `features[].feature_id` | そのまま |
| `functionRoster[].name` | `features[].name` | そのまま |
| `functionRoster[].type` | `features[].type` | そのまま |
| `functionRoster[].sapId` | `features[].sap_id` | そのまま |
| `functionRoster[].programId` | `features[].program_id` | そのまま |
| `functionRoster[].coverageTier` | `features[].coverage_tier` | そのまま |
| `functionStructure.interFunctionConnections[]` | `dependency_graph.edges[]` | from/to/type を変換 |
| `functionStructure.splitRationale` | `split_rationale` | そのまま |

---

## キー名変換規約

機能群 YAML は camelCase（JavaScript 慣習）、epic_design.md は snake_case（Python/STRIDE 慣習）。

| 機能群 YAML（camelCase） | epic_design.md（snake_case） |
|--------------------------|------------------------------|
| `featureId` | `feature_id` |
| `epicLead` | `epic_lead` |
| `teamId` | `team_id` |
| `coverageTier` | `coverage_tier` |
| `contractId` | `contract_id` |
| `ownerTeam` | `owner_team` |
| `ownerFeature` | `owner_feature` |

---

## 不整合検出時の行動規範

転写中にソース YAML 内の不整合を検出した場合（Phase 1 の phase1_design.md と同じルール）:
- **AI が独自判断で修正・補完してはならない**
- 不整合の内容と箇所を明示的にエラーとして報告し、人間に修正を依頼する
- 人間がソース YAML を修正した後、再度転写を実行する

---

## Epic Gate E1 承認後の次ステップ

E1 承認後、以下の順序で進める:

1. `feature_breakdown.md` の詳細化 → `stride epic validate` → E2 承認
2. `shared_contracts` の IF 定義 → E3 承認
3. 各 Feature の SDD Phase 1 開始: `stride init <feature> --epic <EPIC_ID>`
4. E4（統合テスト計画）、E5（Feature Specs Ready）の承認
5. E3 再承認（E5 後に IF 最終確認）
6. 各 Feature の Phase 2〜4 + Final
7. Epic Final Gate
