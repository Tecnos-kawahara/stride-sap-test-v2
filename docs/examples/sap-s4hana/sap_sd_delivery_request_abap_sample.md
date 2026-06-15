# SAP SD 出庫依頼送信アドオン ABAP サンプル

このサンプルは、以下の成果物に整合する ABAP OO 実装イメージです。

- BPMN: [sap_sd_delivery_request_process.bpmn](/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/sap_sd_delivery_request_process.bpmn)
- Basic Design: [sap_sd_delivery_request_basic_design.md](/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/sap_sd_delivery_request_basic_design.md)
- EPIC Flow: [sap_sd_order_to_cash_epic_flow.bpmn](/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/sap_sd_order_to_cash_epic_flow.bpmn)

## 1. BPMN と ABAP の対応

| BPMN ID | BPMN Name | ABAP Method | 役割 |
|---|---|---|---|
| `BPMN-TASK-001` | 納品伝票生成 | `create_delivery_document` | ATP確定済み受注から納品伝票を作成 |
| `BPMN-TASK-002` | 出庫依頼データ組成 | `build_delivery_request` | WMS 向けペイロードを組成 |
| `BPMN-GW-001` | 手動確認要否 | `requires_manual_review` | 例外条件の判定 |
| `BPMN-TASK-003` | 出庫依頼内容確認 | `enqueue_manual_review` | 手動確認待ちへ移送 |
| `BPMN-TASK-004` | 倉庫連携メッセージ送信 | `send_to_wms` | WMS へ出庫依頼送信 |
| `BPMN-TASK-005` | 送信ACK受信 | `receive_ack` | ACK 取得 |
| `BPMN-GW-002` | ACK判定 | `handle_ack` | ACK 成否分岐 |
| `BPMN-TASK-006` | 出庫依頼状態更新 | `update_sent_status` | 送信済み更新 |
| `BPMN-TASK-007` | エラー記録・保留 | `hold_request` | 異常時保留 |

## 2. 想定する責務分割

- `ZCL_SD_DELIVERY_REQUEST_FLOW`
  - BPMN のアプリケーションサービス本体
- `ZIF_SD_WMS_GATEWAY`
  - WMS 送受信の抽象化
- `ZCL_SD_WMS_HTTP_GATEWAY`
  - HTTP/REST 連携実装例
- `ZCX_SD_DELIVERY_REQUEST`
  - 業務例外

## 3. ABAP サンプルコード

