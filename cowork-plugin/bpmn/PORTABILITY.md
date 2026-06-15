# PORTABILITY — Tecnos override の内訳と別プロジェクトへの移植ガイド

> **このパッケージは Tecnos-STRIDE v5.4.0 から派生**。Tecnos 固有の慣習が一部混在するため、別プロジェクトで使う際の「採用判断」と「置換ガイド」をここに集約する。

---

## 1. ルール 2 層構造の理解

| 層 | 内容 | 別プロジェクトでの扱い |
|----|------|----------------------|
| **Universal (BPMN 2.0 + Camunda 8 由来)** | OMG 仕様 / Zeebe 拡張 / FEEL / ISO-8601 / 接続ルール / 実行セマンティクス | **そのまま採用必須** (BPMN を Camunda で動かすなら不可避) |
| **Tecnos override (SDD/HITL レビュー由来)** | 縦型 layout / pool-lane 強制 / BPMN-* ID / FEAT vs EPIC 区別 / `bpmn:documentation` 第2正本 | **採用判断**: 全採用 / 部分採用 / 採用しない の 3 択 |

---

## 2. Tecnos override の項目別内訳

各 override は「なぜ Tecnos がそうしているか」と「他プロジェクトで採用しない場合の対処」をセットで提示する。

### 2.1 縦型 (Top-to-Bottom) Layout

**Tecnos rule**: メインフローは Y 軸を段階的に増加させる縦並び。Start Event 上端、End Event 下端。

**Why Tecnos**: 顧客レビュー時の A4 縦印刷 + 縦長 PDF + モバイル Web Modeler に最適化。コンサル業務で印刷物として配布されるため。

**OMG/Camunda 推奨**: 左→右 (西洋読み順 / 横長スクリーン)。

**他プロジェクトで採用しない場合**:
- `rules/bpmn_generator_rules.md` §24.2 の縦型 layout 詳細を「左→右」に読み替え
- テンプレート (`templates/*.bpmn`) の `<dc:Bounds>` 座標を横並びに調整 (X 増加、Y 一定)
- Camunda Modeler でドラッグ&ドロップで再配置すれば自動的に座標が更新される

**`bpmn_lint.py` への影響**: なし (lint は座標方向を検証しない)

---

### 2.2 Pool/Lane 強制 + `isHorizontal="false"`

**Tecnos rule**: FEAT で actor が複数なら laneSet を使う or pool/participant を使う。pool shape は `isHorizontal="false"` 強制。EPIC は 2+ pool を必須。

**Why Tecnos**: SDD の `basic_design.bpmn_descriptions` の actor 軸と整合させるため。HITL レビューで「誰が何を担当するか」が一目で分かる必要がある。

**OMG/Camunda 推奨**: 操作レベルでは "Avoiding lanes" を推奨 (公式ベストプラクティス、メンテ困難の経験則由来)。

**他プロジェクトで採用しない場合**:
- 単一 pool / lane なしで `process` 直下に flow node を配置可能
- `validators/bpmn_lint.py` の `isHorizontal="false"` チェックは participant shape のみに発動するため、participant を使わなければ警告は出ない
- EPIC のような cross-team overview が必要なら、pool は使わざるを得ない (OMG 仕様で collaboration の構造要件)

**`bpmn_lint.py` 適用範囲**: participant が存在する BPMN のみ vertical swimlane を強制。pool なし FEAT は影響なし。

---

### 2.3 ID 命名規則

**Tecnos rule**:
- FEAT: `BPMN-PROC-<FEATID>` / `BPMN-TASK-001` / `BPMN-GW-001` / `BPMN-EVT-001` / `BPMN-FLOW-001` (3 桁ゼロパディング)
- EPIC: `Process_A` / `Task_A_Send` / `Flow_A_001` / `MsgFlow_AtoB`
- 混在禁止

**Why Tecnos**: `basic_design.bpmn_descriptions[].bpmn_id` と `epic_design.epic_flow_descriptions` との 1:1 traceability を機械検証可能にするため。AI が prefix を見ただけで FEAT vs EPIC を区別できる。

