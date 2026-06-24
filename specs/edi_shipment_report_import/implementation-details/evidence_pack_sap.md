# SAP Evidence Pack Extension - FEAT-XXX

```yaml
evidence_pack_sap:
  extends: "specs/XXX_feature_name/implementation-details/evidence_pack.md"
  category_mapping_ref: "extensions/sap/templates/evidence_pack_category_mapping.yaml"

  sap_object_status: []
  # - type: "program"
  #   name: "ZXXX"
  #   status: "pending"
  #   syntax_check: "pending"
  #   activation: "pending"
  #   transport_request: ""

  s_evidence:
    scenarios: []
    # - test_id: "TS-XXX-01"
    #   name: ""
    #   type: "se38"
    #   screenshot_dir: "specs/XXX_feature_name/tests/reports/screenshots/TS-XXX-01/"
    #   screenshot_count: 0
    #   test_green_confirmation: false

  test_green_confirmation:
    unit_test:
      all_passed: false
      count: 0
    gui_test:
      all_passed: false
      count: 0
    all_passed: false        # unit_test.all_passed AND gui_test.all_passed
    confirmed_at: ""
```
