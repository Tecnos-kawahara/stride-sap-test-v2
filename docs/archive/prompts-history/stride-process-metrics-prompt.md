# Tecnos-STRIDE Process Metrics 実装タスク

> **作成日:** 2026-02-19 ｜ **改修日:** 2026-02-20（cbp-core対応追加）
> **対象リポジトリ:**
> - `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/` （標準テンプレート）
> - `/Users/j620h-okzk/ZINOKZ/cbp-core/` （AIプラットフォーム）

Tecnos-STRIDE にプロセスタイム分析・進捗分析の機能を追加したい。
GitHub Projects V2 で可視化するのが前提。
**標準テンプレートとcbp-coreの両リポジトリで共通的に動作すること。**

**目的:**
- Gate別滞留時間の可視化（どの工程でボトルネックが発生しているか）
- WI・Epic単位の遅延リスク自動検知
- GitHub Projects V2 への自動同期
- PM_DASHBOARD.md への「Process Metrics」セクション追加

## リポジトリ構造の差異（重要：実装前に必ず理解すること）

2つのリポジトリはSTRIDEの同じ5-Gate構造を使うが、**データの持ち方が異なる**。
スクリプトはこの差異を自動検出して両方に対応する必要がある。

| 項目 | sdd_template_enterprise | cbp-core |
|------|------------------------|----------|
| **Gate承認管理** | `specs/<feature>/state/state.yaml` | `specs/<feature>/APPROVAL.md` |
| **Gate承認日時の取得方法** | state.yamlのフィールドから直接読み取り | APPROVAL.mdの `日付:` 行をパース |
| **WI管理** | state.yaml内の `work_items:` 配列 | `specs/<feature>/work_items/SU-*.md` のfrontmatter |
| **WIステータス** | state.yaml内 `status:` フィールド | WI mdファイルのfrontmatter `state:` フィールド |
| **feature名** | specs配下のディレクトリ名 | specs配下のディレクトリ名（`*-plane` 等） |
| **Epic管理** | `epics/EPIC-*` ディレクトリ | `epics/EPIC-*` ディレクトリ |
| **PM_DASHBOARD.md** | `epics/EPIC-*/PM_DASHBOARD.md` | なし（新規作成が必要） |
| **既存スクリプト言語** | Python | JavaScript/Node.js |

### APPROVAL.md のパース仕様（cbp-core用）

cbp-coreの `APPROVAL.md` は以下の構造を持つ:
```markdown
## Gate 1: Basic Design
確認項目：
- [x] basic_design.md の WHO/WHAT/WHY が正しい
...
承認者: CBP Architecture Team
日付:   2026-01-19

## Gate 2: BPMN
...
日付:   2026-01-19
```

パースルール:
1. `## Gate N:` or `## Final:` でセクションを区切る
2. チェックボックス `- [x]` が全て完了 → Gate承認済み
3. `日付:` 行の値（YYYY-MM-DD）→ Gate承認日時
4. チェックボックスに `- [ ]`（未完了）が1つでもあれば → Gate未承認

### WI mdファイルのfrontmatter仕様（cbp-core用）

cbp-coreの `work_items/SU-*.md` は以下のfrontmatterを持つ:
```yaml
---
wi_id: "SU-1"
title: "Add HITL API endpoints..."
feature_id: "agentops-plane"
complexity: "medium"
mode: "autopilot"
state: "closed"          # closed / in_progress / pending
dependencies: []
---
```

**プロセスメトリクス指標:**

| 指標 | STRIDEデータソース | 意味 |
|-----------|-----------------|------|
| プロセスタイム（工程別） | `state.yaml` の Gate承認日時 or `APPROVAL.md` の承認日付 | Gate 1〜Final間の各工程の滞留日数 |
| 待機時間 | Gate承認待ち + レビュー依頼からの経過時間 | ボトルネックの可視化 |
| 差し込み率 | WI作成後に追加されたタスク数 / 当初タスク数 | 計画精度の指標 |
| 期日変更率 | WI期日の変更回数（Issueイベントから） | スコープ安定性 |
| 遅延アラート | 現在Gate + 残日数 vs 複雑度標準日数 | リスク早期検知 |
| デプロイ頻度（Four Keys） | GitHub Actions CI/CD実行履歴 | DORAメトリクス |
| 変更リードタイム | WI開始〜merge完了の時間 | 開発速度 |