**OMG/Camunda 推奨**: ID 形式は任意 (Camunda Modeler はランダム ID を自動生成)。

**他プロジェクトで採用しない場合**:
- `rules/bpmn_generator_rules.md` §24.1 の ID 命名規則を **「無視」または「自プロジェクトの命名規則に置換」**
- `validators/bpmn_lint.py` は ID 形式を検証しない (実在性のみ検証)
- ただし、AI に BPMN を書かせる場合、何らかの一貫した命名は採用したほうが良い (review しやすさのため)

---

### 2.4 FEAT vs EPIC の二重構造

**Tecnos rule**: 単一 feature の executable は `process.bpmn` (FEAT)、複数チーム/システム間の overview は `epic_flow.bpmn` (EPIC) と分離。検証ツールも別 (`stride lint` vs `epic_validator.py`)、ID スキームも別。

**Why Tecnos**: SDD で Phase 1 設計時に「実装単位」と「組織越境フロー」が混在しないようにする。Camunda 実行は executable のみ、overview は HITL レビュー専用。

**OMG/Camunda 推奨**: 区別なし。collaboration 内に複数 process があれば、それで OK。

**他プロジェクトで採用しない場合**:
- 単一の `process.bpmn` で済ませる (collaboration + 多 process でも単一ファイル可)
- `validators/bpmn_lint.py` の auto-detect は participant 数で FEAT/EPIC を判定するため、構造が同じなら適切に判定される
- `--feat` / `--epic` で強制指定も可能

---

### 2.5 `bpmn:documentation` 第2正本必須化

**Tecnos rule**: process / userTask / serviceTask / 条件付き gateway / 条件付き sequenceFlow に `<bpmn:documentation>` を必須記入。第1正本は `basic_design.md` の `bpmn_descriptions`。

**Why Tecnos**: AI/開発者が BPMN ファイル単体を読んで業務意図を理解できるようにする (BPMN ファイルは Camunda Modeler で開かれることも多いため、figure-only ではなく self-contained にする)。

**OMG/Camunda 推奨**: optional。

**他プロジェクトで採用しない場合**:
- `bpmn:documentation` を書かない選択肢は OK
- `validators/bpmn_lint.py` の `BPMN_DOCUMENTATION_MISSING` は **warning** (error ではない)、CI を fail させない
- それでも、AI に書かせる場合は documentation を強制したほうが review 品質が上がる

---

### 2.6 14 MUST-DO (FEAT) / 9 MUST-DO (EPIC) の網羅検証

**Tecnos rule**: `validators/bpmn_lint.py` (元 `stride_lint.py validate_bpmn`) で全 14 / 9 項目を機械検証。違反は CI で error 扱い。

**Why Tecnos**: AI が「動けば OK」で完成宣言するのを防ぐ (literal-follow 強制)。

**OMG/Camunda 推奨**: Camunda Modeler の Linting は構文中心、Tecnos の MUST-DO ほど厳格ではない。

**他プロジェクトで採用しない場合**:
- `bpmn_lint.py` を CI に組み込まない選択肢は OK
- 部分採用なら、不要なチェックを `--skip-check <code>` (将来の拡張) でスキップ

---

## 3. Tecnos-STRIDE 固有の用語・参照を別プロジェクトに置換するチートシート

`rules/*.md` 内に以下の Tecnos-STRIDE 固有の用語が登場する。別プロジェクトで使う際は、対応する自プロジェクトの用語に読み替えるか、PORTABILITY.md (このファイル) を root の README に追記して周知する。

