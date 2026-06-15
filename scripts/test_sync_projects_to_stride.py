#!/usr/bin/env python3
"""
Unit tests for sync_projects_to_stride.py (Reverse Sync)

Tests:
1. state.yaml スキーマ整合性（work_items 配列形式）
2. --prefer file が Status を含めて競合扱いにする
3. state.yaml の mtime が競合検出に反映される
"""

import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

import yaml
from sync_projects_to_stride import (
    update_state_yaml,
    detect_conflict,
    _get_status_from_state,
    _map_project_status_to_state,
    _normalize_work_items,
    sync_project_item_to_file,
    parse_work_item_file,
)


class TestStateYamlSchema(unittest.TestCase):
    """Test state.yaml uses correct schema (work_items array, not work_items_status dict)"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmpdir) / "specs" / "test_feature"
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "state").mkdir()
        (self.feature_dir / "work_items").mkdir()

    def test_update_state_yaml_creates_array_format(self):
        """Test that update_state_yaml uses work_items array format"""
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
feature: test
work_items:
  - wi_id: WI-001
    status: pending
""")
        result = update_state_yaml(self.feature_dir, "WI-001", "in_progress", dry_run=False)

        self.assertIn("status: pending → in_progress", result.get("changes", []))

        # Verify the file content
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # Should be array format, not dict
        self.assertIsInstance(state["work_items"], list)
        self.assertEqual(state["work_items"][0]["wi_id"], "WI-001")
        self.assertEqual(state["work_items"][0]["status"], "in_progress")

    def test_update_state_yaml_adds_new_wi(self):
        """Test that new WI is added to work_items array"""
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
feature: test
work_items:
  - wi_id: WI-001
    status: pending
""")
        result = update_state_yaml(self.feature_dir, "WI-002", "in_progress", dry_run=False)

        with open(state_file) as f:
            state = yaml.safe_load(f)

        self.assertEqual(len(state["work_items"]), 2)
        self.assertEqual(state["work_items"][1]["wi_id"], "WI-002")
        self.assertEqual(state["work_items"][1]["status"], "in_progress")

    def test_get_status_from_state(self):
        """Test _get_status_from_state reads from work_items array"""
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
work_items:
  - wi_id: WI-001
    status: in_progress
  - wi_id: WI-002
    status: done
""")
        self.assertEqual(_get_status_from_state(self.feature_dir, "WI-001"), "in_progress")
        self.assertEqual(_get_status_from_state(self.feature_dir, "WI-002"), "done")
        self.assertIsNone(_get_status_from_state(self.feature_dir, "WI-999"))


class TestPreferFileIncludesStatus(unittest.TestCase):
    """Test --prefer file blocks status updates when there's a conflict"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmpdir) / "specs" / "test_feature"
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "state").mkdir()
        (self.feature_dir / "work_items").mkdir()

    def test_conflict_detection_includes_status(self):
        """Test that status difference is detected as conflict"""
        # Create WI file
        wi_file = self.feature_dir / "work_items" / "WI-001.md"
        wi_file.write_text("""---
wi_id: WI-001
title: Test
mode: autopilot
complexity: low
risk_flags: []
---
# Content
""")

        # Create state.yaml with different status
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
work_items:
  - wi_id: WI-001
    status: done
""")

        # Project item has different status
        project_item = {
            "updatedAt": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            "fields": {
                "WI ID": "WI-001",
                "Mode": "autopilot",
                "Complexity": "low",
                "Status": "in_progress",  # Different from state.yaml
            },
        }

        result = detect_conflict(wi_file, project_item, self.feature_dir, include_status=True)

        self.assertTrue(result["conflict"])
        self.assertTrue(any("status" in d for d in result.get("differences", [])))

    def test_prefer_file_skips_all_updates(self):
        """Test that --prefer file skips status updates when conflict detected"""
        wi_file = self.feature_dir / "work_items" / "WI-001.md"
        wi_file.write_text("""---
wi_id: WI-001
title: Test
mode: autopilot
complexity: low
risk_flags: []
---
# Content
""")

        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
work_items:
  - wi_id: WI-001
    status: done
""")

        project_item = {
            "updatedAt": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            "fields": {
                "WI ID": "WI-001",
                "Mode": "confirm",  # Different mode
                "Complexity": "low",
                "Status": "in_progress",  # Different status
            },
        }

        result = sync_project_item_to_file(project_item, self.feature_dir, prefer="file", dry_run=False)

        self.assertTrue(result.get("skipped"))
        self.assertEqual(result.get("reason"), "prefer_file")

        # Verify state.yaml was NOT changed
        with open(state_file) as f:
            state = yaml.safe_load(f)
        self.assertEqual(state["work_items"][0]["status"], "done")


class TestStateYamlMtimeInConflict(unittest.TestCase):
    """Test state.yaml mtime is considered in conflict detection"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmpdir) / "specs" / "test_feature"
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "state").mkdir()
        (self.feature_dir / "work_items").mkdir()

    def test_state_yaml_mtime_affects_conflict(self):
        """Test that newer state.yaml makes file_newer=True"""
        import os
        import time

        # Create WI file (old)
        wi_file = self.feature_dir / "work_items" / "WI-001.md"
        wi_file.write_text("""---
wi_id: WI-001
title: Test
mode: autopilot
complexity: low
risk_flags: []
---
# Content
""")

        # Make WI file old
        old_time = time.time() - 7200  # 2 hours ago
        os.utime(wi_file, (old_time, old_time))

        # Create state.yaml (recent)
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
work_items:
  - wi_id: WI-001
    status: done
