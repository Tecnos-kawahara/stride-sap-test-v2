---
artifact: "basic_design"
template_id: "TPL-BD-TECNOS-001"
feature_id: "FEAT-XXX"
basic_design_id: "BD-XXX"
title: "Basic Design - <Feature Name>"
version: "{{TEMPLATE_VERSION}}"
status: "draft" # draft | in_review | approved | released | deprecated
# --- yaml 出自追跡フィールド（SAP Extension: yaml → basic_design 転記元情報）---
project_id: ""                # fg.meta.projectId
function_group_id: ""         # fg.meta.groupId
function_group_name: ""       # fg.meta.groupName
feature_name: ""              # fs.meta.featureName（title とは別、yaml 上の機能名）
source_author: ""             # fg/fs.meta.author（yaml 作成者）
source_updated: ""            # fg/fs.meta.updated（yaml 最終更新日）
source_status: ""             # fg/fs.meta.status（yaml ステータス: draft/review/approved 等）
function_type: ""             # yaml.header.functionType（report / dialog / batch 等）
owners:
  - { name: "<Business Owner>", role: "Product Owner / Business" }
  - { name: "<Tech Lead>", role: "Tech Lead / Architect" }
  - { name: "<PMO>", role: "PMO (TEIM)" }
reviewers:
  - { name: "QA Lead", role: "Quality" }
  - { name: "Security Lead", role: "Security" }
  - { name: "ERP/Integration Lead", role: "ERP/Integration" }
links:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  artifact_registry_ref: "memory/artifact_registry.md"
  ai_policy_ref: "memory/tecnos_org_constraints.md#6.3"
  raci_plus_ref: "memory/tecnos_org_constraints.md#6.4"
  process_bpmn_ref: "specs/XXX_feature_name/process.bpmn"
  spec_md_ref: "specs/XXX_feature_name/spec.md"
  plan_md_ref: "specs/XXX_feature_name/plan.md"
  tasks_md_ref: "specs/XXX_feature_name/tasks.md"
  constitution_ref: "memory/constitution.md"
  # v6.0 Phase C: VALUE Upstream Extension references — populated by `stride upstream-bridge --apply`
  upstream_dir_ref: "specs/XXX_feature_name/upstream/"
  upstream_policy_ref: "shared/policies/upstream_policy.yaml"
  baccm_completeness_ref: "shared/policies/baccm_completeness.yaml"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> **Rule-0**: このドキュメントの正本は **#0 Canonical Basic Design (YAML)**。
>
> ## ドキュメント構造
> | セクション | 種別 | 編集方法 |
> |-----------|------|----------|
> | #0 YAML | **正本（SSoT）** | 直接編集可 |
> | #1 Executive Summary | AI生成ビュー | YAML変更後にAIが再生成 |
> | #2 Architecture | AI生成ビュー | YAML変更後にAIが再生成 |
> | #3 Data Model | AI生成ビュー | YAML変更後にAIが再生成 |
> | #4 Process Flow | AI生成ビュー | YAML変更後にAIが再生成 |
> | #5 Test Strategy | AI生成ビュー | YAML変更後にAIが再生成 |
> | #6 Risk & Mitigation | AI生成ビュー | YAML変更後にAIが再生成 |
> | #7 Checks | **ゲート状態** | 手動管理（AIは再生成しない） |
>
> ## 修正ワークフロー
> ```
> 1. #0 YAML セクションを編集
> 2. AIに「YAMLを更新したので、ビューを再生成して」と依頼
> 3. AI が #1～#6 を YAML に基づいて再生成
>    ⚠️ #7 Checks はゲート状態のため再生成しない
> 4. stride lint で検証
> ```
>
> ## 推奨ワークフロー（新規作成時）
> 1. `stride intake <feature>` で簡易入力フォームを作成
> 2. `basic_design_intake.md` を記入（10-15分）
> 3. AIに「この intake から basic_design.md を生成」と依頼
> 4. 生成された本ファイルをレビュー・承認
>
> **Purpose**: 人間の任意テキスト入力を、AIがSDD（BPMN→Spec/Plan/Tasks）へ落とす前に「認識齟齬」を潰すハブ。
> **Tecnos**: 統合・監査・運用・AgentOpsの最低要件は `{{ links.org_constraints_ref }}` を参照。
> **SAP Extension**: SAP ERP 開発向け完全版テンプレート。標準 v6.0.0 + SAP Extension Pack v2 をマージ済み。

# 0. Canonical Basic Design (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

policy_refs:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  artifact_registry_ref: "memory/artifact_registry.md"
  ai_policy_ref: "memory/tecnos_org_constraints.md#6.3"
  raci_plus_ref: "memory/tecnos_org_constraints.md#6.4"

derived_fields:
  counts_are_computed: true
  counts:
    traceability_rows: 0
    integration_flows: 0
    blocking_questions: 0

