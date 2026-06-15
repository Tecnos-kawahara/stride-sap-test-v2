# Appendix C. Fourteen Articles（十四条）要約

---

## この付録について

この付録は、現行の Tecnos-STRIDE constitution に定義された **Fourteen Articles** を
manual 向けに要約したものです。

- **正本**: `memory/constitution.md`
- **用途**: 何を守るべきかを素早く確認するための要約
- **注意**: 正規表現、Gate 条件、厳密なルール本文は必ず constitution を参照

---

## Fourteen Articles とは

Tecnos-STRIDE の原則は、現在 **14条** です。

- **Article I〜IX**: SDD の基本原則
- **Article X〜XII**: Enterprise / マルチチーム拡張
- **Article XIII〜XIV**: STRIDE 運用拡張

旧来の「Nine Articles」は、現在では **Fourteen Articles の前半 9 条** を指す歴史的な呼び方です。  
manual と運用では、以後 **Fourteen Articles** を基準に扱います。

---

## 初心者向けの読み順

1. **I〜IV**: まず「何を一次成果物にするか」を理解する
2. **V〜IX**: 品質を落とさない実装原則を押さえる
3. **X〜XII**: Enterprise / マルチチーム案件で追加ルールを適用する
4. **XIII〜XIV**: STRIDE 運用と AI 権限分離を確認する

---

## 原則一覧

| Article | 名前 | 要点 | まず確認する場所 |
|---------|------|------|------------------|
| I | Library-First | ビジネスロジックを library 境界に集約する | `plan.md`, `spec.md` |
| II | Contract/CLI-First | API/CLI/EVT/FILE などの契約を実装前に定義する | `contracts/`, `plan.md` |
| III | Test-First | AC/CT から先にテストを定義する | `spec.md`, `plan.md`, `tests/` |
| IV | Documentation-First | 仕様・計画・タスクをコード変更より先に更新する | `basic_design.md`, `spec.md`, `plan.md`, `tasks.md` |
| V | Modularity | 境界を越えるのは契約だけにする | `plan.md`, `contracts/` |
| VI | Automation | lint / counts / coverage / evidence を自動化する | `stride lint`, CI |
| VII | Simplicity | 必要性が証明されるまで増やさない | `plan.md`, `DR-*` |
| VIII | Anti-Abstraction | 不要なラッパーや重複モデルを作らない | `plan.md`, `src/` |
| IX | Integration-First | 実環境に近い統合テストを優先する | `tests/integration`, `tests/e2e` |
| X | Epic-Feature Hierarchy | 2チーム以上の機能は Epic/Feature 階層で管理する | `epics/`, `specs/` |
| XI | Shared Contract Governance | 共有契約にオーナーと消費者合意を持たせる | `shared/contracts/`, CCP |
| XII | Tiered Coverage | critical / standard / experimental で要求水準を変える | `basic_design.md`, policy |
| XIII | PM Progress Visibility | Epic / WI / team の進捗を見える化する | `EPIC_PROGRESS_REPORT.md`, `PM_DASHBOARD.md` |
| XIV | Execution Authority Separation | AI の権限境界を明示し、承認権限を分離する | `mode_policy.yaml`, `tasks.md` |

---

## 各 Article の短い説明

### I. Library-First

- UI やアプリ層ではなく、library 境界にビジネスロジックを集約する
- 主要概念が `library` / `component` と対応しているかを確認する

### II. Contract/CLI-First

- API/CLI/EVT/FILE/BATCH/EDI/IDOC を実装より先に定義する
- `CT-*` と `TS-CON-*` の対応が取れていることを求める

### III. Test-First

- AC は必ずテストにトレースされる
- `integration` / `e2e` タグ付き AC は、対応するテスト種別で先に担保する

### IV. Documentation-First

- コードより先に `basic_design.md` / `spec.md` / `plan.md` / `tasks.md` を更新する
- Gate が通っていない段階で実装だけ先行させない

### V. Modularity