```abap
"------------------------------------------------------------
" Exception
"------------------------------------------------------------
CLASS zcx_sd_delivery_request DEFINITION
  PUBLIC
  INHERITING FROM cx_static_check
  FINAL.
  PUBLIC SECTION.
    DATA mv_message TYPE string READ-ONLY.
    METHODS constructor
      IMPORTING
        iv_message TYPE string.
ENDCLASS.

CLASS zcx_sd_delivery_request IMPLEMENTATION.
  METHOD constructor.
    super->constructor( ).
    mv_message = iv_message.
  ENDMETHOD.
ENDCLASS.

"------------------------------------------------------------
" Port for WMS integration
"------------------------------------------------------------
INTERFACE zif_sd_wms_gateway PUBLIC.
  TYPES:
    BEGIN OF ty_delivery_request,
      sales_order       TYPE vbeln_va,
      delivery_document TYPE vbeln_vl,
      shipping_point    TYPE vstel,
      plant             TYPE werks_d,
      route             TYPE route,
      requested_date    TYPE dats,
      split_delivery    TYPE abap_bool,
      dangerous_goods   TYPE abap_bool,
      alternate_wh      TYPE abap_bool,
      urgent_delivery   TYPE abap_bool,
    END OF ty_delivery_request,
    BEGIN OF ty_ack,
      transaction_id TYPE sysuuid_x16,
      ack_status     TYPE char20,
      ack_code       TYPE char20,
      ack_message    TYPE string,
    END OF ty_ack.

  METHODS send_delivery_request
    IMPORTING
      is_request TYPE ty_delivery_request
    RETURNING
      VALUE(rv_transaction_id) TYPE sysuuid_x16
    RAISING
      zcx_sd_delivery_request.

  METHODS poll_ack
    IMPORTING
      iv_transaction_id TYPE sysuuid_x16
    RETURNING
      VALUE(rs_ack) TYPE ty_ack
    RAISING
      zcx_sd_delivery_request.
ENDINTERFACE.

"------------------------------------------------------------
" Main application service aligned to BPMN
"------------------------------------------------------------
CLASS zcl_sd_delivery_request_flow DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    TYPES:
      BEGIN OF ty_context,
        sales_order          TYPE vbeln_va,
        delivery_document    TYPE vbeln_vl,
        shipping_point       TYPE vstel,
        transaction_id       TYPE sysuuid_x16,
        requires_review      TYPE abap_bool,
        ack_status           TYPE char20,
        ack_code             TYPE char20,
        process_status       TYPE char30,
      END OF ty_context.

    METHODS constructor
      IMPORTING
        io_wms_gateway TYPE REF TO zif_sd_wms_gateway.

    METHODS execute
      IMPORTING
        iv_sales_order TYPE vbeln_va
      RETURNING
        VALUE(rs_context) TYPE ty_context
      RAISING
        zcx_sd_delivery_request.

  PRIVATE SECTION.
    DATA mo_wms_gateway TYPE REF TO zif_sd_wms_gateway.

    METHODS create_delivery_document
      CHANGING
        cs_context TYPE ty_context
      RAISING
        zcx_sd_delivery_request.

    METHODS build_delivery_request
      IMPORTING
        is_context TYPE ty_context
      RETURNING
        VALUE(rs_request) TYPE zif_sd_wms_gateway=>ty_delivery_request
      RAISING
        zcx_sd_delivery_request.

    METHODS requires_manual_review
      IMPORTING
        is_request TYPE zif_sd_wms_gateway=>ty_delivery_request
      RETURNING
        VALUE(rv_required) TYPE abap_bool.

    METHODS enqueue_manual_review
      IMPORTING
        is_context TYPE ty_context
        is_request TYPE zif_sd_wms_gateway=>ty_delivery_request
      RAISING
        zcx_sd_delivery_request.

    METHODS send_to_wms
      IMPORTING
        is_request TYPE zif_sd_wms_gateway=>ty_delivery_request
      CHANGING
        cs_context TYPE ty_context
      RAISING
        zcx_sd_delivery_request.

    METHODS receive_ack
      CHANGING
        cs_context TYPE ty_context
      RAISING
        zcx_sd_delivery_request.

    METHODS handle_ack
      CHANGING
        cs_context TYPE ty_context
      RAISING
        zcx_sd_delivery_request.

    METHODS update_sent_status
      CHANGING
        cs_context TYPE ty_context
      RAISING
        zcx_sd_delivery_request.

    METHODS hold_request
      CHANGING
        cs_context TYPE ty_context
      RAISING
        zcx_sd_delivery_request.
ENDCLASS.

CLASS zcl_sd_delivery_request_flow IMPLEMENTATION.
  METHOD constructor.
    mo_wms_gateway = io_wms_gateway.
  ENDMETHOD.

  METHOD execute.
    rs_context-sales_order = iv_sales_order.

    " BPMN-TASK-001: 納品伝票生成
    create_delivery_document( CHANGING cs_context = rs_context ).

    DATA(ls_request) = build_delivery_request( is_context = rs_context ).

    " BPMN-GW-001: 手動確認要否
    rs_context-requires_review = requires_manual_review( ls_request ).
    IF rs_context-requires_review = abap_true.
      " BPMN-TASK-003: 出庫依頼内容確認
      enqueue_manual_review(
        EXPORTING
          is_context = rs_context
          is_request = ls_request
      ).
    ENDIF.

    " BPMN-TASK-004: 倉庫連携メッセージ送信
    send_to_wms(
      EXPORTING
        is_request = ls_request
      CHANGING
        cs_context = rs_context
    ).

    " BPMN-TASK-005: 送信ACK受信
    receive_ack( CHANGING cs_context = rs_context ).

    " BPMN-GW-002 + BPMN-TASK-006/007
    handle_ack( CHANGING cs_context = rs_context ).
  ENDMETHOD.

  METHOD create_delivery_document.
    DATA: lt_sales_order_items TYPE TABLE OF bapidlvreftosalesorder,
          lt_return           TYPE TABLE OF bapiret2,
          lv_delivery         TYPE vbeln_vl.

    APPEND VALUE #( ref_doc = cs_context-sales_order ) TO lt_sales_order_items.

    CALL FUNCTION 'BAPI_OUTB_DELIVERY_CREATE_SLS'
      IMPORTING
        delivery = lv_delivery
      TABLES
        sales_order_items = lt_sales_order_items
        return            = lt_return.

    READ TABLE lt_return WITH KEY type = 'E' TRANSPORTING NO FIELDS.
    IF sy-subrc = 0 OR lv_delivery IS INITIAL.
      RAISE EXCEPTION NEW zcx_sd_delivery_request(
        iv_message = |納品伝票生成に失敗しました。Sales Order={ cs_context-sales_order }|
      ).
    ENDIF.

    cs_context-delivery_document = lv_delivery.

    SELECT SINGLE vstel
      FROM likp
      INTO @cs_context-shipping_point
      WHERE vbeln = @cs_context-delivery_document.

    cs_context-process_status = 'DELIVERY_CREATED'.
  ENDMETHOD.

  METHOD build_delivery_request.
    DATA: ls_likp TYPE likp,
          lt_lips TYPE TABLE OF lips.

    SELECT SINGLE *
      FROM likp
      INTO @ls_likp
      WHERE vbeln = @is_context-delivery_document.

    IF sy-subrc <> 0.
      RAISE EXCEPTION NEW zcx_sd_delivery_request(
        iv_message = |LIKP not found for delivery { is_context-delivery_document }|
      ).
    ENDIF.

    SELECT *
      FROM lips
      INTO TABLE @lt_lips
      WHERE vbeln = @is_context-delivery_document.

    rs_request-sales_order       = is_context-sales_order.
    rs_request-delivery_document = is_context-delivery_document.
    rs_request-shipping_point    = ls_likp-vstel.
    rs_request-plant             = ls_likp-vkorg.
    rs_request-route             = ls_likp-route.
    rs_request-requested_date    = ls_likp-lfdat.

    " Sample rule mapping from custom conditions / extension fields
    rs_request-split_delivery  = xsdbool( lines( lt_lips ) > 10 ).
    rs_request-dangerous_goods = abap_false.
    rs_request-alternate_wh    = abap_false.
    rs_request-urgent_delivery = xsdbool( ls_likp-lfart = 'LF' AND ls_likp-lfdat = sy-datum ).
  ENDMETHOD.

  METHOD requires_manual_review.
    rv_required = xsdbool(
      is_request-dangerous_goods = abap_true OR
      is_request-split_delivery  = abap_true OR
      is_request-alternate_wh    = abap_true OR
      is_request-urgent_delivery = abap_true
    ).
  ENDMETHOD.

  METHOD enqueue_manual_review.
    INSERT zsd_delreq_log FROM VALUE #(
      delivery_document = is_context-delivery_document
      sales_order       = is_context-sales_order
      process_status    = 'REVIEW'
      detail_message    = 'Manual review required before WMS send'
      created_at        = sy-datum
      created_by        = sy-uname
    ).

    IF sy-subrc <> 0.
      RAISE EXCEPTION NEW zcx_sd_delivery_request(
        iv_message = |手動確認待ちログの登録に失敗しました。Delivery={ is_context-delivery_document }|
      ).
    ENDIF.
  ENDMETHOD.

  METHOD send_to_wms.
    cs_context-transaction_id = mo_wms_gateway->send_delivery_request( is_request = is_request ).

    UPDATE zsd_delreq_log
      SET process_status  = 'SENT'
          transaction_id  = cs_context-transaction_id
          changed_at      = sy-datum
          changed_by      = sy-uname
      WHERE delivery_document = cs_context-delivery_document.

    cs_context-process_status = 'SENT'.
  ENDMETHOD.

  METHOD receive_ack.
    DATA(ls_ack) = mo_wms_gateway->poll_ack( iv_transaction_id = cs_context-transaction_id ).

    cs_context-ack_status = ls_ack-ack_status.
    cs_context-ack_code   = ls_ack-ack_code.

    UPDATE zsd_delreq_log
      SET ack_status      = cs_context-ack_status
          ack_code        = cs_context-ack_code
          changed_at      = sy-datum
          changed_by      = sy-uname
      WHERE transaction_id = cs_context-transaction_id.
  ENDMETHOD.

  METHOD handle_ack.
    CASE cs_context-ack_status.
      WHEN 'ACCEPTED'.
        update_sent_status( CHANGING cs_context = cs_context ).
      WHEN OTHERS.
        hold_request( CHANGING cs_context = cs_context ).
    ENDCASE.
  ENDMETHOD.

  METHOD update_sent_status.
    UPDATE zsd_delreq_log
      SET process_status = 'ACK_ACCEPTED'
          changed_at     = sy-datum
          changed_by     = sy-uname
      WHERE transaction_id = cs_context-transaction_id.

    IF sy-subrc <> 0.
      RAISE EXCEPTION NEW zcx_sd_delivery_request(
        iv_message = |送信済み状態の更新に失敗しました。TX={ cs_context-transaction_id }|
      ).
    ENDIF.

    cs_context-process_status = 'ACK_ACCEPTED'.
  ENDMETHOD.

  METHOD hold_request.
    UPDATE zsd_delreq_log
      SET process_status = 'HOLD'
          detail_message = |ACK error: { cs_context-ack_status }/{ cs_context-ack_code }|
          changed_at     = sy-datum
          changed_by     = sy-uname
      WHERE transaction_id = cs_context-transaction_id.

    cs_context-process_status = 'HOLD'.

    " Sample: trigger application log / workflow / mail integration
    MESSAGE e398(00) WITH |Delivery request put on hold. TX={ cs_context-transaction_id }|.
  ENDMETHOD.
ENDCLASS.
```

