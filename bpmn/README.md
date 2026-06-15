# BPMN 2.0 Authoring Pack — Self-Contained, Portable

> **Camunda 8 (Zeebe 8.8 / 8.9 spec) 対応の BPMN 2.0 作成ルール + 辞書 + テンプレート + 検証ツール の単独運用パッケージ。**
> このフォルダだけを別プロジェクトにコピーすれば、BPMN 作成 → 検証まで完結する。

**Version**: 1.0.0
**Spec baseline**: Camunda 8 (8.8 runtime / 8.9 spec aligned)
**Origin**: Tecnos-STRIDE v5.4.0 ([Tecnos override 含む](PORTABILITY.md))

---

## 🎯 このフォルダで何ができるか

1. **BPMN 2.0 を Camunda 8 に正しく書ける** — 全要素 (Tasks / Gateways / Events / Subprocesses / Multi-Instance / Compensation / Ad-Hoc) のルールと XML スニペット完備
2. **顧客レビューに耐える品質** — 縦型フロー / pool-lane / `bpmn:documentation` 第2正本 など、HITL レビュー前提の Tecnos override ルールを同梱 (任意適用)
3. **AI agent (Claude Code, Codex, etc.) に literal-follow させる** — 1-page checklist (`rules/bpmn_quick_reference.md`) + 全要素辞書 (`spec/camunda_bpmn_dictionary_complete.md`) で「迷わない」設計
4. **CI/local で機械検証** — `validators/bpmn_lint.py` (stdlib のみ) で 14 MUST-DO (FEAT) + 9 MUST-DO (EPIC) を即時検証
5. **テンプレートからゼロ立ち上げ** — `templates/process_bpmn_template.bpmn` (FEAT) / `templates/epic_flow_template.bpmn` (EPIC) をコピーして placeholder 置換

---

## 📁 フォルダ構造

```
bpmn/
├── README.md                              # このファイル
├── PORTABILITY.md                         # Tecnos override の内訳 + 移植ガイド (必読)
├── CHANGELOG.md                           # バージョン履歴
├── VERSION                                # 現在バージョン (1.0.0)
│
├── rules/                                 # 適用ルール (literal-follow 用)
│   ├── bpmn_quick_reference.md            #   1-page MUST-DO checklist (毎回最初に参照)
│   ├── bpmn_generator_rules.md            #   全仕様 (24 セクション、Tecnos override 含む)
│   └── camunda_bpmn_practice_guide.md     #   Standard / Advanced / Deferred 区分の実装パターン
│
├── spec/                                  # OMG + Camunda spec 辞書 (深堀り用)
│   └── camunda_bpmn_dictionary_complete.md  #   2744 行 / OMG BPMN 2.0 + Camunda 8.9 全要素
│
├── templates/                             # 開始テンプレート (ゼロから書かない)
│   ├── process_bpmn_template.bpmn         #   FEAT 用 (executable BPMN)
│   └── epic_flow_template.bpmn            #   EPIC 用 (collaboration + multi-pool overview)
│
├── examples/                              # 実装例 (動作するサンプル)
│   ├── README.md                          #   各 example の説明
│   ├── process_bpmn_example.bpmn          #   基本 FEAT サンプル (受注処理)
│   └── process_bpmn_advanced_example.bpmn #   Advanced (boundary timer / DMN / call activity / error end)
│
└── validators/                            # 機械検証ツール (stdlib のみ依存)
    ├── README.md                          #   使い方
    ├── requirements.txt                   #   依存なし (Python 3.7+ stdlib のみ)
    └── bpmn_lint.py                       #   FEAT 14 MUST-DO + EPIC 9 MUST-DO 検証 CLI
```

---

## 🚀 Quick Start

### A. 新規 BPMN を作る (FEAT process.bpmn)