basic_design:
  # --- 固定値（SAP Extension Pack が一律設定する値）---
  profile: "enterprise-erp"       # SAP固定: enterprise-erp
  erp_integration: true            # SAP固定: true
  security_sensitive: true         # SAP固定: true

  # Enterprise Extension Fields (v1.2.6)
  # epic_ref: Epicに属する場合のみ設定（任意）
  # team_id: チーム割り当て（エンタープライズモード時は必須）
  # coverage_tier: critical | standard | experimental（デフォルト: standard）
  epic_ref: null              # 例: "EPIC-ORDER" - Epicに属する場合
  team_id: null               # 例: "TEAM-A" - チーム割り当て
  coverage_tier: "standard"   # critical | standard | experimental

  # NOTE: ed_cf_score は SAP ERP 開発では不使用のため削除済み
  # NOTE: autonomy_bias は yaml SSoT モデルにより AI 裁量が限定的なため削除済み

  # Escalation Flags (v1.2.6) - triggers additional approval requirements
  # These flags trigger escalation rules defined in approval_matrix.yaml:
  # - security_sensitive + critical tier → SECURITY_OFFICER
  # - erp_integration (any tier) → ARCH_BOARD
  # security_sensitive / erp_integration は上記固定値セクションで true 設定済み

  organization:
    company: "Tecnos Japan"
    strategy_alignment:
      mid_term_plan: "2027-2032"
      target_state: ""  # 例: "現状 → 目標状態"
    program_ref:
      portfolio_items: []   # 例: ["2-11", "2-21"]（全社横断PJ番号など）
    delivery_methods:
      - "TEIM"
      - "PMBOK"
      - "SAP Activate"
    ai_governance:
      guideline_ref: "AI Guidelines v6 (ISO/IEC 42001 series)"
      policy_ref: "memory/tecnos_org_constraints.md#6.3"
      human_in_the_loop: true
      provenance_required: true

  delivery_model:
    type: "requirements-driven"   # SAP固定: requirements-driven（SAP 仕様書 yaml 起源のため）
    source: "yaml_spec"           # SAP固定: yaml_spec（仕様書 yaml からの転記）
    version: "2.0.0"              # SAP Extension Pack バージョン
    rationale: "SAP 仕様書 yaml 起源のため"
    ftos_exit_criteria:
      enabled: false
      criteria:
        - ""
    ddd_policy:
      enabled: false
      activation_mode: "validate"  # autopilot | confirm | validate
      domain_model_ref: "specs/XXX_feature_name/implementation-details/domain_model.md"
      technical_design_ref: "specs/XXX_feature_name/implementation-details/technical_design.md"
      adr_index_ref: "shared/decisions/decision-index.md"

  # --- sap_context ---
  # 転記元: yaml.header + fg.sapContext + yaml.programDetail（v2: sap_context に統合）
  sap_context:
    program_type: ""          # report / rap_bo / interface / fugr / enhancement
    program_id: ""            # プログラム ID（例: ZSD_ORDER_EDIT）
    program_id_note: ""       # 命名規約等の補足（null 可）
    client: ""                # クライアント番号
    sid: ""                   # システム ID
    s4hana_version: ""        # S/4HANA バージョン
    package: ""               # 開発パッケージ
    namespace: ""             # ネームスペース（Z 等）
    transport_layer: ""       # 移送レイヤー
    landscape: {}             # dev/qas/prd（構造ごと転記）
    # v2: programDetail → sap_context に統合（SE38属性等）
    se38_attributes:          # yaml.programDetail.se38Attributes から転記
      type: ""                # 1 executable_program 等
      status: ""              # test / productive
      fixed_point_arithmetic: true
      unicode_check: true
    dev_objects:              # header.programType + programId から機械導出
      - type: ""              # PROG / CLAS / INTF / FUGR 等
        name: ""
        description: ""

  # --- raci_plus ---
  # v6.0.0 標準セクションを SAP 用に修正
  # 転記元: yaml.businessSpec.users.roles[]
  raci_plus:
    actors:
      - name: ""              # ロール名
        usage: ""             # 業務における利用方法
        scope: ""             # 権限スコープ

  context:
    who: ""     # 想定ユーザー/ステークホルダー（業務・IT・監査を含む）
    what: ""    # 何を実現するか（価値）
    why: ""     # なぜ今それが必要か（背景・課題）

  business_domain:
    value_chain: ""     # 例: O2C / P2P / M2O / R2R
    capability: ""      # 例: 調達DX / 生産DX / 営業DX / 原価管理
    domain_objects: []  # 例: ["Customer", "Vendor", "Material", "Order", "PurchaseOrder"]

  scope:
    # 転記元: yaml.businessSpec.overview + yaml.functionStructure.functions[]
    summary: ""                 # overview.summary — 機能の概要説明
    target_data: ""             # overview.targetData — 対象データ
    systemization_scope: ""     # overview.systemizationScope — システム化範囲
    in:
      - id: ""                  # functions[].id（例: ZSDR0010）
        name: ""                # functions[].name
        type: ""                # functions[].type（report / dialog / batch 等）
        execution_mode: ""      # functions[].executionMode（online / batch）
        summary: ""             # functions[].summary
    out: []

  # 対象システム（統合・監査の前提）
  systems:
    - system: "SAP"
      category: "ERP"
      owner: ""
      url: ""                   # fg.sapContext.sapUrl（SAP システム URL）
      integration_modes: ["API(OData/REST/SOAP)", "IDoc", "File/Batch"]
    - system: "mcframe"
      category: "ERP/Manufacturing"
      owner: ""
      url: ""
      integration_modes: ["API", "File/Batch"]
    - system: "Salesforce"
      category: "CRM"
      owner: ""
      url: ""
      integration_modes: ["API", "Event"]

  # --- catalogs ---
  # 3種のカタログ定義。yaml.calculations / checks / messages から転記

  catalogs:
    # --- catalogs.calculations ---
    # 転記元: yaml.calculations[]
    calculations:
      - id: "CALC-001"
        name: ""
        inputs: []            # 入力パラメータ（配列）
        logic: ""             # 算出ロジック（自然言語）
        outputs: ""           # 出力定義（通貨単位含む）
        judgment: null        # 丸め以外の判定ルール（null 可）
        references: []        # 参照元（例: [P2, SCR-001.税込金額]）

    # --- catalogs.checks ---
    # 転記元: yaml.checks[]
    # フィールド名変換: continueProcessing → continue_processing, dataHandling → data_handling,
    #                   message → message_ref
    checks:
      - id: "CHK-001"
        category: ""          # input_required / input_range / input_consistency / process_error / performance
        condition: ""         # チェック条件（自然言語）
        continue_processing: "" # abort / continue / confirm_continue
        data_handling: ""     # none / all / skip_row / rollback_all
        message_ref: ""       # MSG-XX 参照
        priority: ""          # high / medium / low
        output: null          # チェック結果の出力物（null 可）
        note: null            # 補足説明（null 可）

    # --- catalogs.messages ---
    # 転記元: yaml.messages[]
    # type 値セット: error / warning / info / success
    # t100.status 値セット: ok / empty（registered/unregistered/pending は旧仕様 — 使用禁止）
    messages:
      - id: "MSG-001"
        type: ""              # error / warning / info / success
        text: ""              # メッセージ本文
        placeholders: []      # 可変部分（例: ["&1=品目コード"]）
        references: []        # 参照元チェック ID（例: [CHK-001]）
        t100:
          class: ""           # T100 メッセージクラス
          number: null        # T100 メッセージ番号（null = 未引当）
          status: ""          # ok / empty

  # --- object_definitions ---
  # 5種のオブジェクト定義。yaml.object_definitions.screens / reports / files / tables / interfaces から転記

  object_definitions:
    # --- object_definitions.screens ---
    # 転記元: yaml.objects.screens[]
    # フィールド名変換: transitionPolicy → transition_policy, visualLayout → visual_layout 等
    screens:
      - id: "SCR-001"
        name: ""
        kind: ""              # select / alv / detail / form / custom
        summary: ""           # 画面概要
        transition_policy: "" # 画面遷移方針（自然言語）
        visual_layout: ""     # レイアウト説明（自然言語）
        blocks:
          - label: ""         # ブロック名（例: ヘッダ）
            fields:
              - id: ""        # F01 等
                name: ""
                type: ""      # text / number / date 等
                max_length: 0
                input_method: "" # text / select / date 等
                io: ""        # input / output
                required: false
                default_value: null
                calc_ref: null # CALC-XX 参照
        display_rules: ""     # 表示ルール（自然言語）
        alv_toolbar: []       # ツールバーボタン定義
        access_control: ""    # 機能内権限要件（自然言語）

    # --- object_definitions.files ---
    # 転記元: yaml.objects.files[]
    # フィールド名変換: io はそのまま（direction ではない）
    files:
      - id: "FILE-001"
        name: ""
        io: ""                # input / output
        target: ""            # local / server / cloud
        format: ""            # csv / tsv / fixed / excel / xml / json
        header: true
        encoding: ""          # UTF-8 / Shift_JIS 等
        newline: ""           # CRLF / LF
        bom: false
        fields:
          - id: ""            # C01 等
            name: ""
            type: ""
            max_length: 0
            business_desc: ""
        logical_file_name: "" # 論理ファイル名（空 = 未確定）
        logical_file_name_note: null

    # --- object_definitions.reports ---
    # 転記元: yaml.objects.reports[]
    reports:
      - id: "RPT-001"
        name: ""
        kind: ""              # alv / smartforms / adobe_forms
        summary: ""
        columns:
          - id: ""
            name: ""
            type: ""
            max_length: 0
            key: false
            calc_ref: null    # CALC-XX 参照
        display_rules: ""     # ソート・色等（自然言語）
        implementation: ""    # ALV 実装クラス（例: cl_salv_table）

    # --- object_definitions.interfaces ---
    # 転記元: yaml.objects.interfaces[]
    # フィールド名変換: counterpartySystem → counterparty_system,
    #                   conditionPolicy → condition_policy,
    #                   authMethod → auth_method,
    #                   ifObjectName → if_object_name
    interfaces:
      - id: "IF-001"
        name: ""
        counterparty_system: "" # 連携先システム名
        direction: ""         # input / output / bidirectional
        timing: ""            # 実行タイミング（自然言語）
        data_names: ""        # やり取りするデータ名
        condition_policy: ""  # 連携条件・ポリシー（自然言語）
        protocol: ""          # odata_v4 / rfc_sync / idoc / file / soap
        auth_method: ""       # oauth2 / basic / cert / api_key
        if_object_name: ""    # IF オブジェクト名（空 = 未確定）
        if_object_name_note: null

    # v2: tables を追加（旧 database.data_references から移行。S-06変更: 5分類統一）
    # 転記元: yaml.object_definitions.tables[]
    tables:
      - id: "TBL-001"
        name: ""
        purpose: ""           # 用途の業務的説明
        table_names: []       # 実テーブル名の配列（標準・アドオン両方可）
        fields: []            # 項目リスト
        main_fields: ""       # 主要項目（自然言語）
        data_model_overview: "" # データモデル概要（自然言語）

  # --- processes ---
  # 転記元: yaml.processes[]（v2: process_definitions → processes に変更）
  # body は自然言語。CHK-XX / CALC-XX / MSG-XX を ID 参照する
  # v2: next は [{target, condition}] 配列（任意数リンク）
  processes:
    - id: "P1"
      name: ""
      trigger: ""             # プロセス実行トリガー
      purpose: ""             # プロセスの目的
      input: ""               # プロセスへの入力（機能内 I/O）
      output: ""              # プロセスからの出力（機能内 I/O）
      body: ""                # 処理本文（自然言語。CHK-XX/CALC-XX/MSG-XX を ID 参照）
      next: []                # v2: [{target: "P2", condition: "正常終了"}]

  # --- database ---
  # v2: database.data_references は廃止。object_definitions.tables に統合（S-06変更）
  # テーブル定義は object_definitions.tables[] に含まれる
  # ※ referenced_tables / custom_tables は旧仕様 — 使用禁止

  # --- test_matrix ---
  # 転記元: yaml.testMatrix
  # マトリクス形式（columns + test_cases）固定
  # ※ 簡易形式（cases[].axis/condition/verify_tags）は旧仕様 — 使用禁止
  # ※ test_matrix は traceability_rows とは別セクション（目的が異なる）
  # columns: テスト軸（条件の分岐観点）を定義。values に取りうる値を列挙
  # test_cases: 各軸の条件組み合わせからテストケースを導出
  #   - conditions のキー = 軸名、値 = 軸の値（"-" = 不問、配列 = パターン展開）
  #   - id は数値型（TC-XXX 形式の文字列ではない）
  test_matrix:
    columns:
      - name: ""              # 軸名（例: 会社コード、在庫状況、権限ロール）
        values: []            # 軸の取りうる値（例: [入力あり, 未入力]）
    test_cases:
      - id: 1
        conditions: {}        # キー = 軸名、値 = 軸の値
        expected_result: ""
        verify: []            # functional / boundary / security / performance 等

  # --- business_requirements ---
  # 転記元: yaml.header + yaml.businessSpec.executionConditions + yaml.businessSpec.users
  #          + yaml.businessSpec.recovery

  business_requirements:
    performance:
      volume_estimate: ""     # 処理件数規模
      response_requirement: "" # レスポンス要件
      response_requirement_delta: null # 機能群要件との差分
    localization:
      languages: ""
      currencies: ""
      timezones: ""
      environment_variations: "" # マルチマンダント/環境差異
    availability_reliability:
      recovery_method: ""     # rerunnable / rollback_rerun / manual
      recovery_note: ""       # リカバリ方法の詳細
      concurrency_constraint: "" # none / first_wins / exclusive_lock
      concurrency_note: ""
      duplicate_prevention: "" # none / warn_continue / prohibit
      duplicate_prevention_note: ""

  # --- business_value ---
  # 転記元: yaml.businessSpec.businessValue
  business_value:
    benefits: []                # businessValue.benefits — 期待効果（文字列配列）
    kpis: []                    # businessValue.kpis — KPI 指標（文字列配列）
    roi: ""                     # businessValue.roi — ROI の概要説明

  data_policy:
    contains_personal_data: false
    data_classes: ["Public", "Internal", "Confidential", "Regulated(PII/契約/財務)"]
    audit_log_required: true
    retention_policy: ""  # 例: "7 years (accounting)", "90 days (logs)"

  # NOTE: agentops_policy は v6.0.0 本体側で管理のため削除済み
  # NOTE: e2e_policy は v6.0.0 本体側で管理のため削除済み

  # BPMN 業務記述正本: BPMN 要素ごとの業務説明（traceability_rows は AC/Contract/Test 正本として別管理）
  # ⚠️ MUST: 以下の bpmn_id / process_id は process.bpmn 内の実 id と完全一致させる。
  # AI はルール literal-follow: process.bpmn の <bpmn:userTask id="BPMN-TASK-001"> を書いたら
  # ここの elements[].bpmn_id も "BPMN-TASK-001" にする。ID を勝手に変えるな。
  # 参照: agent_docs/sdd_bootstrap.md §4-BPMN, sdd-templates/docs/bpmn_quick_reference.md
  #
  # --- bpmn_descriptions ---
  # v6.0.0 標準セクションを SAP 用に修正
  # 転記元: yaml.header + yaml.businessSpec
  # ※ execution_mode, execution_type は SAP 固有追加フィールド
  # ※ elements[] は v6.0.0 標準のまま維持（overlay で変更不要）
  bpmn_descriptions:
    process:
      process_id: "BPMN-PROC-XXX"
      execution_mode: ""      # online / batch / event_driven（SAP固有）
      start_condition: ""     # 開始条件
      execution_type: ""      # 実行タイプ（自然言語）（SAP固有）
      purpose: ""             # プロセス概要
      end_condition: ""       # 完了条件
      business_outcome: ""    # ビジネス成果
      primary_actors: []      # 主要アクター（yaml.businessSpec.users.roles[].role から転記）
    elements:
      - bpmn_id: "BPMN-TASK-001"
        name: "{{ユーザータスク名}}"
        type: "userTask"
        purpose: "{{業務目的}}"
        business_role: "{{業務上の役割}}"
        trigger: "{{トリガー条件}}"
        inputs: ["{{主入力}}"]
        outputs: ["{{主出力}}"]
        business_rules: []
        exceptions: []
      - bpmn_id: "BPMN-TASK-002"
        name: "{{サービスタスク名}}"
        type: "serviceTask"
        purpose: "{{業務目的}}"
        business_role: "{{業務上の役割}}"
        trigger: "{{トリガー条件}}"
        inputs: ["{{主入力}}"]
        outputs: ["{{主出力}}"]
        business_rules: []
        exceptions: []
      - bpmn_id: "BPMN-GW-001"
        name: "{{分岐条件名}}"
        type: "exclusiveGateway"
        purpose: "{{分岐の業務意味}}"
        business_role: "{{判定基準}}"
        trigger: "{{判定のトリガー}}"
        inputs: ["{{判定対象データ}}"]
        outputs: ["{{判定結果}}"]
        business_rules: ["{{ビジネスルール}}"]
        exceptions: []

  flow_reference:
    process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"

  # --- integration_flows ---
  # v6.0.0 標準セクションを SAP 用に修正
  # 転記元: yaml.functionStructure.interFunctionConnections[]
  # ※ kpi_slo / e2e_target / source_system / target_system / mapping は SAP overlay では使用しない
  integration_flows:
    - id: "FLOW-001"
      from: ""                # 呼び出し元
      to: ""                  # 呼び出し先
      method: ""              # 連携方式（rfc / bapi / file / idoc 等）
      transaction_boundary: "" # 同一 LUW / 非同期 等

  # 最重要：抜け漏れ検出（空欄は許容。ただし ready_for_bpmn/ready_for_specify を立てる前に埋める）
  # v2: yaml からのコピーではなく、Phase 1-A1 で AI が processes[].body のパターン分岐検出から生成。
  #     Phase 1-A2 で追記。
  traceability_rows:
    - rq:
        id: "RQ-001"
        statement: ""
      us:
        id: "US-FEATXXX-001"     # 未確定なら "" でも可
        title: ""
      ac:
        id: "AC-US-FEATXXX-001-01"  # 未確定なら "" でも可
        statement: ""
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-001"      # 未確定なら "" でも可
        name: ""
      contract:
        id: "CT-API-01"          # 未確定なら "" でも可（FILE/BATCH/EDI/IDOCも可）
      database:                   # v1.2.5追加：関連DBテーブル
        tables: []               # 例: ["orders", "order_items"]
        operations: []           # 例: ["INSERT", "UPDATE", "SELECT"]
      test:
        id: "TS-INT-01"          # 未確定なら "" でも可
        type: "integration"
      task:
        id: "T-G01-001"          # 未確定なら "" でも可
    # v1.2.3: E2Eタグ付きACの例
    - rq:
        id: "RQ-002"
        statement: ""
      us:
        id: "US-FEATXXX-001"
        title: ""
      ac:
        id: "AC-US-FEATXXX-001-02"
        statement: ""
        tags: ["e2e"]             # E2Eスモーク回帰の対象
      bpmn:
        id: "BPMN-TASK-001"
        name: ""
      contract:
        id: "CT-API-01"
      database:                   # v1.2.5追加
        tables: []
        operations: []
      test:
        id: "TS-E2E-01"           # E2Eテスト
        type: "e2e"
      task:
        id: "T-G04-002"

  open_questions:
    - id: "Q-001"
      question: ""
      blocking: true
      owner: ""
      due: "YYYY-MM-DD"

  # 転記元: yaml.businessSpec.prerequisites（文字列配列）
  # ※ yaml の文字列配列を、AI が以下の構造化オブジェクトに変換して転記する
  assumptions:
    - id: "A-001"
      assumption: ""            # yaml prerequisites の文字列をそのまま転記
      rationale: ""             # AI が文脈から補完（不明なら "yaml記載のまま"）
      risk_if_false: ""         # AI が文脈から補完（不明なら ""）

  decisions:
    - id: "DR-001"
      context: ""
      options:
        - ""
      decision: ""
      consequences: ""

  # 例外は必ず憲法（Article）に紐付け、reason/mitigation をセットで残す
  exceptions: []
  # - article: "V"
  #   reason: "ERP本体DB直結が避けられない"
  #   mitigation: "Read-only view + 監査ログ + 期間限定 + 移行計画"
