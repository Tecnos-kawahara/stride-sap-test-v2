# Upstream Bridge ガイド — Phase 0 → Phase 1 自動接続

> Version: v6.0.0-tecnos-stride-value (Phase C, FEAT-VALC01) / Last reviewed: 2026-04-29

## 1. 何のためのコマンドか

`stride upstream-bridge` は、Discovery / Elicit / Context Modelling (Phase 0 / 0.3 / 0.5) で
作成した **BACCM 6 軸 / stakeholder map / value canvas / business_usecase 等の YAML 成果物**
を、Phase 1 (Design) の `basic_design.md` に **手作業を介さず接続する** ための CLI です。

VALUE Upstream Extension Phase A (schema 基盤) と Phase B (CLI scaffold) によって、Discovery
側で機械可読な成果物が揃うようになりました。しかし、それを Phase 1 の Design に「翻訳」する
段階で、人間が手作業で `links` を埋めたり BPMN Task を一から考えたりすると、必ず **翻訳ロス
(認識齟齬・記入漏れ)** が発生します。Phase C で導入された本ツールは、その橋渡しを 1 コマンド
で行うことで、Phase 1 の出発点を確実に Phase 0 の到達点と一致させます。

## 2. 使い方

### 2.1 Dry-run (推奨初手)

```bash
stride upstream-bridge <feature> --target phase1
```

何も書き換えず、以下を **stdout に Markdown で出力** します:

- **populate 計画**: `basic_design.md` の `links` に追加されるべき `upstream_dir_ref` /
  `upstream_policy_ref` / `baccm_completeness_ref` の予定値
- **BPMN Task 候補**: `business_usecase.yaml` の use case id ベースで生成された
  `BPMN-TASK-001` 〜の候補リスト

最初は dry-run で内容を確認し、納得してから `--apply` に進むことを強く推奨します。

### 2.2 --apply (実書込)

```bash
stride upstream-bridge <feature> --apply
```

**書き込まれるのは `basic_design.md` の `links` 領域だけ** です。具体的には:

- `links.upstream_dir_ref` (specs/<feature>/upstream/ への参照)
- `links.upstream_policy_ref` (shared/policies/upstream_policy.yaml)
- `links.baccm_completeness_ref` (shared/policies/baccm_completeness.yaml)

既に存在するキーは **skip + warn** され、上書きされません (冪等性)。`process.bpmn` /
`implementation-details/*` には一切書き込まれません。

### 2.3 Phase 1 Immutability (重要)

`--apply` は **Gate 1 / Gate 2 が承認済みの feature に対しては実行できません**。これは
Phase 1 完了後の `basic_design.md` を AI が勝手に書き換えることを防ぐための安全装置です。

具体的には、`specs/<feature>/APPROVAL.md` の `## Gate 1: Basic Design` と
`## Gate 2: BPMN` セクションの両方が以下の条件を **同時に** 満たす場合、`--apply` は exit 1
で停止します:

1. すべてのチェックボックスが `[x]` (`- [ ]` が 1 つも残っていない)
2. 少なくとも 1 つの `[x]` が存在する (空セクション保護)
3. 承認者欄が placeholder (`_____`) ではなく実名で埋まっている

承認済み feature を再 populate する場合は、change_log を作成し Gate 1/2 を再承認してから
実行してください。あるいは dry-run で populate 計画のみを確認するに留めるのが安全です。

## 3. BPMN Task 候補のレビュー

`business_usecase.yaml` の `use_cases` 配列をスキャンし、各 use case を `BPMN-TASK-NNN`
候補として **stdout に Markdown で出力** します。

```markdown
## BPMN Task Candidates (FEAT-XXX)

| Suggested BPMN ID | Task Name | Source |
|---|---|---|
| BPMN-TASK-001 | Submit purchase request | business_usecase.yaml |
| BPMN-TASK-002 | Approve purchase order | business_usecase.yaml |
```

これは **参考情報** であり、`process.bpmn` 自体は変更されません。実際の BPMN 編集は Gate 2
承認前に **人間 (Tech Lead / Architect)** が行ってください。Camunda 8 (Zeebe) 互換の正本
として `process.bpmn` を作る責任は人間に残ります。

## 4. ベストプラクティス

### 4.1 タイミング

- Phase 0 (Discovery) と Phase 0.5 (Context Modelling) の `stride upstream init` /
  `stride upstream validate` が PASS した直後に dry-run
- Phase 1 (Design) の Gate 1, 2 承認 **前** に `--apply` を 1 度だけ実行
- 承認済みになったら、以降の populate 変更は新 amendment / change_log で対応

### 4.2 欠損成果物の扱い

`upstream/phase_0_*/` 配下の YAML が一部欠損していても、`stride upstream-bridge` は
**WARNING を返し exit 0 で graceful continue** します。BLOCKER にはなりません。これは
Discovery が iteration を経て段階的に充実していく現実に合わせた設計です。

ただし、本格的な Phase 1 着手の前には Article XV (BACCM Completeness Gate) の機械検証
(`stride upstream validate`) で 6 軸全 PASS を達成しておくことを推奨します。

### 4.3 既存値保護

同じ `--apply` を 2 回実行しても、2 回目は skip + warn のみで何も変更されません (冪等)。
これは「途中までは bridge で populate 済み、残りを手書きで補強した」状態を上書きしないため
の保護です。

## 5. コマンドリファレンス

```
Usage: stride upstream-bridge <feature> [--target phase1] [--apply]

Default:  dry-run (populate 計画 + BPMN Task 候補を Markdown で stdout 出力、書き換えなし)
--apply:  basic_design.md links のみに実書込
          ⚠ process.bpmn は変更しない (BPMN は人間責務)
          ⚠ implementation-details/* には何も書かない (Phase 2 領域)
          ⚠ Gate 1/2 が未承認 feature にのみ許可 (Phase 1 immutability)
Task candidates は両モードで stdout に出力される。

Exit code: 0 = OK, 1 = upstream/ 不在 or Gate 1/2 承認済 violation, 2 = ERROR
```

## 6. 関連 Constitution Article

- **Article XV (BACCM Completeness Gate)**: `stride upstream-bridge` の前提となる Phase 0
  完成度ゲート。`baccm_completeness_ref` リンクの populate でこのゲートへの参照が basic
  design 側からも辿れるようになります。
- **Article XVI (Layered Requirement Architecture / 4-layer aligned)**: Phase 0.5 の
  4-layer Requirements Architecture構造を Phase 1 設計に橋渡しします。

## 7. Attribution

- BABOK v3 (IIBA), KA7 framework backbone — fair-use, names and section refs only
- Layered Requirements Modeling ((concept reference, no proprietary brand)), 4-layer structural integrity — fair-use, layer names only
- value-driven discovery (philosophical foundation), philosophical inspiration — fair-use, model names only
