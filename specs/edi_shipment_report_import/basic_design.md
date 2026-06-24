---
artifact: "basic_design"
template_id: "TPL-BD-TECNOS-001"
feature_id: "FEAT-EDISHIPMENTREPORTIMPORT"
basic_design_id: "BD-EDISHIPMENTREPORTIMPORT-001"
title: "Basic Design - EDI出荷報告データ取込 (IF-IN-001)"
version: "2.0.0"
status: "draft"
# --- yaml 出自追跡フィールド ---
project_id: "STRIDE-PJ-EDI-2026"
function_group_id: "FG-SD005-003"
function_group_name: "EDI入庫/ロットトレース"
feature_name: "EDI出荷報告データ取込"
source_author: ""
source_updated: "2026-06-17"
source_status: "draft"
function_type: "IF"
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
  process_bpmn_ref: "specs/edi_shipment_report_import/process.bpmn"
  spec_md_ref: "specs/edi_shipment_report_import/spec.md"
  plan_md_ref: "specs/edi_shipment_report_import/plan.md"
  tasks_md_ref: "specs/edi_shipment_report_import/tasks.md"
  constitution_ref: "memory/constitution.md"
  upstream_dir_ref: "specs/edi_shipment_report_import/upstream/"
  upstream_policy_ref: "shared/policies/upstream_policy.yaml"
  baccm_completeness_ref: "shared/policies/baccm_completeness.yaml"
created_at: "2026-06-17"
updated_at: "2026-06-17"
---

> **Rule-0**: このドキュメントの正本は **#0 Canonical Basic Design (YAML)**。
>
> 修正ワークフロー: YAML 編集 → AI 再生成依頼 → stride lint で検証。
> **#7 Checks はゲート状態のため再生成しない**。

# 0. Canonical Basic Design (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "2.0.0"

policy_refs:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  artifact_registry_ref: "memory/artifact_registry.md"
  ai_policy_ref: "memory/tecnos_org_constraints.md#6.3"
  raci_plus_ref: "memory/tecnos_org_constraints.md#6.4"

derived_fields:
  counts_are_computed: true
  counts:
    traceability_rows: 6
    integration_flows: 2
    blocking_questions: 0

# --- front_matter (yaml.meta + header からの転記、Markdown 先頭 frontmatter のミラー) ---
front_matter:
  project_id: "STRIDE-PJ-EDI-2026"
  function_group_id: "FG-SD005-003"
  function_group_name: "EDI入庫/ロットトレース"
  feature_id: "FEAT-EDISHIPMENTREPORTIMPORT"
  sap_id: "IF-IN-001"
  feature_name: "EDI出荷報告データ取込"
  function_type: "IF"
  execution_mode: "自動トリガー"
  program_type: "report"
  program_id: "ZMSDP002400"
  ricef_pattern: "#4 AP-File入力→アドオンDB"
  source_author: ""
  source_updated: "2026-06-17"
  source_status: "draft"
  artifact: "basic_design"
  basic_design_id: "BD-EDISHIPMENTREPORTIMPORT-001"
  version: "2.0.0"
  status: "draft"
  created_at: "2026-06-17"
  updated_at: "2026-06-17"