```

---

# 1. Executive Summary（読み方）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.context`, `scope`, `sap_context` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

## 1.1 SAP モジュール・開発概要
<!-- AI-GENERATED: sap_context から自動生成 -->
<!-- SAP 追加: SAP モジュール・Tコード情報を冒頭に追加。sap_context.program_type / program_id を明記 -->
- **プログラム種別**: `{{ basic_design.sap_context.program_type }}`
- **プログラムID**: `{{ basic_design.sap_context.program_id }}`
- **S/4HANA バージョン**: `{{ basic_design.sap_context.s4hana_version }}`
- **開発パッケージ**: `{{ basic_design.sap_context.package }}`
- **システムランドスケープ**: `{{ basic_design.sap_context.landscape }}`
<!-- END AI-GENERATED -->

## 1.2 推奨読み順（レビュー最短経路）
1) **2. Traceability（要件→US→AC→BPMN→契約→テスト→タスク）**
2) 3. Part A（WHAT/WHY要約）
3) 4. Part B（HOW方針：境界・契約・テスト・統合・例外）
4) 5. Part C（運用・フィードバックループ）
5) 6. Decision Log（判断の根拠）

## 1.3 アーティファクト対応（ハブ）
| Artifact | Path | Role | Owner |
|---|---|---|---|
| process.bpmn | {{ links.process_bpmn_ref }} | 業務フロー正本（Camunda 8形式、HITL承認） | PO/TL |
| spec.md | {{ links.spec_md_ref }} | WHAT/WHY（HOW禁止） | PO |
| plan.md | {{ links.plan_md_ref }} | HOW方針・分解・順序（コード禁止） | TL |
| tasks.md | {{ links.tasks_md_ref }} | 実行可能タスク（実装前の正本） | TL |
| constitution.md | {{ links.constitution_ref }} | 原則 / ID規約 / Gate | Arch |
| tecnos_org_constraints.md | {{ links.org_constraints_ref }} | 組織制約（統合/監査/運用/AgentOps/E2E） | PMO/Arch |
| artifact_registry.md | {{ links.artifact_registry_ref }} | 成果物マスター（ID/版/保管先） | PMO |

