# SDD Template Pack Evaluation Report: v1.2.0-tecnos

## 1. Executive Summary

Technos Japan 社向けにカスタマイズされた **v1.2.0-tecnos** テンプレートパックを検証しました。
結論として、本バージョンはベースとなる **v1.2.0** の堅牢な構造（Canonical YAML / Gate / Camunda 8 BPMN）を維持しつつ、**エンタープライズERP導入（SAP/mcframe/Salesforce）** および **CBP / AgentOps** の実務要件を的確に反映した **「即戦力」な構成** になっています。

特に、**統合・監査・運用要件（Integration/Audit/Ops）** が構造レベルで組み込まれており、プロジェクト個別の品質バラつきを防ぐガードレールとして非常に機能的です。

---

## 2. Detailed Validation & Comparison (v1.2.0 vs v1.2.0-tecnos)

ベースの v1.2.0 と、Tecnos版 v1.2.0-tecnos の主要な差異と、その意図を分析しました。

### 2.1 Constitution & ID Conventions（憲法・規約）

| 項目 | v1.2.0 (Base) | v1.2.0-tecnos (Tecnos Edition) | 評価 |
|---|---|---|---|
| **Contract ID** | `CT-(API|CLI|EVT)-NN` | `CT-(API|...|FILE|BATCH|EDI|IDOC)-NN` | **[Merkmal]** ERP連携の実態（ファイル/IDoc）にお茶を濁さず、正規の管理対象としてIDを与えた点は非常に重要。 |
| **Article II** | Contract/CLI First | + **FILE/BATCH/EDI First** | 疎結合APIだけでなく、バッチ連携も「契約（入力/出力/再実行性）」として定義させる強制力が働く。 |
| **Article V** | Modularity | + **No Direct DB Access** | 「ERP本体DBへの直接書き込み」を憲法違反（原則禁止）として明文化し、ガバナンスを強化。 |
| **Gates** | Gate Check Only | + **BPMN Approval Gate** | BPMN承認を「次の工程（Spec/Plan）に進むための必須ゲート」として客観化し、手戻りを防止。 |

### 2.2 Basic Design Template（ハブ機能）

| 項目 | v1.2.0 (Base) | v1.2.0-tecnos (Tecnos Edition) | 評価 |
|---|---|---|---|
| **Context** | generic (who/what/why) | **Organization & Domain** | プロジェクトが「全社横断PJ」「CBP」「TEIM」のどこに位置するかを定義可能。 |
| **Org Constraints** | N/A | **Referenced (Mandatory)** | `memory/tecnos_org_constraints.md` の参照を必須化し、監査/統合ルールを強制。 |
| **Systems** | N/A | **System/Category/Owner** | SAP, mcframe, Salesforce などの対象システムと、連携モード（IDoc/API等）が選択式で定義済み。 |
| **Data Policy** | N/A | **PII / Audit / Retention** | データの機密性区分や監査ログ要件、保持期間を初期段階で定義させる構造。 |

### 2.3 Plan Template（実装計画）

| 項目 | v1.2.0 (Base) | v1.2.0-tecnos (Tecnos Edition) | 評価 |
|---|---|---|---|
| **Context** | Technical Context | **Tecnos Context (TEIM)** | デリバリー標準（TEIM 6x6）や対象ドメイン（CBP等）を明示できる。 |
| **Integration** | N/A | **Correlation / Idempotency** | 統合標準として「冪等性」「相関ID」「SoD」を必須項目化。品質事故を防ぐ。 |
| **Grouping** | Generic Phase/Group | **Security/Ops Group (Default)** | Phase-1 に `G-02-security-ops` がプリセットされ、非機能要件の実装漏れを防ぐ。 |

### 2.4 Governance Artifacts

| ファイル | 役割 | 評価 |
|---|---|---|
| **tecnos_org_constraints.md** | 組織制約（監査・SoD・禁止パターン） | 新設。プロジェクトごとにバラつきがちな「やってはいけないこと（DB直結など）」を一元管理できる。 |
| **constitution.md** (Modified) | 憲法（Tecnos Edition） | 改訂。Gate定義に `security_items` や `data_items` のカウントチェックを追加し、非機能要件の密度を担保。 |

---

## 3. Merits & Demerits

### 3.1 Merits (導入メリット)

1.  **「ERP連携の泥臭さ」を正規化できる**
    *   APIだけでなく、FILE/IDoc/BATCH を「契約」として扱うことで、ブラックボックス化しやすいレガシー連携を管理下に置けます。
2.  **監査・コンプライアンスの自動化**
    *   Basic Design 段階で PII や Audit Log 要件を選択させるため、後工程での「ログが出ていない」等の手戻りを防げます。
3.  **TEIM / CBP との整合性**
    *   Tecnos 独自のメソドロジー（TEIM / CBP）用語がテンプレートに埋め込まれており、現場メンバーが違和感なく導入できます。
4.  **AgentOps ガードレール**
    *   「人間の承認なしに本番実行しない」等のポリシーが YAML レベルで埋め込まれており、AI Agent を安全に活用する準備ができています。

### 3.2 Demerits & Risks (考慮点)

1.  **初期入力コストの増加**
    *   Basic Design の入力項目が増加（Systems, Data Policy 等）しているため、小規模なPoC案件では「重すぎる」と感じる可能性があります。
    *   *Mitigation: PoC用の `lightweight` バリアントを用意するか、必須項目以外を空欄（`[]`）とすることを許容する運用ルールでカバー可能。*
2.  **憲法の陳腐化リスク**
    *   `tecnos_org_constraints.md` が固定化されると、新しい技術（例：GraphQL, Event Mesh）導入の阻害要因になる可能性があります。
    *   *Mitigation: Constitution の "Amendment Process" を活用し、定期的な見直し（半年ごと等）をプロセスに組み込む。*

---

## 4. Conclusion & Recommendation

**v1.2.0-tecnos** は、Tecnos Japan のコアビジネスであるエンタープライズ・インテグレーションにおいて、**品質と効率を両立させるための強力な基盤** です。
単なるドキュメントテンプレートではなく、「何を考え、何を決めるべきか」という **思考プロセスそのものを標準化** しています。

### 推奨アクション
1.  **全社標準テンプレートとしての採用**:
    *   新規の SAP/mcframe/Salesforce 導入プロジェクトにおいて、本テンプレートの利用を推奨（または必須化）する。
2.  **Gate System の CI 導入**:
    *   `speckit-lint` をパイプラインに組み込み、Gate を通過しない仕様変更をマージさせない運用を徹底する。
3.  **教育**:
    *   リードエンジニア・アーキテクト向けに、特に「Contract-First (FILE/IDoc含む)」と「Basic Design Hub」の概念を教育する。

このテンプレートは、AI (Agent) と人間が協調して複雑なERP導入を進めるための、現時点で **Best Practice** と言える構成です。