""")

        # Project item from 1 hour ago
        project_item = {
            "updatedAt": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            "fields": {
                "WI ID": "WI-001",
                "Mode": "confirm",
                "Complexity": "low",
                "Status": "in_progress",
            },
        }

        result = detect_conflict(wi_file, project_item, self.feature_dir, include_status=True)

        # state.yaml is newer than project, so file_newer should be True
        self.assertTrue(result["conflict"])
        self.assertTrue(result["file_newer"])


class TestStatusMapping(unittest.TestCase):
    """Test status mapping from Projects to state.yaml"""

    def test_map_project_status_to_state(self):
        """Test all status mappings"""
        self.assertEqual(_map_project_status_to_state("pending_pre_approval"), "pending")
        self.assertEqual(_map_project_status_to_state("in_progress"), "in_progress")
        self.assertEqual(_map_project_status_to_state("pending_walkthrough"), "in_progress")
        self.assertEqual(_map_project_status_to_state("pending_ci"), "in_progress")
        self.assertEqual(_map_project_status_to_state("pending_ops"), "in_progress")
        self.assertEqual(_map_project_status_to_state("done"), "done")
        # Unknown status passes through
        self.assertEqual(_map_project_status_to_state("custom"), "custom")


class TestPreferAutoProjectNewer(unittest.TestCase):
    """Test --prefer auto correctly updates when Project is newer"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmpdir) / "specs" / "test_feature"
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "state").mkdir()
        (self.feature_dir / "work_items").mkdir()

    def test_prefer_auto_updates_when_project_newer(self):
        """Test --prefer auto updates status when Project is newer than file"""
        import os
        import time

        # Create WI file (old)
        wi_file = self.feature_dir / "work_items" / "WI-001.md"
        wi_file.write_text("""---
wi_id: WI-001
title: Test
mode: autopilot
complexity: low
risk_flags: []
---
# Content
""")
        # Make WI file old
        old_time = time.time() - 7200  # 2 hours ago
        os.utime(wi_file, (old_time, old_time))

        # Create state.yaml (also old)
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
work_items:
  - wi_id: WI-001
    status: pending
    mode: autopilot
""")
        os.utime(state_file, (old_time, old_time))

        # Project item is more recent (30 minutes ago)
        project_item = {
            "updatedAt": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
            "fields": {
                "WI ID": "WI-001",
                "Mode": "autopilot",
                "Complexity": "low",
                "Status": "done",  # Changed in Projects
            },
        }

        result = sync_project_item_to_file(project_item, self.feature_dir, prefer="auto", dry_run=False)

        # Should have updated (not skipped) because Project is newer
        self.assertFalse(result.get("skipped", False), f"Should not be skipped: {result}")
        self.assertTrue(any("State" in c for c in result.get("changes", [])))

        # Verify state.yaml was updated
        with open(state_file) as f:
            state = yaml.safe_load(f)
        self.assertEqual(state["work_items"][0]["status"], "done")


class TestUpdateStateYamlWithMode(unittest.TestCase):
    """Test update_state_yaml includes mode when adding new WI"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmpdir) / "specs" / "test_feature"
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "state").mkdir()

    def test_new_wi_includes_mode(self):
        """Test that new WI added to state.yaml includes mode"""
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
feature: test
work_items: []
""")
        result = update_state_yaml(
            self.feature_dir,
            "WI-NEW-001",
            "in_progress",
            mode="validate",
            dry_run=False
        )

        self.assertTrue(result.get("changes"))

        # Verify the mode was saved
        with open(state_file) as f:
            state = yaml.safe_load(f)

        self.assertEqual(len(state["work_items"]), 1)
        self.assertEqual(state["work_items"][0]["wi_id"], "WI-NEW-001")
        self.assertEqual(state["work_items"][0]["status"], "in_progress")
        self.assertEqual(state["work_items"][0]["mode"], "validate")

    def test_existing_wi_mode_updated_from_projects(self):
        """Test that existing WI mode is updated from Projects (source of truth)"""
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
feature: test
work_items:
  - wi_id: WI-001
    status: pending
    mode: validate
""")
        # Projects says mode=autopilot (synced from WI file via Forward sync)
        result = update_state_yaml(
            self.feature_dir,
            "WI-001",
            "done",
            mode="autopilot",  # From Projects - should update state.yaml
            dry_run=False
        )

        # Verify mode was updated to match Projects (and thus WI file)
        with open(state_file) as f:
            state = yaml.safe_load(f)

        self.assertEqual(state["work_items"][0]["status"], "done")
        self.assertEqual(state["work_items"][0]["mode"], "autopilot")  # Updated from Projects
        self.assertTrue(any("mode:" in c for c in result.get("changes", [])))