## タスク一覧

### Task 1: `scripts/stride_process_metrics.py` を新規作成

**設計方針: データソース自動検出（Adapter Pattern）**

スクリプトは実行時にfeatureディレクトリの構造を自動検出し、適切なデータソースを選択する:
```python
def detect_repo_type(feature_path):
    """リポジトリタイプを自動検出"""
    state_yaml = os.path.join(feature_path, "state", "state.yaml")
    approval_md = os.path.join(feature_path, "APPROVAL.md")
    wi_dir = os.path.join(feature_path, "work_items")

    if os.path.exists(state_yaml):
        return "template"    # sdd_template_enterprise
    elif os.path.exists(approval_md) and os.path.exists(wi_dir):
        return "cbp-core"    # cbp-core（APPROVAL.md + WI個別ファイル方式）
    else:
        raise ValueError(f"Unknown repo structure: {feature_path}")
```

**機能要件:**

1. **Gate承認データの読み込み（2方式対応）**

   **方式A（template）:** `specs/<feature>/state/state.yaml` を読み込む
   - 各Gate（Gate 1〜Gate 5 + Evidence）の承認タイムスタンプから工程別滞留日数を計算

   **方式B（cbp-core）:** `specs/<feature>/APPROVAL.md` をパースする
   - `## Gate N:` セクションごとに `日付:` 行を抽出
   - チェックボックス `- [x]` の完了状態を確認
   - `## Final:` セクションはテンプレートの `Evidence` に相当するものとして扱う
   - パース例:
     ```python
     def parse_approval_md(path):
         """APPROVAL.mdからGate承認日時を抽出"""
         gates = {}
         current_gate = None
         all_checked = True
         for line in open(path):
             if line.startswith("## Gate ") or line.startswith("## Final"):
                 if current_gate and all_checked:
                     gates[current_gate]["approved"] = True
                 # parse gate name
                 current_gate = normalize_gate_name(line)
                 gates[current_gate] = {"date": None, "approved": False}
                 all_checked = True
             elif "- [ ]" in line:
                 all_checked = False
             elif line.strip().startswith("日付:"):
                 date_str = line.split(":", 1)[1].strip()
                 gates[current_gate]["date"] = date_str
         # handle last gate
         if current_gate and all_checked:
             gates[current_gate]["approved"] = True
         return gates
     ```

2. **WIデータの読み込み（2方式対応）**

   **方式A（template）:** `state.yaml` 内の `work_items:` 配列から読み取り

   **方式B（cbp-core）:** `specs/<feature>/work_items/SU-*.md` のYAML frontmatterを読み取り
   - フィールドマッピング:
     | template (state.yaml) | cbp-core (WI frontmatter) |
     |----------------------|--------------------------|
     | `wi_id` | `wi_id` |
     | `status` | `state` |
     | `complexity` | `complexity` |
     | `mode` | `mode` |
     | `completed_at` | （なし。git log から推定、またはnull） |

3. 計算結果を以下の形式で出力する（共通フォーマット）:

```json
{
  "repo_type": "cbp-core",
  "feature": "agentops-plane",
  "gate_process_times": {
    "gate1_design": {"start": "2026-01-19", "end": "2026-01-19", "days": 0, "approved": true},
    "gate2_bpmn": {"start": "2026-01-19", "end": "2026-01-19", "days": 0, "approved": true},
    "gate3_spec": {"start": "2026-01-19", "end": "2026-01-19", "days": 0, "approved": true},
    "gate4_plan": {"start": "2026-01-19", "end": "2026-01-19", "days": 0, "approved": true},
    "gate5_tasks": {"start": "2026-01-19", "end": "2026-01-19", "days": 0, "approved": true},
    "final": {"start": "2026-01-19", "end": "2026-01-19", "days": 0, "approved": true}
  },
  "total_days": 0,
  "current_gate": "final",
  "current_gate_age_days": 0,
  "delay_risk": "on_track",
  "work_items": [
    {"wi_id": "SU-1", "state": "closed", "complexity": "medium"},
    {"wi_id": "SU-2", "state": "closed", "complexity": "low"}
  ]
}
```