basic_design:
  # --- 固定値（SAP Extension Pack）---
  profile: "enterprise-erp"
  erp_integration: true
  security_sensitive: true

  # Enterprise Extension
  epic_ref: null
  team_id: null
  coverage_tier: "critical"   # security_sensitive + erp_integration によりcritical

  organization:
    company: "Tecnos Japan"
    strategy_alignment:
      mid_term_plan: "2027-2032"
      target_state: "EDI出荷報告データを自動取込し、ロットトレース情報を一元管理する"
    program_ref:
      portfolio_items: []
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
    type: "requirements-driven"
    source: "yaml_spec"
    version: "2.0.0"
    rationale: "SAP 仕様書 yaml 起源のため"
    ftos_exit_criteria:
      enabled: false
      criteria:
        - ""
    ddd_policy:
      enabled: false
      activation_mode: "validate"
      domain_model_ref: "specs/edi_shipment_report_import/implementation-details/domain_model.md"
      technical_design_ref: "specs/edi_shipment_report_import/implementation-details/technical_design.md"
      adr_index_ref: "shared/decisions/decision-index.md"

  # --- sap_context ---
  sap_context:
    program_type: "report"
    program_id: "ZMSDP002400"
    program_id_note: "EDI出荷報告データ取込（実行可能プログラム）"
    client: ""
    sid: ""
    s4hana_version: ""
    package: "ZMSD"
    namespace: "Z"
    transport_layer: ""
    landscape: {}
    se38_attributes:
      type: "1 executable_program"
      status: ""
      fixed_point_arithmetic: true
      unicode_check: false
    dev_objects:
      - type: "PROG"
        name: "ZMSDP002400"
        description: "EDI出荷報告データ取込メインプログラム"

  # --- raci_plus ---
  raci_plus:
    actors:
      - name: "物流担当"
        usage: "EDI出荷報告データの送受信状況を確認し、取込結果のエラー対応を行う"
        scope: "EDI出荷報告データ取込ジョブの実行・監視"
      - name: "システム運用"
        usage: "夜間バッチジョブの実行・監視・障害対応"
        scope: "ジョブ実行権限・ロットトレース情報テーブルの参照"

  context:
    who: "物流担当・システム運用・販売管理（出荷ロット確認を要する利用者）"
    what: "各物流拠点(出荷ポイント)から受信した EDI 出荷報告データをロットトレース情報テーブルに登録し、出荷ロット情報を一元管理する。"
    why: "EDI 対象拠点の確定出荷ロット情報は SAP 標準の出荷伝票には存在せず、EDI 出荷報告データのみが正本である。出荷先・在庫転送先に対するロットトレース実施のため、確定したロット情報を一元化する必要がある。"

  business_domain:
    value_chain: "O2C"
    capability: "営業DX / SCM"
    domain_objects: ["ShipmentReport", "LotTrace", "Material", "DeliveryDocument"]

  scope:
    summary: "各物流拠点(出荷ポイント)からの EDI 出荷報告データをロットトレース情報テーブル(ZMSDT0004)へ登録し、履歴を出荷報告テーブル(ZMSDT0009)へ保持する。"
    target_data: "EDI出荷報告データ（送信元センターごとに連携されるCSV/固定長ファイル）"
    systemization_scope: "EDI出荷報告データの受信、形式チェック、ロットトレース情報テーブル・出荷報告テーブルへの登録までを対象とする。出庫確認(BAdI)・ロットトレース照会・ロットトレースアップロード・最終出荷ロット更新は対象外（同機能群の別Feature）。"
    in:
      - id: "IF-IN-001"
        name: "EDI出荷報告データ取込"
        type: "IF"
        execution_mode: "batch"
        summary: "EDI出荷報告データをロットトレース情報テーブルに登録するインターフェース"
    out:
      - id: "FM-IN-001"
        name: "出荷伝票の出庫確認(汎用M)"
        type: "ENH"
      - id: "REP-IN-001"
        name: "ロットトレース照会"
        type: "REP"
      - id: "IF-IN-002"
        name: "ロットトレースアップロード"
        type: "IF"
      - id: "IF-IN-003"
        name: "最終出荷ロット更新"
        type: "IF"

  # 対象システム
  systems:
    - system: "SAP"
      category: "ERP"
      owner: ""
      url: ""
      integration_modes: ["File/Batch"]
    - system: "CBP(ACMS)"
      category: "EDI Gateway"
      owner: ""
      url: ""
      integration_modes: ["File/Batch"]
    - system: "物流拠点(出荷ポイント)"
      category: "External"
      owner: ""
      url: ""
      integration_modes: ["File/Batch"]

  # --- catalogs ---
  catalogs:
    # --- catalogs.calculations ---
    calculations:
      - id: "CALC-001"
        name: "シーケンスNo.採番"
        inputs: ["出荷報告テーブルの既存最大SEQNO"]
        logic: "1からインクリメントして採番"
        outputs: "SEQNO"
        judgment: "処理日付・時刻は1ファイル内で同一値"
        references: ["P3"]

    # --- catalogs.checks ---
    checks:
      - id: "CHK-001"
        category: "process_error"
        condition: "受信先(マルコメ)が物流EDIマスタに存在しない"
        continue_processing: "abort"
        data_handling: "none"
        message_ref: "MSG-001"
        priority: "high"
        output: null
        note: "P1: 取得処理（受信先特定）で実施"
      - id: "CHK-002"
        category: "process_error"
        condition: "入力ファイルがAPサーバに存在しない"
        continue_processing: "abort"
        data_handling: "none"
        message_ref: "MSG-002"
        priority: "high"
        output: null
        note: "P1: ファイル取得時に実施"
      - id: "CHK-003"
        category: "input_range"
        condition: "二次店コード(出荷先)が出荷指示テーブルと一致しない"
        continue_processing: "confirm_continue"
        data_handling: "skip_row"
        message_ref: "MSG-005"
        priority: "medium"
        output: "出荷報告テーブル(エラー明細)"
        note: "P2: チェック処理で実施"
      - id: "CHK-004"
        category: "input_range"
        condition: "納入予定日・出荷日が日付として正しくない"
        continue_processing: "confirm_continue"
        data_handling: "skip_row"
        message_ref: "MSG-006"
        priority: "medium"
        output: "出荷報告テーブル(エラー明細)"
        note: "P2: チェック処理で実施"
      - id: "CHK-005"
        category: "input_range"
        condition: "出荷配送依頼No./商品コードが出荷指示に存在しない"
        continue_processing: "confirm_continue"
        data_handling: "skip_row"
        message_ref: "MSG-004"
        priority: "medium"
        output: "出荷報告テーブル(エラー明細)"
        note: "P2: チェック処理で実施"
      - id: "CHK-006"
        category: "input_range"
        condition: "数量が1〜999999の範囲外"
        continue_processing: "confirm_continue"
        data_handling: "skip_row"
        message_ref: "MSG-006"
        priority: "medium"
        output: "出荷報告テーブル(エラー明細)"
        note: "P2: チェック処理で実施"

    # --- catalogs.messages ---
    messages:
      - id: "MSG-001"
        type: "error"
        text: "&1 が &2 に設定されていません"
        placeholders:
          - "送信先(受手)の企業コード"
          - "物流EDIマスタ"
        references: ["CHK-001"]
        t100:
          class: "ZMSD0001"
          number: "003"
          status: "ok"
      - id: "MSG-002"
        type: "error"
        text: "&1 &2が存在しません"
        placeholders:
          - "EDI出荷報告データ"
        references: ["CHK-002"]
        t100:
          class: "ZMZZ0001"
          number: "003"
          status: "ok"
      - id: "MSG-003"
        type: "error"
        text: "ファイルが空であるか、ヘッダ行しか存在していません"
        placeholders: []
        references: []
        t100:
          class: "ZMZZ0001"
          number: "001"
          status: "ok"
      - id: "MSG-004"
        type: "error"
        text: "出荷配送依頼No.が出荷指示データに存在していません"
        placeholders: []
        references: ["CHK-005"]
        t100:
          class: "ZMSD0001"
          number: "091"
          status: "ok"
      - id: "MSG-005"
        type: "error"
        text: "&1 が &2 と異なります"
        placeholders:
          - "出荷先"
          - "出荷指示データ"
        references: ["CHK-003"]
        t100:
          class: "ZMZZ0001"
          number: "005"
          status: "ok"
      - id: "MSG-006"
        type: "error"
        text: "納入日または引取日が正しく設定されていません"
        placeholders: []
        references: ["CHK-004", "CHK-006"]
        t100:
          class: "ZMSD0001"
          number: "094"
          status: "ok"
      - id: "MSG-007"
        type: "error"
        text: "&1 の登録に失敗しました"
        placeholders:
          - "ロットトレース情報テーブル(ZMSDT0004)"
        references: []
        t100:
          class: "ZMSD0001"
          number: "004"
          status: "ok"
      - id: "MSG-008"
        type: "success"
        text: "&1 を完了しました"
        placeholders:
          - "EDI出荷報告データ取込"
        references: []
        t100:
          class: "ZMZZ0001"
          number: "033"
          status: "ok"

  # --- object_definitions ---
  object_definitions:
    screens:
      - id: "SCR-001"
        name: "選択画面"
        kind: "select"
        summary: "EDI出荷報告データ取込の選択画面。販売組織・ファイルパス・ヘッダ行数を指定する。"
        transition_policy: "実行ボタン押下でジョブ起動。エラー時は実行結果画面(RPT-001)へ遷移し処理件数を表示。"
        visual_layout: "選択条件ブロックに販売組織(SELECT-OPTIONS)、入力ファイルパス(PARAMETERS)、ヘッダ行数(PARAMETERS)を縦並びで配置。"
        blocks:
          - label: "選択条件"
            fields:
              - id: "F01"
                name: "販売組織"
                type: "CHAR"
                max_length: 4
                input_method: "SELECT-OPTIONS"
                io: "input"
                required: true
                default_value: null
                calc_ref: null
              - id: "F02"
                name: "入力ファイルパス(APサーバ)"
                type: "STRING"
                max_length: 0
                input_method: "PARAMETERS"
                io: "input"
                required: true
                default_value: null
                calc_ref: null
              - id: "F03"
                name: "ヘッダ行数"
                type: "NUMC"
                max_length: 2
                input_method: "PARAMETERS"
                io: "input"
                required: true
                default_value: null
                calc_ref: null
        display_rules: "初期値・チェンジイベントは個別仕様なし（共通仕様準拠）。"
        alv_toolbar: []
        access_control: "ジョブ実行権限（物流担当・システム運用）"

    files:
      - id: "FILE-001"
        name: "EDI出荷報告データ（EDIファイル）"
        io: "input"
        target: "server"
        format: "csv"
        header: true
        encoding: "Shift_JIS"
        newline: "CRLF"
        bom: false
        fields:
          - id: "R1_RCDKB"
            name: "1_レコード区分"
            type: "CHAR"
            max_length: 1
            business_desc: "レコード区分（固定値）"
          - id: "R1_RKGCD"
            name: "1_利用者企業コード（受け手）"
            type: "CHAR"
            max_length: 12
            business_desc: "企業コード(マルコメ)／受信先チェック"
          - id: "R1_SMTCD"
            name: "1_データ送信元センターコード"
            type: "CHAR"
            max_length: 6
            business_desc: "ステーションコード(物流/運送会社)"
          - id: "R1_SSSCD"
            name: "1_最終送信先コード"
            type: "CHAR"
            max_length: 6
            business_desc: "ステーションコード(マルコメ)"
          - id: "R2_RCDKB"
            name: "2_レコード区分"
            type: "CHAR"
            max_length: 1
            business_desc: "レコード区分（固定値）"
          - id: "R2_SHINO"
            name: "2_出荷配送依頼No."
            type: "CHAR"
            max_length: 8
            business_desc: "出荷伝票と突合（外部書式）"
          - id: "R2_SECCD"
            name: "2_二次店コード"
            type: "CHAR"
            max_length: 12
            business_desc: "出荷先＝出荷指示と一致チェック"
          - id: "R2_NOKDT"
            name: "2_納入日または引取日"
            type: "CHAR"
            max_length: 8
            business_desc: "日付妥当性チェック→LFDAT"
          - id: "R2_SHKDT"
            name: "2_出庫日"
            type: "CHAR"
            max_length: 8
            business_desc: "日付妥当性チェック→MBDAT"
          - id: "R2_DENKB"
            name: "2_伝票区分"
            type: "CHAR"
            max_length: 8
            business_desc: "伝票区分"
          - id: "DTL_MAKER"
            name: "明細_商品コード(メーカプライベート)"
            type: "CHAR"
            max_length: 13
            business_desc: "品目コードへ変換し突合"
          - id: "DTL_FRSH"
            name: "明細_商品鮮度日付"
            type: "CHAR"
            max_length: 8
            business_desc: "ロット番号を導出（ロットマスタ存在確認）"
          - id: "DTL_QTY"
            name: "明細_数量"
            type: "NUMC"
            max_length: 6
            business_desc: "1〜999999 範囲チェック"
        logical_file_name: ""
        logical_file_name_note: "未確定（運用設計で確定）"

    reports:
      - id: "RPT-001"
        name: "実行結果画面（処理件数表示）"
        kind: "alv"
        summary: "EDI出荷報告データ取込の実行結果（処理件数）を表示する ALV。"
        columns:
          - id: "C01"
            name: "選択画面パラメータ"
            type: "CHAR"
            max_length: 0
            key: false
            calc_ref: null
          - id: "C02"
            name: "処理件数（正常）"
            type: "NUMC"
            max_length: 7
            key: false
            calc_ref: null
          - id: "C03"
            name: "処理件数（エラー）"
            type: "NUMC"
            max_length: 7
            key: false
            calc_ref: null
        display_rules: "ジョブ実行完了時に処理件数（正常/エラー）を画面表示。"
        implementation: "cl_salv_table"

    interfaces:
      - id: "IF-001"
        name: "EDI出荷報告データ受信"
        counterparty_system: "CBP(ACMS)"
        direction: "input"
        timing: "夜間バッチ（日次）"
        data_names: "EDI出荷報告データ（CSV/固定長ファイル）"
        condition_policy: "送信元から複数回送信分を CBP(ACMS) でマージし1ファイルでSAPに連携。送信元ごとにファイル連携される。"
        protocol: "file"
        auth_method: "cert"
        if_object_name: ""
        if_object_name_note: "AP-File入力（#4 RICEF パターン）"

    tables:
      - id: "TBL-001"
        name: "物流EDIマスタ（受信先特定）"
        purpose: "販売組織から受信先(マルコメ)を特定する。送信先(受手)の企業コード、ステーションコード、出荷ポイントを保持。"
        table_names: []
        fields:
          - id: "KUNRG"
            name: "企業コード"
            type: "CHAR"
            max_length: 10
            business_desc: "送信先(受手)の企業コード"
          - id: "SMTCD"
            name: "ステーションコード"
            type: "CHAR"
            max_length: 6
            business_desc: "最終送信先コード"
          - id: "VKORG"
            name: "販売組織"
            type: "CHAR"
            max_length: 4
            business_desc: "選択画面の販売組織で抽出"
          - id: "VSTEL"
            name: "出荷ポイント"
            type: "CHAR"
            max_length: 4
            business_desc: "ブランク条件"
        main_fields: "KUNRG, SMTCD, VKORG"
        data_model_overview: "販売組織で抽出。VSTELはブランク条件。"
      - id: "TBL-002"
        name: "固定値テーブル（共通部品）"
        purpose: "本機能で使用する固定値を一括取得するための共通部品テーブル。"
        table_names: []
        fields:
          - id: "FIXED_VALUE"
            name: "固定値"
            type: "CHAR"
            max_length: 0
            business_desc: "本機能で使用する固定値（処理開始時に一括取得）"
        main_fields: ""
        data_model_overview: "固定値テーブルから一括取得（共通部品）。"
      - id: "TBL-003"
        name: "出荷指示テーブル"
        purpose: "出荷配送依頼No./商品コードと突合し、出荷先・出荷日・納入予定日・プラント・出庫保管場所を取得する。"
        table_names:
          - "ZMSDT0008"
        fields:
          - id: "VBELN"
            name: "出荷伝票"
            type: "CHAR"
            max_length: 10
            business_desc: "出荷配送依頼No.で突合"
          - id: "KUNNR"
            name: "出荷先"
            type: "CHAR"
            max_length: 10
            business_desc: "二次店コードと一致確認"
          - id: "MATNR"
            name: "品目コード"
            type: "CHAR"
            max_length: 40
            business_desc: "商品コードで突合"
          - id: "MBDAT"
            name: "品目利用可能日"
            type: "DATS"
            max_length: 8
            business_desc: "出荷日"
          - id: "LFDAT"
            name: "納入日付"
            type: "DATS"
            max_length: 8
            business_desc: "納入予定日"
          - id: "VKORG"
            name: "販売組織"
            type: "CHAR"
            max_length: 4
            business_desc: "荷主"
          - id: "WERKS"
            name: "プラント"
            type: "CHAR"
            max_length: 4
            business_desc: "ZMSDT0009へ転記"
          - id: "LGORT"
            name: "出庫保管場所"
            type: "CHAR"
            max_length: 4
            business_desc: "ZMSDT0009へ転記"
        main_fields: "VBELN, KUNNR, MATNR, LFDAT"
        data_model_overview: "出荷配送依頼No.をキーに突合し、KUNNR/MATNR/MBDAT/LFDAT/WERKS/LGORT等を取得する。"
      - id: "TBL-004"
        name: "ロットマスタ（ロット番号存在確認）"
        purpose: "商品鮮度日付から導出したロット番号がロットマスタに存在するかを確認する。"
        table_names: []
        fields:
          - id: "CHARG"
            name: "ロット番号"
            type: "CHAR"
            max_length: 10
            business_desc: "商品鮮度日付からのロット番号が存在するか確認"
        main_fields: "CHARG"
        data_model_overview: "ロット番号(CHARG)の存在確認のみ。"
      - id: "TBL-005"
        name: "ロットトレース情報テーブル"
        purpose: "登録対象。EDI出荷報告データから抽出した確定ロット情報を一元保持する。"
        table_names:
          - "ZMSDT0004"
        fields:
          - id: "VBELN"
            name: "出荷伝票"
            type: "CHAR"
            max_length: 10
            business_desc: "出荷配送依頼No.から特定"
          - id: "MATNR"
            name: "品目コード"
            type: "CHAR"
            max_length: 40
            business_desc: "商品コードから変換"
          - id: "CHARG"
            name: "ロット番号"
            type: "CHAR"
            max_length: 10
            business_desc: "商品鮮度日付から導出"
          - id: "MENGE"
            name: "数量"
            type: "NUMC"
            max_length: 6
            business_desc: "明細_数量"
        main_fields: "VBELN, MATNR, CHARG"
        data_model_overview: "出荷伝票/品目キーで既存確認し、存在すれば削除後に登録（P3）。"
      - id: "TBL-006"
        name: "出荷報告テーブル"
        purpose: "出荷報告履歴とエラー明細を保持。SEQNOで一意化（CALC-001）。"
        table_names:
          - "ZMSDT0009"
        fields:
          - id: "SEQNO"
            name: "シーケンスNo."
            type: "NUMC"
            max_length: 10
            business_desc: "CALC-001で採番"
          - id: "WERKS"
            name: "プラント"
            type: "CHAR"
            max_length: 4
            business_desc: "ZMSDT0008から転記"
          - id: "LGORT"
            name: "出庫保管場所"
            type: "CHAR"
            max_length: 4
            business_desc: "ZMSDT0008から転記"
          - id: "ERR_MSG"
            name: "エラーメッセージ"
            type: "CHAR"
            max_length: 200
            business_desc: "チェックNG時のエラー内容"
        main_fields: "SEQNO, WERKS, LGORT"
        data_model_overview: "履歴・エラー保持。1ファイル内で処理日付・時刻は同一値。"

  # --- processes ---
  process_definitions:
    - id: "P1"
      name: "取得処理（固定値・送受信先・ファイル）"
      trigger: "実行ボタン押下／ジョブ起動"
      purpose: "固定値・物流EDIマスタ・ファイルを取得し受信先を特定"
      input: "選択画面（販売組織/ファイルパス/ヘッダ行数）"
      output: "EDI出荷報告データ（明細）"
      body: |
        固定値テーブルを一括取得。
        物流EDIマスタから販売組織で受信先(マルコメ)を特定（CHK-001）。
        APサーバのファイルを取得しヘッダ行数分を除外（CHK-002）。0件ならMSG-003で終了。
        ソート（送信元センター/出荷配送依頼No/商品コード）。
      next:
        - target: "P2"
          condition: "正常終了"
        - target: "終了"
          condition: "チェックNG"
    - id: "P2"
      name: "EDI出荷報告データチェック"
      trigger: "取得処理完了"
      purpose: "出荷指示との突合と各項目の妥当性チェック"
      input: "EDI出荷報告データ"
      output: "正常データ／エラーデータ"
      body: |
        二次店コード(出荷先)が出荷指示と一致（CHK-003）。
        納入予定日・出荷日が日付として妥当（CHK-004）。
        出荷配送依頼No.／商品コードが出荷指示に存在（CHK-005）。
        数量が1〜999999（CHK-006）。
        エラー明細は出荷報告テーブルにエラーメッセージを保持。
      next:
        - target: "P3"
          condition: "正常終了"
        - target: "P3"
          condition: "チェックNG"
    - id: "P3"
      name: "テーブル登録（ロットトレース情報・出荷報告）"
      trigger: "チェック完了"
      purpose: "正常データをロットトレース情報テーブルへ登録、履歴を出荷報告テーブルへ保持"
      input: "正常データ／エラーデータ"
      output: "ZMSDT0004／ZMSDT0009"
      body: |
        出荷伝票／品目キーで既存を確認し、存在すれば削除後に登録（CALC-001でSEQNO採番）。
        登録/削除失敗時はロールバックしMSG-007で終了。
        完了をMSG-008で出力（INSERT/COMMIT）。
      next:
        - target: "終了"
          condition: "正常終了"
        - target: "終了"
          condition: "チェックNG"

  # --- test_matrix ---
  test_matrix:
    columns:
      - name: "前提条件"
        values:
          - "受信先(マルコメ)が物流EDIマスタに存在しない"
          - "入力ファイルがAPサーバに存在しない"
          - "二次店コード(出荷先)が出荷指示テーブルと一致しない"
          - "納入予定日・出荷日が日付として正しくない"
          - "出荷配送依頼No./商品コードが出荷指示に存在しない"
          - "数量が1〜999999の範囲外"
    test_cases:
      - id: 1
        conditions:
          前提条件: "受信先(マルコメ)が物流EDIマスタに存在しない"
        expected_result: "中断 / MSG-001"
        verify: ["functional", "boundary"]
      - id: 2
        conditions:
          前提条件: "入力ファイルがAPサーバに存在しない"
        expected_result: "中断 / MSG-002"
        verify: ["functional", "boundary"]
      - id: 3
        conditions:
          前提条件: "二次店コード(出荷先)が出荷指示テーブルと一致しない"
        expected_result: "確認後続行 / MSG-005"
        verify: ["functional"]
      - id: 4
        conditions:
          前提条件: "納入予定日・出荷日が日付として正しくない"
        expected_result: "確認後続行 / MSG-006"
        verify: ["functional", "boundary"]
      - id: 5
        conditions:
          前提条件: "出荷配送依頼No./商品コードが出荷指示に存在しない"
        expected_result: "確認後続行 / MSG-004"
        verify: ["functional"]
      - id: 6
        conditions:
          前提条件: "数量が1〜999999の範囲外"
        expected_result: "確認後続行 / MSG-006"
        verify: ["functional", "boundary"]

  # --- business_requirements ---
  business_requirements:
    performance:
      volume_estimate: "平均=3000明細 予想量=3000明細"
      response_requirement: "レスポンス時間 5秒以内"
      response_requirement_delta: "なし（機能群要件と同一）"
    localization:
      languages: "JA"
      currencies: "JPY"
      timezones: "Asia/Tokyo"
      environment_variations: "本番／検証／開発の3環境"
    availability_reliability:
      recovery_method: "rerunnable"
      recovery_note: "登録/削除失敗時はロールバックしMSG-007で終了。ファイル再投入で再実行可能。"
      concurrency_constraint: "none"
      concurrency_note: "EDI出荷報告データ取込とロットトレースアップロードは同一出荷伝票に対して同時に行われることはない（前提条件）。"
      duplicate_prevention: "prohibit"
      duplicate_prevention_note: "出荷伝票／品目キーで既存確認し、存在すれば削除後に登録（重複防止）。"

  # --- business_value ---
  business_value:
    benefits:
      - "出荷先／在庫転送先向けに出荷した品目毎の最終出荷ロットの情報を確認できる"
      - "EDI 対象拠点の確定出荷ロット情報を一元管理し、ロットトレースを実施できる"
    kpis:
      - "EDI出荷報告データ取込ジョブ成功率 99%以上"
      - "取込エラー件数（日次）"
    roi: "EDI 対象拠点の出荷ロット情報を自動取込することで、手作業によるロット情報入力・確認工数を削減し、ロットトレース精度を向上する。"

  data_policy:
    contains_personal_data: false
    data_classes: ["Internal", "Confidential"]
    audit_log_required: true
    retention_policy: "7 years (accounting/traceability)"

  # --- bpmn_descriptions ---
  bpmn_descriptions:
    process:
      process_id: "BPMN-PROC-EDISHIPMENTREPORTIMPORT"
      execution_mode: "batch"
      start_condition: "実行ボタン押下／ジョブ起動（夜間バッチ・日次）"
      execution_type: "オンライン+バッチ（プログラム実行）"
      purpose: "EDI出荷報告データをロットトレース情報テーブル(ZMSDT0004)と出荷報告テーブル(ZMSDT0009)に登録し、出荷ロット情報を一元管理する"
      end_condition: "全明細の登録／エラー対応完了。MSG-008で完了出力"
      business_outcome: "EDI対象拠点の確定出荷ロット情報がロットトレース情報テーブルに反映される"
      primary_actors: ["物流担当", "システム運用"]
    elements:
      - bpmn_id: "BPMN-EVT-001"
        name: "ジョブ起動"
        type: "startEvent"
        purpose: "夜間バッチまたは実行ボタンでジョブを起動する"
        business_role: "取込処理の開始トリガー"
        trigger: "ジョブスケジューラ／実行ボタン押下"
        inputs: ["選択画面パラメータ"]
        outputs: ["取込処理開始"]
        business_rules: []
        exceptions: []
      - bpmn_id: "BPMN-TASK-001"
        name: "P1: 取得処理（固定値・送受信先・ファイル）"
        type: "serviceTask"
        purpose: "固定値・物流EDIマスタ・APサーバのファイルを取得し受信先を特定"
        business_role: "前処理（前提データの取得とファイル受信）"
        trigger: "ジョブ起動"
        inputs: ["選択画面パラメータ", "固定値テーブル(TBL-002)", "物流EDIマスタ(TBL-001)", "EDIファイル(FILE-001)"]
        outputs: ["EDI出荷報告データ（ソート済み明細）"]
        business_rules:
          - "CHK-001: 受信先(マルコメ)が物流EDIマスタに存在するか"
          - "CHK-002: 入力ファイルがAPサーバに存在するか"
        exceptions:
          - "MSG-001: 受信先未設定 → 中断"
          - "MSG-002: ファイル不在 → 中断"
          - "MSG-003: ファイル空 → 中断"
      - bpmn_id: "BPMN-TASK-002"
        name: "P2: EDI出荷報告データチェック"
        type: "serviceTask"
        purpose: "出荷指示との突合と各項目の妥当性チェックを行う"
        business_role: "入力データの妥当性検証"
        trigger: "取得処理完了"
        inputs: ["EDI出荷報告データ", "出荷指示テーブル(TBL-003)", "ロットマスタ(TBL-004)"]
        outputs: ["正常データ", "エラーデータ"]
        business_rules:
          - "CHK-003: 二次店コード一致"
          - "CHK-004: 日付妥当性"
          - "CHK-005: 出荷配送依頼No./商品コード存在"
          - "CHK-006: 数量範囲"
        exceptions:
          - "MSG-004 / MSG-005 / MSG-006: 確認後続行（エラー明細を出荷報告テーブルに保持）"
      - bpmn_id: "BPMN-GW-001"
        name: "取得処理OK?"
        type: "exclusiveGateway"
        purpose: "受信先特定／ファイル取得の成否で次工程を判定"
        business_role: "前提エラーの即時遮断"
        trigger: "P1 取得処理完了"
        inputs: ["CHK-001/CHK-002 判定結果"]
        outputs: ["P2 続行 or 異常終了"]
        business_rules:
          - "CHK-001/CHK-002 OK かつファイル明細1件以上 → P2 へ。NG → MSG-001/002/003 で異常終了"
        exceptions:
          - "CHK-001/CHK-002 NG: BPMN-EVT-003 異常終了へ"
      - bpmn_id: "BPMN-GW-002"
        name: "正常データあり?"
        type: "exclusiveGateway"
        purpose: "チェック後の正常データ件数で登録処理に進むか終了するかを判定"
        business_role: "登録対象データの存在判定"
        trigger: "P2 チェック完了"
        inputs: ["正常データ件数", "エラーデータ件数"]
        outputs: ["P3 登録処理 or 正常終了"]
        business_rules:
          - "正常データが1件以上あれば P3 へ。0件（エラーのみ）の場合は登録スキップして正常終了"
        exceptions: []
      - bpmn_id: "BPMN-GW-003"
        name: "登録成功?"
        type: "exclusiveGateway"
        purpose: "ZMSDT0004 / ZMSDT0009 INSERT/COMMIT の成否を判定"
        business_role: "DB登録失敗時のロールバック・中断判定"
        trigger: "P3 登録処理完了"
        inputs: ["INSERT/COMMIT 実行結果"]
        outputs: ["正常終了 or 異常終了"]
        business_rules:
          - "登録成功 → MSG-008 完了。登録失敗 → ロールバックし MSG-007 で異常終了"
        exceptions:
          - "INSERT/COMMIT 失敗: ロールバック + MSG-007"
      - bpmn_id: "BPMN-TASK-003"
        name: "P3: テーブル登録（ロットトレース情報・出荷報告）"
        type: "serviceTask"
        purpose: "正常データをロットトレース情報テーブル(ZMSDT0004)に登録し、履歴を出荷報告テーブル(ZMSDT0009)に保持"
        business_role: "確定ロット情報のDB登録（INSERT/COMMIT）"
        trigger: "正常データあり"
        inputs: ["正常データ", "エラーデータ"]
        outputs: ["ZMSDT0004(ロットトレース情報)", "ZMSDT0009(出荷報告)"]
        business_rules:
          - "出荷伝票／品目キーで既存確認、存在すれば削除後に登録"
          - "CALC-001: SEQNO採番（1からインクリメント）"
        exceptions:
          - "MSG-007: 登録/削除失敗 → ロールバックして中断"
          - "MSG-008: 完了出力"
      - bpmn_id: "BPMN-EVT-002"
        name: "正常終了"
        type: "endEvent"
        purpose: "全データ処理完了。MSG-008で完了出力"
        business_role: "ジョブ正常終了"
        trigger: "P3 INSERT/COMMIT完了"
        inputs: ["処理件数（正常/エラー）"]
        outputs: ["RPT-001 実行結果画面表示", "MSG-008 完了メッセージ"]
        business_rules: []
        exceptions: []
      - bpmn_id: "BPMN-EVT-003"
        name: "異常終了"
        type: "endEvent"
        purpose: "前提エラー or 登録失敗による中断終了"
        business_role: "ジョブ異常終了（再投入が必要）"
        trigger: "CHK-001/CHK-002 中断 or MSG-007 ロールバック"
        inputs: ["エラーメッセージ"]
        outputs: ["エラーログ", "RPT-001 実行結果画面表示"]
        business_rules: []
        exceptions: []

  flow_reference:
    process_bpmn_path: "specs/edi_shipment_report_import/process.bpmn"
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"

  # --- integration_flows ---
  integration_flows:
    - id: "FLOW-001"
      from: "IF-IN-001 (EDI出荷報告データ取込)"
      to: "REP-IN-001 (ロットトレース照会)"
      method: "DB経由 (ZMSDT0004 ロットトレース情報テーブル)"
      transaction_boundary: "非同期（DB登録後に照会側が参照）"
    - id: "FLOW-002"
      from: "IF-IN-001 (EDI出荷報告データ取込)"
      to: "IF-IN-003 (最終出荷ロット更新)"
      method: "DB経由 (ZMSDT0004 ロットトレース情報テーブル)"
      transaction_boundary: "非同期（DB登録後に最終出荷ロット更新側が参照）"

  # --- traceability_rows ---
  traceability_rows:
    - rq:
        id: "RQ-001"
        statement: "EDI出荷報告データの受信先を特定し、APサーバから入力ファイルを取得できる"
      us:
        id: "US-FEATEDISHIP-001"
        title: "EDI出荷報告データを取得する"
      ac:
        id: "AC-US-FEATEDISHIP-001-01"
        statement: "受信先（マルコメ）が物流EDIマスタに存在しない場合、MSG-001で中断する"
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-001"
        name: "P1: 取得処理（固定値・送受信先・ファイル）"
      contract:
        id: "CT-FILE-01"
      database:
        tables: ["TBL-001", "TBL-002"]
        operations: ["SELECT"]
      test:
        id: "TS-INT-01"
        type: "integration"
      task:
        id: "T-G01-001"
    - rq:
        id: "RQ-002"
        statement: "EDI出荷報告データの入力ファイルが存在しない場合は中断する"
      us:
        id: "US-FEATEDISHIP-001"
        title: "EDI出荷報告データを取得する"
      ac:
        id: "AC-US-FEATEDISHIP-001-02"
        statement: "入力ファイルがAPサーバに存在しない場合、MSG-002で中断する"
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-001"
        name: "P1: 取得処理（固定値・送受信先・ファイル）"
      contract:
        id: "CT-FILE-01"
      database:
        tables: []
        operations: []
      test:
        id: "TS-INT-02"
        type: "integration"
      task:
        id: "T-G01-002"
    - rq:
        id: "RQ-003"
        statement: "EDI出荷報告データの明細を出荷指示テーブルと突合し妥当性を検証する"
      us:
        id: "US-FEATEDISHIP-002"
        title: "EDI出荷報告データをチェックする"
      ac:
        id: "AC-US-FEATEDISHIP-002-01"
        statement: "二次店コード／日付／出荷配送依頼No.／商品コード／数量を出荷指示と突合し、不一致／範囲外はエラー明細として出荷報告テーブルに保持する"
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-002"
        name: "P2: EDI出荷報告データチェック"
      contract:
        id: "CT-DB-01"
      database:
        tables: ["TBL-003", "TBL-004", "TBL-006"]
        operations: ["SELECT", "INSERT"]
      test:
        id: "TS-INT-03"
        type: "integration"
      task:
        id: "T-G02-001"
    - rq:
        id: "RQ-004"
        statement: "正常データをロットトレース情報テーブルに登録し、履歴を出荷報告テーブルに保持する"
      us:
        id: "US-FEATEDISHIP-003"
        title: "ロットトレース情報を登録する"
      ac:
        id: "AC-US-FEATEDISHIP-003-01"
        statement: "出荷伝票／品目キーで既存確認、存在すれば削除後にZMSDT0004にINSERT。登録失敗時はロールバックしMSG-007を出力する"
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-003"
        name: "P3: テーブル登録（ロットトレース情報・出荷報告）"
      contract:
        id: "CT-DB-02"
      database:
        tables: ["TBL-005", "TBL-006"]
        operations: ["DELETE", "INSERT", "COMMIT"]
      test:
        id: "TS-INT-04"
        type: "integration"
      task:
        id: "T-G03-001"
    - rq:
        id: "RQ-005"
        statement: "正常データのSEQNOを採番する"
      us:
        id: "US-FEATEDISHIP-003"
        title: "ロットトレース情報を登録する"
      ac:
        id: "AC-US-FEATEDISHIP-003-02"
        statement: "出荷報告テーブルの既存最大SEQNOから1インクリメントしてCALC-001で採番する。1ファイル内で処理日付・時刻は同一値"
        tags: ["data"]
      bpmn:
        id: "BPMN-TASK-003"
        name: "P3: テーブル登録（ロットトレース情報・出荷報告）"
      contract:
        id: "CT-DB-02"
      database:
        tables: ["TBL-006"]
        operations: ["SELECT", "INSERT"]
      test:
        id: "TS-UT-01"
        type: "unit"
      task:
        id: "T-G03-002"
    - rq:
        id: "RQ-006"
        statement: "実行結果（処理件数）を画面表示する"
      us:
        id: "US-FEATEDISHIP-004"
        title: "実行結果を確認する"
      ac:
        id: "AC-US-FEATEDISHIP-004-01"
        statement: "RPT-001 実行結果画面に選択画面パラメータと処理件数（正常/エラー）を表示する。完了時はMSG-008、中断時は該当MSGを出力する"
        tags: ["e2e"]
      bpmn:
        id: "BPMN-EVT-002"
        name: "正常終了"
      contract:
        id: "CT-CLI-01"
      database:
        tables: []
        operations: []
      test:
        id: "TS-E2E-01"
        type: "e2e"
      task:
        id: "T-G04-001"

  open_questions: []

  # --- assumptions (yaml.businessSpec.prerequisites → 構造化) ---
  assumptions:
    - id: "A-001"
      assumption: "本機能における関連マスタが正しく設定されている（物流系IFにおける送信元/先のコード（ステーションコード、企業コード）、固定値テーブルのデータ）"
      rationale: "受信先特定・出荷指示突合のキー情報がマスタ整備済みであることが前提"
      risk_if_false: "受信先未特定エラー（MSG-001）・チェックNGの多発、再投入による業務停滞"
    - id: "A-002"
      assumption: "送信元から複数回送信分を CBP(ACMS) でマージし1ファイルでSAPに連携される（マージ対象に同一出荷伝票のデータが存在しない／変更ファイル送信時は運用で変更前ファイルを削除する）"
      rationale: "ファイルマージは CBP 側責務。SAP は1ファイル前提で処理する"
      risk_if_false: "重複明細による予期せぬ挙動（既存削除後に再登録の重複）"
    - id: "A-003"
      assumption: "EDI出荷報告データ(フォーマット変換後)は、送信元ごとにファイル連携される"
      rationale: "送信元ごとに独立処理可能なため"
      risk_if_false: "送信元混在ファイルの場合、受信先特定ロジック修正が必要"
    - id: "A-004"
      assumption: "EDI出荷報告データ取込とロットトレースアップロードは、同一出荷伝票に対して同時に行われることはない"
      rationale: "排他制御を簡素化するため"
      risk_if_false: "ZMSDT0004の同時更新による不整合"
    - id: "A-005"
      assumption: "ロットトレースアップロードの出荷伝票明細毎の数量は正しくデータが作成される"
      rationale: "アップロード側で数量整合性を担保することを前提とする"
      risk_if_false: "明細数量の二重カウントまたは欠損"
    - id: "A-006"
      assumption: "SAPとCBP(ACMS)間のIF仕様に関してはプロジェクト標準に準拠する"
      rationale: "IF仕様（文字コード／改行／ファイル受渡し）は標準準拠"
      risk_if_false: "個別IF仕様による追加実装が発生"

  decisions:
    - id: "DR-001"
      context: "EDI出荷報告データのSAP取込方式（File取込 vs 標準IDoc）"
      options:
        - "File取込（ACMS経由のAP-File入力 → アドオンDB登録）— #4 RICEF パターン"
        - "標準IDoc／RFC連携"
      decision: "File取込を採用（#4 RICEF パターン）"
      consequences: "ACMS のファイルマージ運用に依存。アドオンテーブル(ZMSDT0004/ZMSDT0009)で一元管理。"
    - id: "DR-002"
      context: "重複明細の取扱（既存出荷伝票／品目の再連携）"
      options:
        - "既存レコードを削除後にINSERT（上書き）"
        - "差分のみINSERT（履歴保持）"
      decision: "既存削除後にINSERT（上書き）"
      consequences: "確定ロット情報の最新化を優先。履歴は出荷報告テーブル(ZMSDT0009)で保持。"

  exceptions: []

