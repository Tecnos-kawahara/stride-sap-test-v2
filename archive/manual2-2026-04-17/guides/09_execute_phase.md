# Phase 3-5: 実行

> **対象**: 実装者 / AI と協働する開発者 / レビュー担当
> **所要時間**: 20分
> **前提**: [08_specify_phase.md](08_specify_phase.md) を読んでいること
> **In scope**: `tasks.md`、Work Item、Run、`evidence_pack.md` を中心にした実行の進め方
> **Out of scope**: GitHub Projects の詳細設定、CI ベンダー別設定、各テストフレームワークの詳細

---

## このフェーズの目的

Execute フェーズの目的は、**承認済みの仕様を安全に実装し、テストし、証跡を残して完了へ持ち込むこと**です。

ここでは次の成果物や単位が重要になります。

- `tasks.md`
- Work Item（WI）
- Run
- `implementation-details/evidence_pack.md`

---

## `tasks.md` は何のためにあるか

`tasks.md` は、仕様を実行単位へ分解する文書です。  
ToDo リストではなく、**どの順で何を進めると安全かを示す実行計画**と考えてください。

良い `tasks.md` は次を満たします。

- タスク粒度が大きすぎない
- 依存関係が見える
- 高リスク作業が埋もれない
- テストや証跡作業が抜けていない

---

## Work Item と Run

> **注: Work Item**  
> 実際に着手・追跡する作業単位です。`WI-*` という ID で扱います。

> **注: Run**  
> Work Item を 1 回実行した記録単位です。  
> 実装、テスト、レビュー結果、気づきなどを残す器と考えると理解しやすいです。

Work Item は「何をやるか」、Run は「その作業を今回どう進めたか」です。  
この区別があることで、途中中断や再開、複数回の試行を追いやすくなります。

---

## 実行の基本フロー

1. `tasks.md` から対象 WI を決める
2. リスクに応じて Mode を確認する
3. 実装とテストを進める
4. walkthrough や test_results を整理する
5. `evidence_pack.md` に必要な証跡を揃える
6. Final に向けて `pr-check` を通す

---

## リスクに応じた進め方

リスクが低い実装は AI が比較的自律的に進められます。  
一方で、ERP、権限、セキュリティ、共有契約に関わる変更は、人間の確認密度を上げるべきです。

迷ったときは、次の順で考えてください。

1. この変更は業務や監査に効くか
2. 他 feature や外部システムへ波及するか
3. 失敗時に巻き戻しや説明が難しいか

1 つでも重いなら、軽率に `autopilot` 扱いにしない方が安全です。

---

## `evidence_pack.md` の役割

`evidence_pack.md` は、完了の根拠を残す文書です。  
「テストは通りました」だけでなく、何を確認し、何が残課題で、何をもって完了としたのかを追えるようにします。

主に次のような内容を扱います。

- 実施したテスト
- 結果サマリ
- 必要なログやレポート
- セキュリティや静的解析の結果
- AI の実行履歴や判断材料

---

## 実装者が最低限見るコマンド

```bash
# 整合性確認
sdd-templates/bin/stride lint specs/<feature>/

# Gate 状態確認
sdd-templates/bin/stride phase-status specs/<feature>/

# 次の実行候補
sdd-templates/bin/stride auto-continue specs/<feature>/

# PR 前の総合チェック
sdd-templates/bin/stride pr-check .
```

---

## よくある失敗

### タスク分解が粗すぎる

1 つの WI に実装、テスト、修正、レビューを全部詰め込むと、進捗もリスクも見えません。

### テストをタスクに含めていない

実装タスクだけが並んでいると、最後にテストがまとめて残ります。

### 証跡を最後に集めようとする

証跡は、作業の最後に思い出して集めると抜けやすいです。  
Run ごとに整理する方が安定します。

---

## 補助資料

- WI/Run の詳細運用: `sdd-templates/docs/wi-management-guide.md`
- テスト戦略: [10_testing.md](10_testing.md)
- 品質ゲート: [11_quality_gates.md](11_quality_gates.md)

---

## 次に読むべきもの

- テスト戦略を確認する: [10_testing.md](10_testing.md)
- 品質ゲートを確認する: [11_quality_gates.md](11_quality_gates.md)
- 付録のチュートリアルで流れを追う: [../appendix/19_tutorial_web_edi.md](../appendix/19_tutorial_web_edi.md)