4. 遅延リスク判定ロジック（共通）:
   - `current_gate_age_days` が Complexity別の閾値を超えたら `at_risk`
   - 閾値: low=3日, medium=5日, high=7日 → `overdue`、その半分で → `at_risk`

5. CLI引数:
   - `--feature <path>`: featureパス (例: `specs/sample_erp_addon` or `specs/agentops-plane`)
   - `--epic <path>`: epicパス内の全featureを対象 (例: `epics/EPIC-SAMPLE` or `epics/EPIC-CORE`)
   - `--all`: specs/配下の全featureを対象（cbp-coreで特に有用）
   - `--output json|table|markdown`: 出力形式 (デフォルト: table)
   - `--update-dashboard`: PM_DASHBOARD.mdを自動更新
   - `--repo-type auto|template|cbp-core`: 強制指定（デフォルト: auto = 自動検出）

**参考にすべき既存コード:**
- `sdd_template_enterprise/scripts/sync_projects_to_stride.py` — state.yaml読み込みパターン
- `sdd_template_enterprise/sdd-templates/tools/epic_progress_aggregator.py` — Epic横断集計パターン
- `sdd_template_enterprise/sdd-templates/tools/run_report_generator.py` — レポート生成・Issue更新パターン

**データソース参照:**
- テンプレート: `sdd_template_enterprise/specs/sample_erp_addon/state/state.yaml`
- cbp-core: `cbp-core/specs/agentops-plane/APPROVAL.md` + `cbp-core/specs/agentops-plane/work_items/SU-*.md`

---

### Task 2: `scripts/auto_set_project_fields.py` に Process Metrics フィールド設定を追加

**追加するフィールド:**
- `Gate Age (days)`: Number型 → `current_gate_age_days` の値をセット
- `Delay Risk`: Single Select → `on_track` / `at_risk` / `overdue`
- `Gate`: Single Select → 現在のGate名 (`g1`〜`evidence`)

**実装方針:**
- 既存の `item_edit()` / `get_field_map()` パターンを踏襲
- `stride_process_metrics.py` をimportまたはサブプロセス呼び出しで利用
- `--feature` オプションが指定された場合に追加フィールドを更新

---

### Task 3: PM_DASHBOARD.md に「Process Metrics」セクションを追加

**対象ファイル:**
- テンプレート: `epics/EPIC-SAMPLE/PM_DASHBOARD.md`（既存ファイルに追記）
- cbp-core: `epics/EPIC-CORE/PM_DASHBOARD.md`（**新規作成**。cbp-coreにはまだPM_DASHBOARD.mdが存在しない）

**cbp-core用PM_DASHBOARD.md新規作成時の注意:**
- cbp-coreには10個のfeature（plane）が存在する: agentops-plane, ai-ux-enhancement, business-application-plane, control-plane, data-ai-plane, master-admin-ui, platform-plane, runtime-plane, shared, web-edi
- 全featureを横断したサマリを冒頭に置き、feature別の詳細を後続に配置する

**追加する場所:** 「Gate Progress」セクションの直後（テンプレート）、またはファイル冒頭のサマリ直後（cbp-core新規作成時）

**追加するコンテンツ（テンプレート形式で）:**