```bash
# 1. テンプレートをコピー
cp bpmn/templates/process_bpmn_template.bpmn path/to/your-project/process.bpmn

# 2. Camunda Modeler で開いて placeholder ({{プロセス名}}, BPMN-PROC-XXX 等) を置換しつつ作成

# 3. 検証
python3 bpmn/validators/bpmn_lint.py path/to/your-project/process.bpmn
```

検証出力例:
```
BPMN Lint Report (FEAT)
============================================================
PASS: 0 errors, 0 warnings
```

### B. 新規 BPMN を作る (EPIC epic_flow.bpmn)

```bash
cp bpmn/templates/epic_flow_template.bpmn path/to/your-project/epic_flow.bpmn
# placeholder (EPIC-XXX, {{Participant A Name}} 等) を置換
python3 bpmn/validators/bpmn_lint.py path/to/your-project/epic_flow.bpmn
# auto-detect で EPIC モード判定 (2+ participant)
```

### C. AI に BPMN を書かせる

AI agent (Claude Code / Codex / Gemini etc.) に対して、以下の順で参照を渡す:

1. `rules/bpmn_quick_reference.md` — 1-page checklist (FEAT 14 / EPIC 9 MUST-DO)
2. `templates/process_bpmn_template.bpmn` or `epic_flow_template.bpmn` — 開始点
3. `rules/bpmn_generator_rules.md` — 詳細仕様 (§24 で Tecnos override が universal vs Tecnos-specific を明示)
4. `spec/camunda_bpmn_dictionary_complete.md` — 深堀り (要素詳細、OMG 実行セマンティクス)
5. `examples/*.bpmn` — 動作サンプル

AI 用 prompt 雛形:
```
以下のルールに従って Camunda 8 process.bpmn を作成してください:
- @bpmn/rules/bpmn_quick_reference.md (FEAT 14 MUST-DO)
- @bpmn/templates/process_bpmn_template.bpmn (開始テンプレート)
作成後、@bpmn/validators/bpmn_lint.py で検証して PASS まで修正してください。
```

---

## 🔍 何が "BPMN 2.0 + Camunda 8" の universal で、何が "Tecnos override" か

このパッケージは **2 層構造**:

### 層 1: Universal (どこでも適用、変更不要)
- BPMN 2.0 / OMG 仕様の構文と接続ルール
- Camunda 8 (Zeebe 8.8/8.9) の実装サポート範囲
- `zeebe:taskDefinition` / `zeebe:userTask` / `zeebe:subscription` などの拡張
- FEEL 式の文法、ISO-8601 タイマー
- Token-based 実行セマンティクス

### 層 2: Tecnos override (Tecnos-STRIDE 固有、別プロジェクトでは適用判断)
- 縦型 (top-to-bottom) layout (OMG 推奨は left-to-right)
- Pool/Lane 強制 (OMG 推奨は "avoiding lanes")
- `BPMN-PROC-XXX` / `BPMN-TASK-NNN` ID 命名 (FEAT) / `Process_A` / `Task_A_Send` (EPIC)
- FEAT (executable) と EPIC (overview) の二重構造
- `bpmn:documentation` を第2正本として必須化
- 14 MUST-DO (FEAT) / 9 MUST-DO (EPIC) の網羅検証

→ **詳細は [PORTABILITY.md](PORTABILITY.md) 参照**。Tecnos override を全部適用するか、一部のみ採用するか、別プロジェクトのコンテキストで判断できる。

---

## 🛠️ 検証ツールの能力

`validators/bpmn_lint.py` は以下を **Python 3.7+ stdlib のみ** で検証する (PyPI 依存なし):

