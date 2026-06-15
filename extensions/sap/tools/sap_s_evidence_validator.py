"""
sap_s_evidence_validator.py — S-Evidence 検証ツール

evidence_pack_sap.md の s_evidence セクションと plan.md の evidence_capture 定義を
突合し、正式エビデンスの完全性を検証する。

検証内容:
- s_evidence セクションの存在
- 各シナリオ（test_id 単位）のスクショ取得状況
- plan.md の evidence_capture.scenarios に定義された全 test_id がカバーされているか
- test_green_confirmation の全フラグが true か

stride-lint のエクステンションツールとして MANIFEST.yaml に宣言し、自動実行される。
インターフェース: validate_sap_s_evidence(feature_path, approval_status, coverage_tier)
                  -> (errors, warnings)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent))
from sap_evidence_common import load_yaml_from_md as _load_yaml


def validate_sap_s_evidence(
    feature_path: str | Path,
    approval_status: dict[str | int, bool],
    coverage_tier: str,
) -> tuple[list[tuple[str, str, list[str]]], list[tuple[str, str, list[str]]]]:
    """
    S-Evidence の完全性を検証する。

    Returns:
        (errors, warnings) — 各要素は (error_code, message, details) のタプル
    """
    errors: list[tuple[str, str, list[str]]] = []
    warnings: list[tuple[str, str, list[str]]] = []

    fp = Path(feature_path)

    # チェックボックス → YAML 同期 + S-Evidence テーブル生成
    # lint 実行のたびに最新状態を反映し、テーブルを再生成する
    plan_md_path = fp / "plan.md"
    if plan_md_path.is_file():
        try:
            from sap_evidence_table_generator import sync_manual_waived_from_checkboxes
            sync_manual_waived_from_checkboxes(plan_md_path)
        except Exception:
            pass  # 同期失敗は致命的ではない
        try:
            from sap_evidence_table_generator import update_plan_md
            update_plan_md(plan_md_path)
        except Exception:
            pass  # テーブル生成失敗は致命的ではない

    # spec.md ビュー自動再生成
    spec_md_path = fp / "spec.md"
    if spec_md_path.is_file():
        try:
            from sap_spec_view_generator import update_spec_md
            update_spec_md(spec_md_path)
        except Exception:
            pass

    # plan.md の S-Evidence サマリ表の生成チェック
    plan_md_path = fp / "plan.md"
    if plan_md_path.is_file():
        import re
        plan_text = plan_md_path.read_text(encoding="utf-8")
        start = "<!-- S-EVIDENCE-TABLE-START -->"
        end = "<!-- S-EVIDENCE-TABLE-END -->"
        if start in plan_text and end in plan_text:
            table_content = plan_text.split(start)[1].split(end)[0]
            if "| Test ID |" not in table_content:
                warnings.append((
                    "S_EVIDENCE_TABLE_NOT_GENERATED",
                    "plan.md の S-Evidence サマリ表が未生成です。"
                    "`python3 extensions/sap/tools/sap_evidence_table_generator.py "
                    f"{plan_md_path}` を実行してください",
                    [],
                ))

    # --- plan.md test_scenarios.scenarios 空チェック（統合構造） ---
    if plan_md_path.is_file():
        plan_doc_for_ec = _load_yaml(plan_md_path)
        plan_strat = plan_doc_for_ec.get("plan", {}).get("test_strategy", {})
        # 統合構造: test_scenarios.scenarios を優先、旧 evidence_capture.scenarios はフォールバック
        ts_scenarios = plan_strat.get("test_scenarios", {}).get("scenarios") or []
        ec_scenarios = plan_strat.get("evidence_capture", {}).get("scenarios") or []
        scenarios = ts_scenarios if ts_scenarios else ec_scenarios
        filled_sc = [s for s in scenarios if s.get("id") or s.get("test_id")]
        if not filled_sc:
            warnings.append((
                "S_EVIDENCE_SCENARIOS_EMPTY",
                "plan.md の test_scenarios.scenarios が未記入です。"
                "テストシナリオ（SC-01 等）を定義してください",
                [],
            ))

        # シナリオごとの type + se16_checks 整合チェック
        for sc in filled_sc:
            sc_id = sc.get("test_id", "?")
            sc_type = sc.get("type", "")
            se16 = sc.get("se16_checks") or {}
            pre = se16.get("pre") or []
            post = se16.get("post") or []

            if not sc_type:
                warnings.append((
                    "EVIDENCE_CAPTURE_TYPE_MISSING",
                    f"シナリオ '{sc_id}' の type が未設定です。"
                    f"update | reference | ui_only のいずれかを設定してください",
                    [],
                ))
            elif sc_type == "reference" and not pre:
                warnings.append((
                    "EVIDENCE_CAPTURE_PRE_MISSING",
                    f"シナリオ '{sc_id}' (type: reference) に se16_checks.pre が未設定です。"
                    f"参照データの存在確認・結果突合のために pre を定義してください",
                    [],
                ))
            elif sc_type == "update":
                if not pre:
                    warnings.append((
                        "EVIDENCE_CAPTURE_PRE_MISSING",
                        f"シナリオ '{sc_id}' (type: update) に se16_checks.pre が未設定です",
                        [],
                    ))
                if not post:
                    warnings.append((
                        "EVIDENCE_CAPTURE_POST_MISSING",
                        f"シナリオ '{sc_id}' (type: update) に se16_checks.post が未設定です。"
                        f"変更後のデータ状態を確認するために post を定義してください",
                        [],
                    ))

        # auto テストに対応する evidence_capture.scenario が存在するかチェック
        plan_tests_all = plan_strat.get("tests") or []
        scenario_test_ids = set()
        for sc in filled_sc:
            scenario_test_ids.add(sc.get("test_id", ""))
            for cid in sc.get("covers_test_ids") or []:
                scenario_test_ids.add(cid)

        for test in plan_tests_all:
            test_id = test.get("id", "")
            s_ev = test.get("s_evidence") or {}
            method = s_ev.get("method", "")
            if method == "auto" and test_id not in scenario_test_ids:
                warnings.append((
                    "EVIDENCE_SCENARIO_MISSING_FOR_AUTO_TEST",
                    f"テスト '{test_id}' (method: auto) に対応する evidence_capture.scenario がありません。"
                    f"sap_scenario_generator.py を実行してテストシナリオを生成してください",
                    [],
                ))

        # manual_required テストの判断状態検証
        plan_tests_for_waived = plan_strat.get("tests") or []
        for test in plan_tests_for_waived:
            s_ev = test.get("s_evidence") or {}
            if s_ev.get("method") != "manual_required":
                continue
            test_id = test.get("id", "?")
            is_manual = s_ev.get("manual_test_manual", False)
            is_waived = s_ev.get("manual_test_waived", False)
            waive_reason = (s_ev.get("waive_reason") or "").strip()

            # 両方ON は矛盾
            if is_manual and is_waived:
                errors.append((
                    "MANUAL_BOTH_CHECKED",
                    f"テスト '{test_id}' の manual_test_manual と manual_test_waived が両方 true です。片方のみを選択してください",
                    [],
                ))
            # waived=true なのに理由なし
            elif is_waived and not waive_reason:
                errors.append((
                    "MANUAL_WAIVED_NO_REASON",
                    f"テスト '{test_id}' が manual_test_waived=true ですが waive_reason が未記載です",
                    [],
                ))
            # 両方OFF（未判断）は警告
            elif not is_manual and not is_waived:
                warnings.append((
                    "MANUAL_NOT_DECIDED",
                    f"テスト '{test_id}' の manual/waived 判断が未実施です。Gate 4 承認前に判断してください",
                    [],
                ))

    # evidence_pack_sap.md を探す
    evidence_sap_path = fp / "implementation-details" / "evidence_pack_sap.md"
    if not evidence_sap_path.is_file():
        return errors, warnings

    evidence_doc = _load_yaml(evidence_sap_path)
    ep = evidence_doc.get("evidence_pack_sap", {})

    # s_evidence セクションの存在チェック
    s_evidence = ep.get("s_evidence")
    if not s_evidence:
        errors.append((
            "S_EVIDENCE_MISSING",
            "evidence_pack_sap.md に s_evidence セクションがありません。"
            "期待形式: evidence_pack_sap: > s_evidence: > scenarios: [...] "
            "（stride init でスキャフォールドされたテンプレートを使用してください）",
            [],
        ))
        return errors, warnings

    # s_evidence.scenarios が空でないこと
    scenarios = s_evidence.get("scenarios") or []
    if not scenarios:
        errors.append((
            "S_EVIDENCE_SCENARIOS_EMPTY",
            "s_evidence.scenarios が空です。evidence_capture.js を実行してください",
            [],
        ))
        return errors, warnings

    # 各シナリオのスクショ取得状況チェック
    for sc in scenarios:
        test_id = sc.get("test_id", "unknown")
        ss_count = sc.get("screenshot_count", 0)
        if not ss_count or ss_count <= 0:
            errors.append((
                "S_EVIDENCE_SCREENSHOTS_MISSING",
                f"テストケース '{test_id}' のスクリーンショットが未取得です",
                [],
            ))

    # test_green_confirmation チェック（v2 構造: unit_test.all_passed / gui_test.all_passed / all_passed）
    tgc = ep.get("test_green_confirmation", {})
    unit_test = tgc.get("unit_test", {})
    gui_test = tgc.get("gui_test", {})
    if not unit_test.get("all_passed"):
        errors.append((
            "SE_TEST_GREEN_NOT_CONFIRMED",
            "ABAP Unit テストの GREEN 確認が未完了です (unit_test.all_passed: false)",
            [],
        ))
    if not gui_test.get("all_passed"):
        errors.append((
            "SE_TEST_GREEN_NOT_CONFIRMED",
            "GUI テストの GREEN 確認が未完了です (gui_test.all_passed: false)",
            [],
        ))
    if not tgc.get("all_passed"):
        errors.append((
            "SE_TEST_GREEN_NOT_CONFIRMED",
            "テスト全体の GREEN 確認が未完了です (all_passed: false)",
            [],
        ))

    # plan.md の test_strategy を取得
    plan_path = fp / "plan.md"
    plan_doc = _load_yaml(plan_path)
    plan_strategy = plan_doc.get("plan", {}).get("test_strategy", {})

    plan_evidence = plan_strategy.get("evidence_capture", {})
    plan_scenarios = plan_evidence.get("scenarios") or []

    if plan_scenarios:
        evidence_test_ids = {
            (sc.get("test_id") or "").upper() for sc in scenarios
        }
        for ps in plan_scenarios:
            ps_test_id = (ps.get("test_id") or "").upper()
            if ps_test_id and ps_test_id not in evidence_test_ids:
                errors.append((
                    "S_EVIDENCE_SCENARIO_NOT_COVERED",
                    f"plan.md で定義されたテストケース '{ps_test_id}' の証跡が未取得です",
                    [],
                ))

    # --- D-1: tests[] の s_evidence フィールドと evidence_capture.scenarios の突合 ---
    plan_tests = plan_strategy.get("tests") or []

    if plan_tests:
        # evidence_capture.scenarios の covers_test_ids を収集
        covered_test_ids = set()
        scenarios_without_covers = []
        for ps in plan_scenarios:
            covers = ps.get("covers_test_ids") or []
            if covers:
                for tid in covers:
                    covered_test_ids.add(tid.upper())
            else:
                # 後方互換: test_id 自体が tests[] の ID と一致する場合は暗黙的にカバー
                ps_tid = (ps.get("test_id") or "").upper()
                covered_test_ids.add(ps_tid)

        # 各テストの s_evidence 定義を検証
        for test in plan_tests:
            test_id = (test.get("id") or "").upper()
            if not test_id:
                continue

            s_ev = test.get("s_evidence") or {}
            method = s_ev.get("method", "")
            reason = s_ev.get("reason", "")

            if not s_ev:
                # s_evidence 未定義
                warnings.append((
                    "S_EVIDENCE_NOT_DEFINED",
                    f"テスト '{test_id}' に s_evidence が定義されていません。"
                    f"method: auto | manual_required を設定してください",
                    [],
                ))
            elif method == "auto":
                # auto: evidence_capture.scenarios に対応シナリオが必要
                if test_id not in covered_test_ids:
                    errors.append((
                        "S_EVIDENCE_TEST_NOT_COVERED",
                        f"テスト '{test_id}' (s_evidence.method: auto) に対応する S-Evidence シナリオがありません。"
                        f"evidence_capture.scenarios に covers_test_ids: [\"{test_id}\"] を含むシナリオを追加してください",
                        [],
                    ))
            elif method == "manual_required":
                # manual_required: reason が必須
                if not reason.strip():
                    errors.append((
                        "S_EVIDENCE_MANUAL_REASON_MISSING",
                        f"テスト '{test_id}' (s_evidence.method: manual_required) に reason が記載されていません。"
                        f"自動取得不可の理由と対応方針を記載してください",
                        [],
                    ))
            else:
                # 不明な method
                warnings.append((
                    "S_EVIDENCE_UNKNOWN_METHOD",
                    f"テスト '{test_id}' の s_evidence.method '{method}' は不明です。"
                    f"auto | manual_required のいずれかを設定してください",
                    [],
                ))

    # --- H-2: 更新系プログラムの se16_checks.post 必須チェック ---
    basic_path = fp / "basic_design.md"
    if basic_path.is_file():
        basic_doc = _load_yaml(basic_path)
        basic = basic_doc.get("basic_design", {})
        scope_in = basic.get("scope", {}).get("in") or []
        scope_out = basic.get("scope", {}).get("out") or []
        scope_in_text = " ".join(scope_in) if isinstance(scope_in, list) else str(scope_in)
        scope_out_text = " ".join(scope_out) if isinstance(scope_out, list) else str(scope_out)

        import re as _re
        is_readonly = _re.search(
            r"照会のみ|参照のみ|read.only|データの更新.*行わない|更新.*対象外",
            scope_out_text + scope_in_text, _re.IGNORECASE
        )
        plan_full = plan_doc.get("plan", {})
        db_tables = plan_full.get("contracts", {}).get("database", {}).get("tables") or []
        has_write = any(
            any(op in ("INSERT", "UPDATE", "DELETE", "MODIFY") for op in (t.get("operations") or []))
            for t in db_tables
        )

        if has_write and not is_readonly:
            for ps in plan_scenarios:
                post_checks = (ps.get("se16_checks") or {}).get("post") or []
                if not post_checks:
                    sc_id = ps.get("test_id", "?")
                    warnings.append((
                        "UPDATE_POST_CHECK_MISSING",
                        f"更新系プログラムのシナリオ '{sc_id}' に se16_checks.post が定義されていません。"
                        f"更新後のデータ状態を SE16N で確認するために post チェックを追加してください",
                        [],
                    ))

    # --- G-3: spec 変更時のテスト更新強制 ---
    spec_path = fp / "spec.md"
    if spec_path.is_file() and plan_path.is_file():
        spec_mtime = spec_path.stat().st_mtime
        plan_mtime = plan_path.stat().st_mtime
        if spec_mtime > plan_mtime:
            warnings.append((
                "SPEC_NEWER_THAN_PLAN",
                "spec.md が plan.md より新しいです。spec 変更に伴いテストシナリオの更新が必要な可能性があります。"
                "plan.md tests[] と evidence_capture.scenarios を確認してください",
                [],
            ))

    # --- G-4: エビデンスとコードバージョンの紐付け ---
    # evidence_pack_sap.md の sap_object_status と実際のソースファイルのハッシュを比較
    import hashlib
    sap_objects = ep.get("sap_object_status") or []
    src_dir = fp.parents[1] / "src"
    for obj in sap_objects:
        obj_name = (obj.get("name") or "").upper()
        obj_status = obj.get("status", "")
        if obj_status == "active" and obj_name:
            # ソースファイルを探す
            for src_file in src_dir.rglob(f"{obj_name}.*abap"):
                current_hash = hashlib.sha256(src_file.read_bytes()).hexdigest()[:16]
                recorded_hash = obj.get("source_hash", "")
                if recorded_hash and recorded_hash != current_hash:
                    warnings.append((
                        "EVIDENCE_CODE_MISMATCH",
                        f"オブジェクト '{obj_name}' のソースが S-Evidence 取得後に変更されています "
                        f"(記録: {recorded_hash}, 現在: {current_hash})。"
                        f"S-Evidence の再取得が必要です",
                        [],
                    ))
                break

    # --- G-5: 環境依存テストの前提条件注意喚起 ---
    manual_tests = [
        t for t in plan_tests
        if (t.get("s_evidence") or {}).get("method") == "manual_required"
    ]
    if manual_tests:
        test_ids = [t.get("id", "?") for t in manual_tests]
        warnings.append((
            "MANUAL_REQUIRED_TESTS_PRESENT",
            f"{len(manual_tests)} 件のテストが s_evidence.method: manual_required です ({', '.join(test_ids)})。"
            f"これらのテストは環境依存またはGUI再現困難なため、人間が前提条件を確認し対応方針を決定する必要があります",
            [],
        ))

    # --- H-5: シナリオ間の順序依存チェック ---
    scenario_ids = {(ps.get("test_id") or "").upper() for ps in plan_scenarios}
    for ps in plan_scenarios:
        depends_on = ps.get("depends_on") or []
        if isinstance(depends_on, str):
            depends_on = [depends_on]
        for dep in depends_on:
            if dep.upper() not in scenario_ids:
                errors.append((
                    "S_EVIDENCE_DEPENDENCY_NOT_FOUND",
                    f"シナリオ '{ps.get('test_id', '?')}' の depends_on '{dep}' が "
                    f"evidence_capture.scenarios に存在しません",
                    [],
                ))

    return errors, warnings
