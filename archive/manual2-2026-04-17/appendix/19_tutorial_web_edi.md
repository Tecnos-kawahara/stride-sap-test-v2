# Web-EDI チュートリアル

> **対象**: 初学者 / これから一連の流れを体験したい人
> **所要時間**: 45分
> **前提**: [../01_quickstart.md](../01_quickstart.md) を読んでいること
> **In scope**: 1 つの feature を Design から Final まで追う学習用の流れ
> **Out of scope**: ERP 実務運用の細かなルール、Enterprise 横断管理

---

## このチュートリアルの目的

ここでは、Web-EDI の受注受付 feature を例にして、Tecnos-STRIDE の一連の流れを体験します。  
学習用の一本道として整理しているため、実案件の細かな分岐は一部省いています。

---

## Step 1. feature を準備する

まず feature を作ります。

```bash
sdd-templates/bin/stride intake web_edi_order
```

学習目的なら `init` でも構いませんが、このチュートリアルでは `intake` を推奨します。

---

## Step 2. `basic_design.md` を固める

まず次の点を言語化します。

- 受注受付で誰が困っているか
- 何をオンライン化したいか
- どこまでを今回の対象にするか

Design Phase では、完璧な仕様よりも、背景と範囲が明確なことが重要です。

---

## Step 3. `process.bpmn` を作る

受注入力、確認、登録、通知の流れを図にします。  
例外ケースがあるなら、この時点で見えるようにします。

---

## Step 4. Gate 1・2 を確認する

次を見てから承認します。

- 基本設計の目的と対象範囲に無理がないか
- BPMN が実業務と大きくずれていないか

---

## Step 5. `spec.md` と `plan.md` を作る

ここで、次を具体化します。

- 利用者が何をできるべきか
- 何をもって完了とみなすか
- どのテストで確かめるか
- 外部連携や契約は何か

---

## Step 6. Gate 3・4 を確認する

- AC が十分か
- テスト戦略に無理がないか
- 契約が足りているか

---

## Step 7. `tasks.md` へ分解する

設計と仕様が固まったら、実施単位へ落とします。  
UI、API、バリデーション、通知、テストなどを、実行しやすい粒度に分けます。

---

## Step 8. Gate 5 を確認する

- タスク粒度が適切か
- 高リスク作業が埋もれていないか
- テストと証跡がタスクに含まれているか

---

## Step 9. 実装と検証を進める

実装、テスト、証跡整理を進めます。  
途中で何度か `stride lint` を実行し、整合性を保ちます。

```bash
sdd-templates/bin/stride lint specs/web_edi_order/
sdd-templates/bin/stride pr-check .
```

---

## Step 10. Final 承認へ進む

最後に次を確認します。

- テスト結果が揃っている
- Evidence Pack に根拠が残っている
- PR 前チェックが通っている

これで、学習用の一連の流れをひととおり体験できます。

---

## 次に読むべきもの

- 実務運用へ広げる: [../guides/09_execute_phase.md](../guides/09_execute_phase.md)
- ERP 実務へ寄せる: [20_erp_addon_playbook.md](20_erp_addon_playbook.md)
- 旧チュートリアル詳細: `manual/08_web_edi_tutorial.md`