## 4. WMS Gateway 実装例

```abap
CLASS zcl_sd_wms_http_gateway DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.
  PUBLIC SECTION.
    INTERFACES zif_sd_wms_gateway.
ENDCLASS.

CLASS zcl_sd_wms_http_gateway IMPLEMENTATION.
  METHOD zif_sd_wms_gateway~send_delivery_request.
    DATA(lv_uuid) = cl_system_uuid=>create_uuid_x16_static( ).

    " 実装例:
    " 1. /ui2/cl_json=>serialize で JSON 化
    " 2. cl_http_client で WMS API へ POST
    " 3. WMS の correlation id を transaction_id として保持
    rv_transaction_id = lv_uuid.
  ENDMETHOD.

  METHOD zif_sd_wms_gateway~poll_ack.
    " 実装例:
    " 1. transaction_id を使って WMS ACK API を GET
    " 2. 未応答なら TIMEOUT / PENDING 扱い
    " 3. 受理済みなら ACCEPTED を返す
    rs_ack-transaction_id = iv_transaction_id.
    rs_ack-ack_status     = 'ACCEPTED'.
    rs_ack-ack_code       = '200'.
    rs_ack-ack_message    = 'Accepted by WMS'.
  ENDMETHOD.
ENDCLASS.
```

## 5. 実行例