```markdown
## Process Metrics

> Generated by `stride_process_metrics.py` | Updated: YYYY-MM-DD

### Gate別滞留時間（プロセスタイム分析）

| Gate | 開始 | 完了 | 滞留日数 | 状態 |
|------|------|------|---------|------|
| Gate 1: Design Review | 2026-02-01 | 2026-02-01 | 0日 | ✅ |
| Gate 2: BPMN Review | 2026-02-01 | 2026-02-01 | 0日 | ✅ |
| Gate 3: Spec Review | 2026-02-01 | 2026-02-03 | 2日 | ✅ |
| Gate 4: Plan Review | 2026-02-03 | 2026-02-05 | 2日 | ✅ |
| Gate 5: Tasks Review | 2026-02-05 | 2026-02-05 | 0日 | ✅ |
| Evidence Review | 2026-02-05 | -(進行中) | **14日** | 🟡 at_risk |

**合計プロセスタイム:** 4日（完了Gate） + 現在14日経過

### WI別遅延リスクサマリ

| WI ID | Complexity | 現在Gate | 滞留日数 | リスク |
|-------|-----------|---------|---------|-------|
| WI-ERP-SAMPLE-001 | medium | evidence | 14日 | 🟡 at_risk |
| WI-ERP-SAMPLE-002 | high | gate3_spec | 2日 | 🟢 on_track |

### 差し込み率

| WI ID | 当初タスク数 | 現在タスク数 | 差し込み率 | 評価 |
|-------|-----------|-----------|---------|------|
| WI-ERP-SAMPLE-001 | 8 | 9 | 12.5% | 🟢 良好 |
| WI-ERP-SAMPLE-002 | 6 | 6 | 0% | 🟢 良好 |
```

---

### Task 4: `agent_docs/github_project_views.md` に「View 6: Process Metrics View」を追加

**追加する内容:**
- Table View の設定手順
- カラム: Title / Status / WI ID / Gate / Gate Age (days) / Delay Risk / Complexity
- フィルタ例: `Delay Risk is at_risk OR overdue`
- 活用方法の説明

---

### Task 5: GitHub Actionsワークフロー にProcess Metrics自動更新を追加

**テンプレート:** `stride-sync.yml` に追加
**cbp-core:** 既存のCIワークフローに追加、または新規 `stride-metrics.yml` を作成

**トリガー:**
- テンプレート: `state.yaml` の変更がpushされた時
- cbp-core: `APPROVAL.md` または `work_items/*.md` の変更がpushされた時

**追加するステップ（共通）:**
```yaml
- name: Update Process Metrics
  run: |
    python scripts/stride_process_metrics.py \
      --all \
      --update-dashboard \
      --output markdown
```

**cbp-core用のトリガー設定例:**
```yaml
on:
  push:
    paths:
      - 'specs/*/APPROVAL.md'
      - 'specs/*/work_items/*.md'
```

---

## GitHub Projects V2 カスタムフィールド追加

以下のフィールドをGitHub Projectsに追加する:

| フィールド名 | 型 | 選択肢 | 用途 |
|-------------|----|----- --|------|
| `Gate Age (days)` | Number | — | 現在Gateでの滞留日数 |
| `Delay Risk` | Single Select | `on_track` / `at_risk` / `overdue` | 遅延リスク |
| `Inject Rate` | Single Select | `0%` / `1-20%` / `21-50%` / `50%+` | 差し込み率 |
| `Lead Time (days)` | Number | — | WI開始〜完了の日数 |
| `Gate` | Single Select | `g1`〜`evidence` | 現在のGate |

**フィールド作成コマンド:**
```bash
gh project field-create <N> --owner <OWNER> --name "Gate Age (days)" \
  --data-type "NUMBER"
gh project field-create <N> --owner <OWNER> --name "Delay Risk" \
  --data-type "SINGLE_SELECT" --single-select-options "on_track,at_risk,overdue"
gh project field-create <N> --owner <OWNER> --name "Inject Rate" \
  --data-type "SINGLE_SELECT" --single-select-options "0%,1-20%,21-50%,50%+"
gh project field-create <N> --owner <OWNER> --name "Lead Time (days)" \
  --data-type "NUMBER"
gh project field-create <N> --owner <OWNER> --name "Gate" \
  --data-type "SINGLE_SELECT" --single-select-options "g1,g2,g3,g4,g5,evidence"
```

---

## 実装上の注意事項

1. **データソースのスキーマを確認してから実装する**
   - テンプレート: `specs/sample_erp_addon/state/state.yaml` の実際のフィールド名・構造に合わせる
   - cbp-core: `specs/agentops-plane/APPROVAL.md` のセクション構造と `work_items/SU-*.md` のfrontmatterに合わせる
   - 仮定で実装しない。**必ず実ファイルを読んでから実装すること**