---

# 2. Architecture（トレーサビリティ + システムランドスケープ）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.traceability_rows`, `sap_context.landscape`, `integration_flows` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

## 2.1 Traceability（最重要：抜け漏れ検出のビュー）
<!-- AI-GENERATED: traceability_rows から自動生成 -->
| RQ | US | AC | Tags | BPMN | Contract | Database | Test | Task |
|---|---|---|---|---|---|---|---|---|
| RQ-001 | US-FEATXXX-001 | AC-US-FEATXXX-001-01 | integration | BPMN-TASK-001 | CT-API-01 | (tables) | TS-INT-01 | T-G01-001 |
| RQ-002 | US-FEATXXX-001 | AC-US-FEATXXX-001-02 | e2e | BPMN-TASK-001 | CT-API-01 | (tables) | TS-E2E-01 | T-G04-002 |
<!-- END AI-GENERATED -->

## 2.2 SAP システムランドスケープ
<!-- AI-GENERATED: sap_context.landscape, integration_flows から自動生成 -->
<!-- SAP 追加: SAP システムランドスケープ（sap_context.landscape）、IF 連携図（integration_flows）を追加 -->
- **ランドスケープ構成**: `{{ basic_design.sap_context.landscape }}`
- **IF連携一覧**:

| ID | From | To | Method | Transaction Boundary |
|---|---|---|---|---|
| FLOW-001 | `{{ integration_flows[0].from }}` | `{{ integration_flows[0].to }}` | `{{ integration_flows[0].method }}` | `{{ integration_flows[0].transaction_boundary }}` |
<!-- END AI-GENERATED -->