- 境界を越えるやり取りは契約に限定する
- ERP 本体 DB 直結のような境界破りは原則禁止

### VI. Automation

- `stride lint`、coverage、counts、Evidence Pack を自動化する
- 手計算の counts を残さず、CI で再現可能な状態にする

### VII. Simplicity

- 最小構成から始め、将来のためだけの抽象化を避ける
- 例外は DR/Exceptions に明示して残す

### VIII. Anti-Abstraction

- 不要なラッパーや duplicate model を作らない
- framework が提供する構造を素直に使う

### IX. Integration-First

- 単体テスト偏重ではなく、契約テストと統合テストを優先する
- E2E は重要なユーザージャーニーに限定する

### X. Epic-Feature Hierarchy

- 2チーム以上にまたがる機能は Epic 化する
- 各 Feature は 1 つの team に Ownership を持つ
- `stride epic validate` と `stride lint specs/<feature>/ --enterprise`（必要に応じて `stride lint --all --enterprise`）で整合性を検証する

### XI. Shared Contract Governance

- 共有契約にはオーナーチームと消費者登録を持たせる
- Breaking Change は CCP を作成し、消費者合意を取る

### XII. Tiered Coverage

- `critical`: AC 100%, CT 100%, E2E 必須
- `standard`: AC 100%, CT 80%, E2E 任意
- `experimental`: 要求水準を下げるが、理由を明示する

### XIII. PM Progress Visibility

- Epic / team / WI / gate の進捗を PM が追える状態を維持する
- `stride epic progress <EPIC_ID>` は標準ではサマリ表示
- レポート生成が必要なら `--format markdown --output <path>` を付ける

### XIV. Execution Authority Separation

- AI の権限スコープを宣言し、承認権限と分離する
- AI は Responsible になれても、Accountable にはなれない

---

## 実務チェックリスト

### Feature 単位

- [ ] `basic_design.md` に Canonical YAML がある
- [ ] `spec.md` に AC が揃っている
- [ ] `plan.md` に CT / TS / coverage_policy がある
- [ ] `tasks.md` に実行単位と DoD がある
- [ ] `stride lint specs/<feature>/` が通る

### Enterprise / マルチチーム案件

- [ ] `sdd-templates/config/enterprise.yaml` で `enterprise.enabled: true`
- [ ] `epics/<EPIC_ID>/` が存在し、`stride epic validate <EPIC_ID>` が通る
- [ ] 各 Feature に `epic_ref` / `team_id` / `coverage_tier` がある
- [ ] `shared/contracts/CONTRACT_REGISTRY.yaml` を管理している
- [ ] `stride lint --all --enterprise` を CI に組み込んでいる

### STRIDE 運用

- [ ] `EPIC_PROGRESS_REPORT.md` / `PM_DASHBOARD.md` を更新している
- [ ] WI / Run / Mode が state と一致している
- [ ] `execution_authority` と `mode` が矛盾していない

---

## CCP（Contract Change Proposal）の現行フロー

```text
1. 契約オーナーが CCP を起票
2. stride lint specs/<feature>/ --enterprise または stride lint --all --enterprise と dependency_checker で影響範囲を確認
3. 消費者チームへ通知し、移行方針を合意
4. ARCH_BOARD / 必要承認者が最終承認
5. 新バージョンを実装し、契約テストを更新
6. 消費者移行完了後に旧版を廃止
```

`stride lint specs/<feature>/ --enterprise` / `stride lint --all --enterprise` は影響分析ドキュメントを自動生成するツールではありません。  
lint 結果と依存情報を使って、**人間が移行判断できる状態にする**のが現行運用です。

---

## 迷ったときの優先順位

1. `memory/constitution.md` を正本として確認する
2. `agent_docs/commands.md` のコマンド正本を見る
3. Enterprise 案件なら `manual/04_enterprise_guide.md` を参照する
4. 実行前に `stride lint` / `stride epic validate` で機械検証する

---

> SDD Templates Manual - Appendix C. Fourteen Articles Summary