### FEAT (process.bpmn) — 14 MUST-DO
1. namespace (`bpmn`, `bpmndi`, `dc`, `di`, `xsi`, `zeebe`, `modeler`)
2. `modeler:executionPlatform="Camunda Cloud"` + `executionPlatformVersion="8.x"` (8.8/8.9 推奨)
3. `<bpmn:process isExecutable="true">`
4. 全 flow node に `<bpmn:incoming>` / `<bpmn:outgoing>` (start/end の例外あり)
5. `<bpmn:serviceTask>` は `<zeebe:taskDefinition type="...">`
6. `<bpmn:exclusiveGateway>` (2+ outgoing) は `default` 属性 OR 全 outgoing に conditionExpression
7. `<bpmn:conditionExpression>` は `xsi:type="bpmn:tFormalExpression"` + `=` で開始する FEEL
8. `<bpmn:sequenceFlow>` の sourceRef/targetRef は実在 node ID
9. `<bpmn:boundaryEvent>` は `attachedToRef` を持つ
10. `<bpmn:timeDuration>` は ISO-8601
11. `<bpmndi:BPMNDiagram>` → `<bpmndi:BPMNPlane>` を持つ
12. 全 flow node に `<bpmndi:BPMNShape>`、全 sequenceFlow に `<bpmndi:BPMNEdge>`
13. participant shape は `isHorizontal="false"` (vertical swimlane)  ← Tecnos override
14. process / userTask / serviceTask / 条件付き gateway / 条件付き sequenceFlow に `<bpmn:documentation>` (warning)  ← Tecnos override

### EPIC (epic_flow.bpmn) — 9 MUST-DO
1. `<bpmn:collaboration>` 必須
2. `<bpmn:participant>` ≥ 2
3. 各 participant の `processRef` が実在
4. 各 process 内の flow node に `incoming/outgoing`
5. sequenceFlow の sourceRef/targetRef が process 内に実在
6. messageFlow の構造 (オプション + warning)
7. BPMNPlane が collaboration を参照
8. participant shape は `isHorizontal="false"` (vertical swimlane)  ← Tecnos override
9. 全 flow node に BPMNShape、全 sequenceFlow/messageFlow に BPMNEdge

### Placeholder check (両モード)
- `{{...}}`、`BPMN-PROC-XXX`、`EPIC-XXX` などの未置換 placeholder を warning 検出

---

## 🤝 別プロジェクトでの採用パターン

### パターン 1: 全部そのまま使う (Tecnos-STRIDE と同等の品質を目指す)
```bash
cp -r bpmn/ /path/to/your-project/
```
全ルールが適用される。`bpmn_lint.py` を CI に組み込めば、PR 時に自動検証。

### パターン 2: Universal 層だけ使う (Tecnos override は採用しない)
```bash
cp -r bpmn/spec/ bpmn/templates/ bpmn/examples/ /path/to/your-project/bpmn/
# rules/ は採用せず、bpmn_lint.py の警告を選択的に suppress
python3 bpmn_lint.py --no-tecnos-override your-process.bpmn  # 将来の拡張オプション (現在は手動編集)
```

### パターン 3: AI agent に knowledge base として食わせる
- `spec/camunda_bpmn_dictionary_complete.md` を AI の知識ベースに登録 (例: ByteRover, Cursor rules, Copilot custom instructions)
- `rules/bpmn_quick_reference.md` を毎ターン system prompt に含める

---

## 📜 ライセンス・帰属

- BPMN 2.0 仕様: OMG (Object Management Group) — 公開仕様、自由参照可
- Camunda 8 / Zeebe / Camunda Modeler: Camunda Services GmbH — fair-use, spec reference のみ
- Tecnos-STRIDE override ルール: Tecnos Japan Inc. — 本パッケージ内で公開、自由採用可

---

## 🔗 関連リソース

- Tecnos-STRIDE 本体: 上位ディレクトリ参照 (このパッケージは Tecnos-STRIDE v5.4.0 から派生)
- Camunda 8 公式ドキュメント: https://docs.camunda.io/
- BPMN 2.0 仕様: https://www.omg.org/spec/BPMN/2.0/
- Camunda Modeler: https://camunda.com/download/modeler/

---

> Tecnos-STRIDE BPMN Authoring Pack v1.0.0 — 2026-05-07