---

# 3. Data Model（データ参照関係）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.object_definitions.tables` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: object_definitions.tables から自動生成 -->
<!-- SAP 追加: object_definitions.tables のテーブル参照関係を表示。標準テーブル/アドオンテーブル両対応 -->

## 3.1 テーブル参照一覧
| ID | Name | Purpose | Tables | Fields |
|---|---|---|---|---|
| TBL-001 | `{{ tables[0].name }}` | `{{ tables[0].purpose }}` | `{{ tables[0].table_names | join(", ") }}` | `{{ tables[0].main_fields }}` |

## 3.2 データポリシー
- **個人データ**: `{{ basic_design.data_policy.contains_personal_data }}`
- **データ分類**: `{{ basic_design.data_policy.data_classes | join(", ") }}`
- **監査ログ**: `{{ "必須" if basic_design.data_policy.audit_log_required else "任意" }}`
- **保持期間**: `{{ basic_design.data_policy.retention_policy }}`
<!-- END AI-GENERATED -->

---

# 4. Process Flow（プロセス定義 + 画面遷移）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.processes`, `object_definitions.screens`, `bpmn_descriptions` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: processes, screens, bpmn_descriptions から自動生成 -->
<!-- SAP 追加: processes の body を自然言語展開。画面遷移図（screens の transition_policy）を追加 -->