| Tecnos-STRIDE 固有用語 | 説明 | 別プロジェクトでの読み替え |
|----------------------|------|------------------------|
| `stride lint` | Tecnos の総合 lint コマンド | `python validators/bpmn_lint.py path/to/file.bpmn` |
| `stride init` | feature scaffold 生成 | `cp templates/process_bpmn_template.bpmn ...` |
| `agent_docs/sdd_bootstrap.md §4-BPMN` | Tecnos SDD の Phase Gate 規範 | 自プロジェクトの BPMN ガイドライン (なければこの README) |
| `manual/10_bpmn_guide.md` | Tecnos のエンドユーザーガイド | 自プロジェクトの README/Wiki |
| `basic_design.bpmn_descriptions` | Tecnos の Canonical YAML 第1正本 | 自プロジェクトの BPMN メタデータ管理方法 (任意) |
| `epic_design.epic_flow_descriptions` | EPIC 用の Canonical YAML | 同上 |
| `Phase 1 / Phase 2 / Gate 1 / Gate 2` | Tecnos SDD のフェーズ | 自プロジェクトのリリースフロー |
| `enterprise-erp / saas-integration / prototype` | Tecnos の profile (品質基準階層) | 自プロジェクトの品質基準 (採用任意) |
| `Camunda Cloud` | Camunda 8 SaaS のブランド名 | Camunda 8 (`executionPlatform="Camunda Cloud"` は SaaS/SM 共通の値、変更不要) |
| `FEATID / EPICID` | Tecnos 固有の機能/エピック ID | 自プロジェクトの命名 |

---

## 4. 「Tecnos override をどこまで採用するか」決定ツリー

```
質問: あなたのプロジェクトの BPMN は誰がレビューするか?
├── 開発者のみ (技術 review のみ)
│   └── → Universal 層のみで OK。Tecnos override 不要。
│         - layout は左→右でも OK
│         - lane 不要、ID 形式自由、documentation optional
│         - bpmn_lint.py は --no-tecnos-checks 相当の運用 (将来の拡張)
│
├── 開発者 + 業務担当者 (HITL review)
│   └── → ID 命名 + documentation は採用推奨
│         - layout / lane は好み
│         - bpmn_lint.py で documentation 警告を error に昇格させる手も
│
├── 開発者 + 業務担当者 + 顧客 (印刷物配布あり)
│   └── → 縦型 layout + pool/lane + documentation 全部採用推奨
│         - 完全な Tecnos override 採用が最適
│         - bpmn_lint.py 全 14 MUST-DO 適用
│
└── AI agent に書かせる (literal-follow 強制したい)
    └── → 全 Tecnos override 採用が最適 (AI が迷わない)
          - rules/bpmn_quick_reference.md を毎回参照させる
          - bpmn_lint.py で PASS まで自動修正させる
```

---

## 5. 移植時のチェックリスト

別プロジェクトに `bpmn/` フォルダをコピーした後の確認:

- [ ] `bpmn/README.md` 内の "Tecnos-STRIDE" 言及箇所を、自プロジェクト名に読み替え (任意)
- [ ] `bpmn/rules/bpmn_generator_rules.md` の §24 を読み、採用しない override は記憶しておく
- [ ] `bpmn/templates/*.bpmn` の placeholder (`BPMN-PROC-XXX`, `XXX_feature_name` 等) を自プロジェクトに合わせて変更
- [ ] `python3 bpmn/validators/bpmn_lint.py bpmn/examples/process_bpmn_example.bpmn` を実行し、PASS することを確認
- [ ] CI に `bpmn_lint.py` を組み込む (オプション)
- [ ] チームに本 README + PORTABILITY.md を共有
- [ ] (任意) `bpmn/spec/camunda_bpmn_dictionary_complete.md` を AI agent の knowledge base に登録

---

## 6. 「動かす vs ドキュメント」の責務境界

このパッケージは **BPMN を「正しく書く」までを担保**する。**「書いた BPMN を Camunda で動かす」**には、別途以下が必要:

- Camunda 8 Cluster (SaaS or Self-Managed)
- Job Worker 実装 (Java SDK / TypeScript SDK / Go / Python)
- BPMN deploy (Camunda Modeler / `zbctl` / REST API)
- Operate / Tasklist / Optimize の運用

これらは本パッケージの範囲外。Camunda 公式ドキュメント (https://docs.camunda.io/) を参照のこと。

---

> このファイルは Tecnos-STRIDE BPMN Authoring Pack v1.0.0 の portability guide。bpmn フォルダごと別プロジェクトにコピーしても、このガイドが付いてくるので採用判断に困らない。