basic_design_gate_check:
  counts:
    traceability_rows: 6
    integration_flows: 2
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0

  traceability_present: true
  integration_flows_identified: true
  exceptions_documented: true
  delivery_model_defined: true
  ddd_artifacts_ready: true
  raci_plus_defined: true
  ai_policy_defined: true
  artifact_registry_defined: true

  ready_for_bpmn: true
  process_bpmn_linked: true
  process_bpmn_approved: true
  ready_for_specify: true
```

---

# 1. Executive Summary

## 1.1 SAP モジュール・開発概要
- **プログラム種別**: report（実行可能プログラム）
- **プログラムID**: ZMSDP002400
- **S/4HANA バージョン**: （プロジェクト標準準拠）
- **開発パッケージ**: ZMSD
- **RICEF パターン**: #4 AP-File入力 → アドオンDB

## 1.2 推奨読み順
1) **2. Traceability**（要件→US→AC→BPMN→契約→テスト→タスク）
2) 3. Part A（WHAT/WHY 要約）
3) 4. Part B（HOW 方針：境界・契約・テスト・統合・例外）
4) 5. Part C（運用・フィードバックループ）
5) 6. Decision Log

## 1.3 アーティファクト対応
| Artifact | Path | Role | Owner |
|---|---|---|---|
| process.bpmn | specs/edi_shipment_report_import/process.bpmn | 業務フロー正本（Camunda 8形式、HITL承認） | PO/TL |
| spec.md | specs/edi_shipment_report_import/spec.md | WHAT/WHY（HOW禁止） | PO |
| plan.md | specs/edi_shipment_report_import/plan.md | HOW方針・分解・順序（コード禁止） | TL |
| tasks.md | specs/edi_shipment_report_import/tasks.md | 実行可能タスク | TL |

---

# 2. Architecture（トレーサビリティ + システムランドスケープ）

## 2.1 Traceability
| RQ | US | AC | Tags | BPMN | Contract | Database | Test | Task |
|---|---|---|---|---|---|---|---|---|
| RQ-001 | US-FEATEDISHIP-001 | AC-US-FEATEDISHIP-001-01 | integration | BPMN-TASK-001 | CT-FILE-01 | TBL-001, TBL-002 / SELECT | TS-INT-01 | T-G01-001 |
| RQ-002 | US-FEATEDISHIP-001 | AC-US-FEATEDISHIP-001-02 | integration | BPMN-TASK-001 | CT-FILE-01 | — | TS-INT-02 | T-G01-002 |
| RQ-003 | US-FEATEDISHIP-002 | AC-US-FEATEDISHIP-002-01 | integration | BPMN-TASK-002 | CT-DB-01 | TBL-003,TBL-004,TBL-006 / SELECT,INSERT | TS-INT-03 | T-G02-001 |
| RQ-004 | US-FEATEDISHIP-003 | AC-US-FEATEDISHIP-003-01 | integration | BPMN-TASK-003 | CT-DB-02 | TBL-005,TBL-006 / DELETE,INSERT,COMMIT | TS-INT-04 | T-G03-001 |
| RQ-005 | US-FEATEDISHIP-003 | AC-US-FEATEDISHIP-003-02 | data | BPMN-TASK-003 | CT-DB-02 | TBL-006 / SELECT,INSERT | TS-UT-01 | T-G03-002 |
| RQ-006 | US-FEATEDISHIP-004 | AC-US-FEATEDISHIP-004-01 | e2e | BPMN-EVT-002 | CT-CLI-01 | — | TS-E2E-01 | T-G04-001 |

## 2.2 SAP システムランドスケープ
- **IF連携一覧**:

| ID | From | To | Method | Transaction Boundary |
|---|---|---|---|---|
| FLOW-001 | IF-IN-001 | REP-IN-001 | DB経由 (ZMSDT0004) | 非同期 |
| FLOW-002 | IF-IN-001 | IF-IN-003 | DB経由 (ZMSDT0004) | 非同期 |

---

# 3. Data Model

## 3.1 テーブル参照一覧
| ID | Name | Purpose | Tables | Main Fields |
|---|---|---|---|---|
| TBL-001 | 物流EDIマスタ | 販売組織から受信先(マルコメ)を特定 | （アドオンマスタ） | KUNRG, SMTCD, VKORG |
| TBL-002 | 固定値テーブル | 共通部品 | （アドオン共通） | — |
| TBL-003 | 出荷指示テーブル | 出荷配送依頼No./商品コードで突合 | ZMSDT0008 | VBELN, KUNNR, MATNR, LFDAT |
| TBL-004 | ロットマスタ | ロット番号存在確認 | （標準ロットマスタ） | CHARG |
| TBL-005 | ロットトレース情報テーブル | 確定ロット情報を一元保持（登録対象） | ZMSDT0004 | VBELN, MATNR, CHARG |
| TBL-006 | 出荷報告テーブル | 履歴とエラー明細（登録対象） | ZMSDT0009 | SEQNO, WERKS, LGORT |

## 3.2 データポリシー
- **個人データ**: なし
- **データ分類**: Internal / Confidential
- **監査ログ**: 必須（取込件数・エラー明細・MSG-008/MSG-007）
- **保持期間**: 7 years (accounting/traceability)

---

# 4. Process Flow

## 4.1 BPMN プロセス概要
- **プロセスID**: BPMN-PROC-EDISHIPMENTREPORTIMPORT
- **実行モード**: batch
- **開始条件**: 実行ボタン押下／ジョブ起動（夜間バッチ・日次）
- **目的**: EDI出荷報告データをZMSDT0004/ZMSDT0009に登録し出荷ロット情報を一元管理
- **主要アクター**: 物流担当, システム運用

## 4.2 プロセス定義
| ID | Name | Trigger | Purpose |
|---|---|---|---|
| P1 | 取得処理（固定値・送受信先・ファイル） | 実行ボタン押下／ジョブ起動 | 固定値・物流EDIマスタ・ファイルを取得し受信先を特定 |
| P2 | EDI出荷報告データチェック | 取得処理完了 | 出荷指示との突合と各項目の妥当性チェック |
| P3 | テーブル登録（ロットトレース情報・出荷報告） | チェック完了 | 正常データを ZMSDT0004 へ登録、履歴を ZMSDT0009 へ保持 |

## 4.3 画面遷移
| Screen ID | Name | Kind | Transition Policy |
|---|---|---|---|
| SCR-001 | 選択画面 | select | 実行ボタン押下でジョブ起動。完了時に RPT-001 表示 |

## 4.4 境界（ERP/SCM/EDI）
- **SoR**: SAP (ZMSDT0004 / ZMSDT0009 / ZMSDT0008)
- **対象システム**: SAP, CBP(ACMS), 物流拠点(出荷ポイント)
- **直接DB連携など禁止事項の例外有無**: なし

## 4.5 契約（Contract）
- **Contract list**:
  - CT-FILE-01: EDI出荷報告データファイル契約
  - CT-DB-01: 出荷指示テーブル参照契約
  - CT-DB-02: ロットトレース情報／出荷報告テーブル登録契約
  - CT-CLI-01: 実行結果画面（ALV）表示契約
- **Versioning policy**: セマンティックバージョニング

---

# 5. Test Strategy

## 5.1 テスト種別
- **Contract tests (TS-CON-*)**: 全CTをカバー
- **Integration tests (TS-INT-*)**: integrationタグ付きACをカバー
- **E2E tests (TS-E2E-*)**: 重要ユーザージャーニーのみ（実行結果確認）
- **Unit tests (TS-UT-*)**: ビジネスロジック層（SEQNO採番等）

## 5.2 Coverage Policy
- AC Coverage: 100%
- CT Coverage: 100%

## 5.3 SAP 固有テスト観点
- **移送テスト**: DEV→QAS→PRD の移送後動作確認
- **権限テスト**: ジョブ実行権限・テーブル登録権限
- **大量データテスト**: 3000明細／5秒以内の応答要件検証

## 5.4 テストマトリクス
| TC ID | 前提条件 | Expected | Verify |
|---|---|---|---|
| 1 | 受信先(マルコメ)が物流EDIマスタに存在しない | 中断 / MSG-001 | functional, boundary |
| 2 | 入力ファイルがAPサーバに存在しない | 中断 / MSG-002 | functional, boundary |
| 3 | 二次店コードが出荷指示と一致しない | 確認後続行 / MSG-005 | functional |
| 4 | 納入予定日・出荷日が正しくない | 確認後続行 / MSG-006 | functional, boundary |
| 5 | 出荷配送依頼No./商品コードが出荷指示に存在しない | 確認後続行 / MSG-004 | functional |
| 6 | 数量が1〜999999の範囲外 | 確認後続行 / MSG-006 | functional, boundary |

## 5.5 チェックカタログ参照
| Check ID | Category | Condition | Message Ref |
|---|---|---|---|
| CHK-001 | process_error | 受信先が物流EDIマスタに存在しない | MSG-001 |
| CHK-002 | process_error | 入力ファイルがAPサーバに存在しない | MSG-002 |
| CHK-003 | input_range | 二次店コード不一致 | MSG-005 |
| CHK-004 | input_range | 日付妥当性NG | MSG-006 |
| CHK-005 | input_range | 出荷配送依頼No./商品コード不在 | MSG-004 |
| CHK-006 | input_range | 数量範囲外 | MSG-006 |

---

# 6. Risk & Mitigation

## 6.1 Decision Log
| ID | Context | Decision | Consequences |
|---|---|---|---|
| DR-001 | EDI出荷報告データの取込方式（File vs IDoc） | File取込（#4 RICEF） | ACMS のファイルマージ運用に依存 |
| DR-002 | 既存重複明細の取扱（再連携時） | 既存削除後にINSERT | 確定ロット情報の最新化を優先 |

## 6.2 例外管理
- **Exceptions**: 0 件（憲法 Article 例外なし）

## 6.3 Open Questions
- なし

## 6.4 Assumptions
| ID | Assumption | Rationale | Risk if False |
|---|---|---|---|
| A-001 | 関連マスタが正しく設定されている | キー情報がマスタ整備済み前提 | チェックNG多発・業務停滞 |
| A-002 | CBP(ACMS) で複数回送信分がマージされる | マージは CBP 側責務 | 重複明細による予期せぬ挙動 |
| A-003 | EDI出荷報告データは送信元ごとにファイル連携 | 送信元ごとに独立処理 | 受信先特定ロジック修正要 |
| A-004 | 同一出荷伝票への同時取込なし | 排他制御簡素化 | ZMSDT0004 の同時更新不整合 |
| A-005 | アップロード側で数量整合性を担保 | 上流データ正確性前提 | 数量二重カウント／欠損 |
| A-006 | SAP-CBP間IF仕様はプロジェクト標準準拠 | 個別調整不要前提 | 個別実装発生 |

## 6.5 SAP 固有リスク
| リスク | 影響 | 緩和策 |
|--------|------|--------|
| 移送競合 | 同一オブジェクトの並行開発 | 移送管理・ロック管理 |
| カーネルバージョン依存 | S/4HANA バージョンアップ非互換 | sap_context.s4hana_version 明記・互換性テスト |
| 権限設定不備 | 本番でジョブ実行不可 | 権限ロール設計・権限テスト |
| ファイル文字コード差異 | Shift_JIS 前提が崩れた場合の文字化け | encoding を仕様で固定し受信時に検証 |

---

# 7. Checks（HITL/AI 両対応の Gate）

## 7.1 Human Review Checklist
- [x] Traceability に重大な欠落がない
- [x] 未確定事項が明示され、推測で埋めていない
- [x] Integration critical flow が明確
- [x] 監査・運用の最低要件が触れられている
- [x] 例外は reason/mitigation がセット（例外なしは空配列で明示）
- [x] process.bpmn は Camunda 8 (Zeebe) 互換・DIありでレビュー可能 ← Gate 2 承認済
- [x] Delivery Model（requirements-driven）が決まっている
- [x] RACI+ が定義されている
- [x] AI Policy が明示されている
- [x] Artifact Registry が確定している
- [x] E2Eタグ付きACは重要ユーザージャーニーに限定（AC-US-EDISHIP-004-01のみ）
- [x] Coverage Policy 方針が決定されている

## 7.2 Machine-readable Gate（basic_design_gate_check）
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "2.0.0"

basic_design_gate_check:
  counts:
    traceability_rows: 6
    integration_flows: 2
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0

  traceability_present: true
  integration_flows_identified: true
  exceptions_documented: true
  delivery_model_defined: true
  ddd_artifacts_ready: true
  raci_plus_defined: true
  ai_policy_defined: true
  artifact_registry_defined: true

  ready_for_bpmn: true
  process_bpmn_linked: true
  process_bpmn_approved: true
  ready_for_specify: true
```

## 7.3 SAP Extension Gate チェック
- [ ] stride lint PASS（Basic Design Gate + BPMN リンク済み）
- [x] coverage_policy 方針定義済み
- [ ] basic_design_completeness_validator PASS
- [ ] catalogs_consistency_validator PASS

> End of basic_design.md (SAP Extension Pack v2 — IF-IN-001 EDI出荷報告データ取込)