## 4.1 BPMN プロセス概要
- **プロセスID**: `{{ basic_design.bpmn_descriptions.process.process_id }}`
- **実行モード**: `{{ basic_design.bpmn_descriptions.process.execution_mode }}`
- **開始条件**: `{{ basic_design.bpmn_descriptions.process.start_condition }}`
- **目的**: `{{ basic_design.bpmn_descriptions.process.purpose }}`
- **主要アクター**: `{{ basic_design.bpmn_descriptions.process.primary_actors | join(", ") }}`

## 4.2 プロセス定義
| ID | Name | Trigger | Purpose |
|---|---|---|---|
| P1 | `{{ processes[0].name }}` | `{{ processes[0].trigger }}` | `{{ processes[0].purpose }}` |

## 4.3 画面遷移
| Screen ID | Name | Kind | Transition Policy |
|---|---|---|---|
| SCR-001 | `{{ screens[0].name }}` | `{{ screens[0].kind }}` | `{{ screens[0].transition_policy }}` |

## 4.4 境界（ERP/SCM/CRM）
- **SoR（System of Record: データ所有）**: `{{ basic_design.systems | selectattr("category", "equalto", "ERP") | map(attribute="system") | join(", ") }}`
- **対象システム**: `{{ basic_design.systems | map(attribute="system") | join(", ") }}`
- **統合モード**: 各システムの `integration_modes` を参照
- **直接DB連携など禁止事項の例外有無**: `{{ "あり（exceptionsを参照）" if basic_design.exceptions else "なし" }}`