class TestOldSchemaMigration(unittest.TestCase):
    """Test automatic migration of old schema (string array) to new schema (dict array)"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmpdir) / "specs" / "test_feature"
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "state").mkdir()

    def test_normalize_string_array(self):
        """Test _normalize_work_items converts string array to dict array"""
        old_format = ["WI-001", "WI-002", "WI-003"]
        normalized, changes = _normalize_work_items(old_format, default_mode="autopilot")

        self.assertEqual(len(changes), 3)
        self.assertTrue(any("WI-001" in c for c in changes))
        self.assertEqual(len(normalized), 3)
        self.assertEqual(normalized[0]["wi_id"], "WI-001")
        self.assertEqual(normalized[0]["status"], "pending")
        self.assertEqual(normalized[0]["mode"], "autopilot")

    def test_normalize_mixed_array(self):
        """Test _normalize_work_items handles mixed array (strings + dicts)"""
        mixed = [
            "WI-001",  # Old format
            {"wi_id": "WI-002", "status": "done"},  # Missing mode
            {"wi_id": "WI-003", "status": "in_progress", "mode": "validate"},  # Complete
        ]
        normalized, changes = _normalize_work_items(mixed, default_mode="confirm")

        self.assertEqual(len(changes), 2)  # 1 string conversion + 1 mode補完
        self.assertEqual(len(normalized), 3)
        # String converted
        self.assertEqual(normalized[0]["wi_id"], "WI-001")
        self.assertEqual(normalized[0]["mode"], "confirm")
        # Missing mode補完
        self.assertEqual(normalized[1]["wi_id"], "WI-002")
        self.assertEqual(normalized[1]["mode"], "confirm")
        # Existing mode preserved
        self.assertEqual(normalized[2]["wi_id"], "WI-003")
        self.assertEqual(normalized[2]["mode"], "validate")

    def test_update_state_yaml_migrates_old_schema(self):
        """Test update_state_yaml auto-migrates old schema"""
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
feature: test
work_items:
  - WI-001
  - WI-002
""")
        result = update_state_yaml(
            self.feature_dir,
            "WI-001",
            "done",
            mode="autopilot",
            dry_run=False
        )

        # Should have schema conversion changes
        self.assertTrue(any("dict 形式に変換" in c for c in result.get("changes", [])))

        with open(state_file) as f:
            state = yaml.safe_load(f)

        # All items should be dicts now
        for wi in state["work_items"]:
            self.assertIsInstance(wi, dict)
            self.assertIn("wi_id", wi)
            self.assertIn("mode", wi)

    def test_mode_complement_for_existing_wi(self):
        """Test mode is補完 for existing WI missing mode"""
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
work_items:
  - wi_id: WI-001
    status: pending
""")  # No mode

        result = update_state_yaml(
            self.feature_dir,
            "WI-001",
            "in_progress",
            mode="confirm",
            dry_run=False
        )

        # Should have mode補完 change
        self.assertTrue(any("mode補完" in c for c in result.get("changes", [])))

        with open(state_file) as f:
            state = yaml.safe_load(f)
        self.assertEqual(state["work_items"][0]["mode"], "confirm")

    def test_default_mode_when_none_provided(self):
        """Test default mode 'autopilot' when mode is None"""
        state_file = self.feature_dir / "state" / "state.yaml"
        state_file.write_text("""
work_items: []
""")
        result = update_state_yaml(
            self.feature_dir,
            "WI-NEW",
            "pending_pre_approval",
            mode=None,  # No mode provided
            dry_run=False
        )

        with open(state_file) as f:
            state = yaml.safe_load(f)

        self.assertEqual(state["work_items"][0]["mode"], "autopilot")

    def test_current_wi_mode_does_not_affect_other_wis(self):
        """Test that current WI's mode doesn't propagate to other WIs during normalization"""
        state_file = self.feature_dir / "state" / "state.yaml"
        # Old schema with string array
        state_file.write_text("""
work_items:
  - WI-001
  - WI-002
  - WI-003
""")
        # Update WI-002 with mode=validate
        result = update_state_yaml(
            self.feature_dir,
            "WI-002",
            "in_progress",
            mode="validate",  # This should NOT affect WI-001 and WI-003
            dry_run=False
        )

        with open(state_file) as f:
            state = yaml.safe_load(f)

        # WI-001 and WI-003 should have autopilot (default), not validate
        wi_modes = {wi["wi_id"]: wi["mode"] for wi in state["work_items"]}
        self.assertEqual(wi_modes["WI-001"], "autopilot")  # Not validate!
        self.assertEqual(wi_modes["WI-002"], "validate")   # This one was specified
        self.assertEqual(wi_modes["WI-003"], "autopilot")  # Not validate!


if __name__ == "__main__":
    unittest.main(verbosity=2)