```abap
DATA(lo_gateway) = NEW zcl_sd_wms_http_gateway( ).
DATA(lo_flow)    = NEW zcl_sd_delivery_request_flow( io_wms_gateway = lo_gateway ).

TRY.
    DATA(ls_result) = lo_flow->execute( iv_sales_order = '0000123456' ).
    WRITE: / 'Delivery request flow finished:', ls_result-process_status.
  CATCH zcx_sd_delivery_request INTO DATA(lx_delreq).
    WRITE: / 'Delivery request flow failed:', lx_delreq->mv_message.
ENDTRY.
```

## 6. 実装上の注意

- `BAPI_OUTB_DELIVERY_CREATE_SLS` の呼び出しパラメータは、プロジェクトの受注/納品設計に合わせて調整が必要です。
- `plant` への値マッピングなど、一部は説明用の簡略化です。実案件では `LIKP/LIPS/VBAK/VBAP/TVST` のどこを正本にするかを明確にしてください。
- `ZSD_DELREQ_LOG` は監査・再送制御用のサンプルテーブルです。実際には application log (`BAL`) や workflow inbox 連携も合わせて設計した方が安全です。
- 手動確認 (`BPMN-TASK-003`) は ABAP ダイアログ、Fiori、Workflow inbox のどれで実現するかを別途決める必要があります。
- ACK 取得は同期 API でも非同期キューでもよいですが、BPMN の `BPMN-TASK-005` と `BPMN-GW-002` に対応する状態遷移は必ず残してください。