## 4.5 契約（Contract/CLI-First）
- **Contract list**:
  - CT-API-*: REST/OData API契約
  - CT-EVT-*: イベント契約
  - CT-FILE-*: ファイル連携契約
  - CT-IDOC-*: IDoc連携契約
- **Versioning policy**: セマンティックバージョニング
<!-- END AI-GENERATED -->

---

# 5. Test Strategy（テスト戦略 + テストマトリクス）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.test_matrix`, `catalogs.checks`, `traceability_rows` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: test_matrix, catalogs.checks, traceability_rows から自動生成 -->
<!-- SAP 追加: test_matrix を含むテスト戦略。SAP 固有テスト観点（移送/権限/多言語/BAPI）を追加 -->

## 5.1 テスト種別
- **Contract tests (TS-CON-*)**: 全CTをカバー
- **Integration tests (TS-INT-*)**: integrationタグ付きACをカバー（可能なら実システム/実コネクタ）
- **E2E tests (TS-E2E-*)**: **e2eタグ付きAC（重要ユーザージャーニー）のみ**
- **Unit tests (TS-UT-*)**: ビジネスロジック層をカバー

## 5.2 Coverage Policy
- **AC Coverage**: 100%（全ACが少なくとも1つのTSでカバー）
- **CT Coverage**: 100%（全CTがTS-CONでカバー）
- **Code Coverage**: LIB=85%/75%、CMP=60%/50%（目標、例外は記録）

## 5.3 SAP 固有テスト観点
- **移送テスト**: 移送後の動作確認（DEV→QAS→PRD）
- **権限テスト**: SAP 権限オブジェクトによるアクセス制御テスト
- **多言語テスト**: 多言語環境での表示・メッセージ確認
- **BAPI/RFC テスト**: 外部連携インターフェースの単体・結合テスト
- **大量データテスト**: `business_requirements.performance.volume_estimate` に基づく負荷テスト

## 5.4 テストマトリクス
| TC ID | Conditions | Expected Result | Verify |
|---|---|---|---|
| 1 | `{{ test_cases[0].conditions }}` | `{{ test_cases[0].expected_result }}` | `{{ test_cases[0].verify | join(", ") }}` |