2. **既存コードのパターンを踏襲する**
   - `gh` CLI呼び出しは既存の `run_gh()` / `run_gh_json()` ヘルパーを使う
   - エラーハンドリングは既存スクリプトと同じスタイルで
   - cbp-coreの既存スクリプトはJSだが、本スクリプトはPythonで統一（テンプレートと共通化のため）

3. **段階的に実装・検証する**
   - Task 1 → Task 2 → Task 3 の順で実装・動作確認してから次へ
   - Task 4・5 は Task 1〜3 が動いてから
   - **テンプレートで動作確認 → cbp-coreで動作確認** の2段階検証を行う

4. **ドライランモードを必ず実装する**
   - `--dry-run` フラグで実際のファイル変更・API呼び出しをスキップ
   - デバッグ用に `--verbose` フラグも実装する

5. **テンプレート変数の扱い**
   - PM_DASHBOARD.mdの更新は「## Process Metrics」セクション全体を
     生成コンテンツで置換する方式（正規表現で範囲検出）
   - cbp-coreで新規作成する場合はファイル全体を生成

6. **Gate名の正規化**
   - テンプレートの `Evidence` と cbp-coreの `Final: Implementation` は同じステージとして扱う
   - 正規化マッピング:
     ```python
     GATE_ALIASES = {
         "Gate 1: Basic Design": "gate1_design",
         "Gate 1: Design Review": "gate1_design",
         "Gate 2: BPMN": "gate2_bpmn",
         "Gate 2: BPMN Review": "gate2_bpmn",
         "Gate 3: Spec": "gate3_spec",
         "Gate 3: Spec Review": "gate3_spec",
         "Gate 4: Plan": "gate4_plan",
         "Gate 4: Plan Review": "gate4_plan",
         "Gate 5: Tasks": "gate5_tasks",
         "Gate 5: Tasks Review": "gate5_tasks",
         "Final: Implementation": "final",
         "Evidence Review": "final",
         "evidence": "final",
     }
     ```

## 完了条件

**テンプレートリポジトリ:**
- [ ] `python scripts/stride_process_metrics.py --feature specs/sample_erp_addon --output table` が動く
- [ ] PM_DASHBOARD.mdに「Process Metrics」セクションが追加されている
- [ ] `--dry-run` フラグが正しく動作する
- [ ] 既存のCIワークフロー（stride-lint.yml等）が壊れていない

**cbp-coreリポジトリ:**
- [ ] `python scripts/stride_process_metrics.py --feature specs/agentops-plane --output table` が動く
- [ ] `python scripts/stride_process_metrics.py --all --output table` で全10 featureが一覧表示される
- [ ] `epics/EPIC-CORE/PM_DASHBOARD.md` が新規生成される（`--update-dashboard`時）
- [ ] APPROVAL.mdの未承認Gate（`- [ ]` あり）が正しく検出される
- [ ] `work_items/SU-*.md` のfrontmatterからWI情報が正しく読み取られる

---

## 優先順位

| 優先度 | タスク | 理由 |
|-------|--------|------|
| 🔴 最高 | Task 1 (stride_process_metrics.py) | 全ての基盤。Adapter Patternで両リポジトリ対応 |
| 🔴 最高 | Task 3 (PM_DASHBOARD.md更新) | PMの視認性。cbp-coreは新規作成 |
| 🟡 中 | Task 2 (auto_set_project_fields.py) | Projects連携 |
| 🟡 中 | Task 4 (View 6追加) | PMガイド |
| 🟢 低 | Task 5 (CI自動化) | Task 1-4完了後。cbp-coreはAPPROVAL.mdトリガー |

## スクリプトの配置

スクリプトは**テンプレートリポジトリに実装し、cbp-coreにはコピーまたはシンボリックリンクで配置**する。
将来的にはPyPIパッケージ化またはgit submodule化を検討する。

```
sdd_template_enterprise/scripts/stride_process_metrics.py  ← 実装元
cbp-core/scripts/stride_process_metrics.py                  ← コピー配置
```
