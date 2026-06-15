"""Integration tests for stride_wi_sync.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from stride_wi_sync import parse_yaml_block, parse_issue_form, issue_to_work_item, work_item_to_md


class TestParseYamlBlock:
    def test_basic_yaml_block(self):
        body = (
            "Some preamble text\n\n"
            "```yaml\n"
            "wi_id: WI-TEST-001\n"
            "feature_id: FEAT-TEST\n"
            "title: Test work item\n"
            "complexity: M\n"
            "mode: confirm\n"
            "priority: high\n"
            "risk_flags:\n"
            "  - authz\n"
            "```\n"
            "\nSome trailing text"
        )
        data = parse_yaml_block(body)
        assert data["wi_id"] == "WI-TEST-001"
        assert data["feature_id"] == "FEAT-TEST"
        assert data["mode"] == "confirm"

    def test_empty_body(self):
        data = parse_yaml_block("")
        assert data == {} or data is None


class TestParseIssueForm:
    def test_section_parsing(self):
        body = (
            "### WI ID\n\nWI-FORM-001\n\n"
            "### Feature\n\nFEAT-FORM\n\n"
            "### Title\n\nForm-based work item\n\n"
            "### Complexity\n\nL\n\n"
            "### Mode\n\nvalidate\n\n"
            "### Priority\n\nhigh\n\n"
            "### Risk Flags\n\n- sod\n- authz\n"
        )
        data = parse_issue_form(body)
        # parse_issue_form may use different key names
        assert data.get("wi_id") == "WI-FORM-001"
        assert data.get("complexity") == "L"


class TestIssueToWorkItem:
    def test_converts_issue_dict(self):
        issue = {
            "number": 42,
            "title": "WI-CONV-001: Convert test",
            "body": (
                "```yaml\n"
                "wi_id: WI-CONV-001\n"
                "feature_id: FEAT-CONV\n"
                "title: Convert test\n"
                "complexity: S\n"
                "mode: autopilot\n"
                "priority: normal\n"
                "```\n"
            ),
            "url": "https://github.com/test/issues/42",
            "state": "open",
            "assignees": [{"login": "tester"}],
            "labels": [{"name": "work-item"}],
        }
        wi = issue_to_work_item(issue)
        assert wi.wi_id == "WI-CONV-001"
        assert wi.feature_id == "FEAT-CONV"
        assert wi.issue_number == 42


class TestWorkItemToMd:
    def test_renders_markdown(self):
        issue = {
            "number": 1,
            "title": "WI-MD-001: MD test",
            "body": "```yaml\nwi_id: WI-MD-001\nfeature_id: FEAT-MD\ntitle: MD test\ncomplexity: S\nmode: autopilot\npriority: normal\n```\n",
            "url": "https://github.com/t/1",
            "state": "open",
            "assignees": [],
            "labels": [{"name": "work-item"}],
        }
        wi = issue_to_work_item(issue)
        md = work_item_to_md(wi)
        assert "WI-MD-001" in md
        assert "FEAT-MD" in md
        assert "---" in md  # YAML frontmatter


class TestDryRunDoesNotWrite:
    def test_main_dry_run_does_not_create_files(self, wi_sync_project, monkeypatch, capsys):
        """main() with --dry-run + mocked gh does not write WI files."""
        import stride_wi_sync as sws

        mock_issues = [
            {
                "number": 99,
                "title": "WI-DRY-001: Dry run test",
                "body": "```yaml\nwi_id: WI-DRY-001\nfeature_id: FEAT-SYNC\ntitle: Dry run\ncomplexity: S\nmode: autopilot\npriority: normal\n```\n",
                "url": "https://github.com/t/99",
                "state": "open",
                "assignees": [],
                "labels": [{"name": "work-item"}],
            },
        ]

        monkeypatch.setattr(sws, "get_repo", lambda: "test/repo")
        monkeypatch.setattr(sws, "fetch_issues", lambda repo, label="work-item", state="all": mock_issues)
        monkeypatch.setattr("sys.argv", ["stride_wi_sync", "--dry-run"])
        monkeypatch.chdir(wi_sync_project)

        sws.main()

        captured = capsys.readouterr()
        assert "[dry-run]" in captured.out
        # WI file should NOT have been written
        wi_file = wi_sync_project / "specs" / "FEAT-SYNC" / "work_items" / "WI-DRY-001.md"
        assert not wi_file.exists(), f"dry-run should not create {wi_file}"


class TestFeatureFilter:
    def test_filter_includes_matching_feature(self):
        """Issues with matching feature_id are included by filter."""
        issues = [
            {"number": 1, "title": "WI-A-001", "body": "```yaml\nwi_id: WI-A-001\nfeature_id: FEAT-ALPHA\ntitle: A\ncomplexity: S\nmode: autopilot\npriority: normal\n```\n",
             "url": "u", "state": "open", "assignees": [], "labels": [{"name": "work-item"}]},
            {"number": 2, "title": "WI-B-001", "body": "```yaml\nwi_id: WI-B-001\nfeature_id: FEAT-BETA\ntitle: B\ncomplexity: S\nmode: autopilot\npriority: normal\n```\n",
             "url": "u", "state": "open", "assignees": [], "labels": [{"name": "work-item"}]},
        ]
        work_items = [issue_to_work_item(i) for i in issues]
        # Simulate feature filter (as main() does)
        filtered = [wi for wi in work_items if wi.feature_id == "FEAT-ALPHA"]
        assert len(filtered) == 1
        assert filtered[0].wi_id == "WI-A-001"

    def test_filter_excludes_non_matching(self):
        """Issues with different feature_id are excluded."""
        issue = {
            "number": 3, "title": "WI-C-001",
            "body": "```yaml\nwi_id: WI-C-001\nfeature_id: FEAT-GAMMA\ntitle: C\ncomplexity: S\nmode: autopilot\npriority: normal\n```\n",
            "url": "u", "state": "open", "assignees": [], "labels": [{"name": "work-item"}],
        }
        wi = issue_to_work_item(issue)
        filtered = [wi] if wi.feature_id == "FEAT-DELTA" else []
        assert len(filtered) == 0