## 5.5 チェックカタログ参照
| Check ID | Category | Condition | Message Ref |
|---|---|---|---|
| CHK-001 | `{{ checks[0].category }}` | `{{ checks[0].condition }}` | `{{ checks[0].message_ref }}` |
<!-- END AI-GENERATED -->

---

# 6. Risk & Mitigation（判断の根拠 + リスク）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.decisions`, `exceptions`, `open_questions`, `assumptions` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: decisions, exceptions, open_questions, assumptions から自動生成 -->
<!-- SAP 追加: SAP 固有リスク（移送競合、カーネルバージョン依存、権限設定不備等）を追加 -->

## 6.1 Decision Log
| ID | Context | Options | Decision | Consequences |
|---|---|---|---|---|
| DR-001 | `{{ decisions[0].context }}` | `{{ decisions[0].options | join(", ") }}` | `{{ decisions[0].decision }}` | `{{ decisions[0].consequences }}` |

## 6.2 例外管理
- **Exceptions**: `{{ basic_design.exceptions | length }}` 件
<!-- exceptions があれば以下に展開 -->

## 6.3 Open Questions
| ID | Question | Blocking | Owner | Due |
|---|---|---|---|---|
| Q-001 | `{{ open_questions[0].question }}` | `{{ open_questions[0].blocking }}` | `{{ open_questions[0].owner }}` | `{{ open_questions[0].due }}` |

## 6.4 Assumptions
| ID | Assumption | Rationale | Risk if False |
|---|---|---|---|
| A-001 | `{{ assumptions[0].assumption }}` | `{{ assumptions[0].rationale }}` | `{{ assumptions[0].risk_if_false }}` |

## 6.5 SAP 固有リスク
| リスク | 影響 | 緩和策 |
|--------|------|--------|
| 移送競合 | 複数開発者による同一オブジェクト変更の競合 | 移送管理ルール策定・ロック管理 |
| カーネルバージョン依存 | S/4HANAバージョンアップ時の非互換 | `sap_context.s4hana_version` 明記・互換性テスト |
| 権限設定不備 | 本番環境での機能利用不可 | 権限ロール設計・権限テスト実施 |
| 標準テーブル変更影響 | SAP標準アップグレード時の影響 | カスタムテーブル利用・Enhancement Point活用 |
<!-- END AI-GENERATED -->

---

# 7. Checks（HITL/AI両対応のGate）
## 7.1 Human Review Checklist（最小）
- [ ] Traceability に重大な欠落がない（空欄が多い場合は差し戻し）
- [ ] 未確定事項が明示され、推測で埋めていない
- [ ] Integration critical flow が明確（KPI/SLO含む）
- [ ] 監査・SoD・運用の最低要件が触れられている（`tecnos_org_constraints`準拠）
- [ ] 例外は reason/mitigation がセット（例外が無いなら exceptions は空配列）
- [ ] process.bpmn は Camunda 8 (Zeebe) 互換・DIありでレビュー可能
- [ ] **Delivery Model（requirements-driven / ftos / hybrid / ddd）が決まっている**
- [ ] **FtoS適用時のExit Criteriaが明示されている**
- [ ] **DDD適用時（validate推奨）に Domain Model / Technical Design / ADR 方針が明示されている**
- [ ] **RACI+（Human/AI/CI）が定義されている**
- [ ] **AI Policy（入力制御/ライセンス/監査）が明示されている**
- [ ] **Artifact Registry（成果物ID/版/保管先）が確定している**
- [ ] **E2Eタグ付きACは「重要ユーザージャーニー」に限定されている**（v1.2.3）
- [ ] **Coverage Policyの方針が決定されている**（v1.2.3）

## 7.2 Machine-readable Gate（basic_design_gate_check）
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

basic_design_gate_check:
  counts:
    traceability_rows: 0
    integration_flows: 0
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0

  traceability_present: false
  integration_flows_identified: false
  exceptions_documented: true  # exceptions が空でも true（方針として空を明示できていればOK）
  delivery_model_defined: false
  ddd_artifacts_ready: true    # ddd未採用ならtrue。採用時はDomain/Technical/ADR参照が必要
  raci_plus_defined: false
  ai_policy_defined: false
  artifact_registry_defined: false

  ready_for_bpmn: false            # Basic Design Gate の最終フラグ（BPMN作成へ進める）
  process_bpmn_linked: false       # process_bpmn_path が確定したら true
  process_bpmn_approved: false     # HITLでBPMN承認後に true
  ready_for_specify: false         # BPMN承認後に true（spec/plan/tasks生成へ進める）
```

## 7.3 SAP Extension Gate チェック
<!-- SAP 拡張 Gate チェック（MANIFEST.yaml validators） -->
- [ ] stride lint PASS
- [ ] coverage_policy PASS
- [ ] basic_design_completeness_validator PASS
- [ ] catalogs_consistency_validator PASS

> End of basic_design.md (SAP Extension Pack v2 merged)
