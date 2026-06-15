#!/usr/bin/env python3
"""
GitHub Projects → STRIDE 逆方向同期スクリプト (Option B: Hybrid)

GitHub Projects の変更をローカルファイルに反映する。
ファイルが正本だが、Projects での状態変更も許可する。

Usage:
    python scripts/sync_projects_to_stride.py --feature specs/<feature>/
    python scripts/sync_projects_to_stride.py --wi-id WI-ERP-SAMPLE-001
    python scripts/sync_projects_to_stride.py --dry-run --feature specs/<feature>/

Environment:
    GH_TOKEN: GitHub Personal Access Token (project:read scope)
    GITHUB_PROJECT_NUMBER: Project番号 (e.g., 1)
    GITHUB_OWNER: Organization or User名

Conflict Resolution:
    - ファイルの mtime と Projects の updatedAt を比較
    - 新しい方を採用（--prefer-file / --prefer-projects で上書き可能）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests required. Install with: pip install requests")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

GITHUB_API_URL = "https://api.github.com/graphql"


def get_config() -> dict:
    """環境変数から設定を取得"""
    return {
        "token": os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"),
        "project_number": os.environ.get("GITHUB_PROJECT_NUMBER"),
        "owner": os.environ.get("GITHUB_OWNER"),
        "owner_type": os.environ.get("GITHUB_OWNER_TYPE", "organization"),
    }


# =============================================================================
# GitHub Projects API
# =============================================================================

def graphql_request(query: str, variables: dict, token: str) -> dict:
    """GraphQL リクエスト実行"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        GITHUB_API_URL,
        headers=headers,
        json={"query": query, "variables": variables},
    )
    response.raise_for_status()
    result = response.json()
    if "errors" in result:
        raise Exception(f"GraphQL errors: {result['errors']}")
    return result


def get_project_id(owner: str, project_number: int, token: str, owner_type: str = "organization") -> str:
    """Project ID を取得"""
    if owner_type == "organization":
        query = """
        query($owner: String!, $number: Int!) {
            organization(login: $owner) {
                projectV2(number: $number) {
                    id
                }
            }
        }
        """
        result = graphql_request(query, {"owner": owner, "number": project_number}, token)
        return result["data"]["organization"]["projectV2"]["id"]
    else:
        query = """
        query($owner: String!, $number: Int!) {
            user(login: $owner) {
                projectV2(number: $number) {
                    id
                }
            }
        }
        """
        result = graphql_request(query, {"owner": owner, "number": project_number}, token)
        return result["data"]["user"]["projectV2"]["id"]


def get_project_items_with_details(project_id: str, token: str) -> list:
    """Project の全アイテムを詳細情報付きで取得"""
    query = """
    query($projectId: ID!, $cursor: String) {
        node(id: $projectId) {
            ... on ProjectV2 {
                items(first: 100, after: $cursor) {
                    nodes {
                        id
                        updatedAt
                        fieldValues(first: 20) {
                            nodes {
                                ... on ProjectV2ItemFieldTextValue {
                                    text
                                    field { ... on ProjectV2Field { name } }
                                }
                                ... on ProjectV2ItemFieldSingleSelectValue {
                                    name
                                    field { ... on ProjectV2SingleSelectField { name } }
                                }
                            }
                        }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        }
    }
    """
    items = []
    cursor = None
    while True:
        result = graphql_request(query, {"projectId": project_id, "cursor": cursor}, token)
        items_data = result["data"]["node"]["items"]
        for item in items_data["nodes"]:
            # フィールドを辞書に変換
            fields = {}
            for fv in item.get("fieldValues", {}).get("nodes", []):
                field_name = fv.get("field", {}).get("name")
                if field_name:
                    # text または name (single select)
                    value = fv.get("text") or fv.get("name")
                    fields[field_name] = value
            items.append({
                "id": item["id"],
                "updatedAt": item["updatedAt"],
                "fields": fields,
            })
        if not items_data["pageInfo"]["hasNextPage"]:
            break
        cursor = items_data["pageInfo"]["endCursor"]
    return items


# =============================================================================
# File Operations
# =============================================================================

def find_feature_dir_for_wi(wi_id: str, specs_root: Path = Path("specs")) -> Optional[Path]:
    """WI ID から Feature ディレクトリを探す"""
    for feature_dir in specs_root.iterdir():
        if not feature_dir.is_dir():
            continue
        wi_dir = feature_dir / "work_items"
        if wi_dir.exists():
            for wi_file in wi_dir.glob("*.md"):
                if wi_id in wi_file.name:
                    return feature_dir
    return None


def parse_work_item_file(wi_file: Path) -> Optional[dict]:
    """WI ファイルを解析"""
    if not wi_file.exists():
        return None

    content = wi_file.read_text()
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not match:
        return None

    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = match.group(2)
        return {
            "frontmatter": frontmatter,
            "body": body,
            "raw": content,
            "mtime": datetime.fromtimestamp(wi_file.stat().st_mtime, tz=timezone.utc),
        }
    except yaml.YAMLError:
        return None


def update_work_item_file(wi_file: Path, updates: dict, dry_run: bool = False) -> dict:
    """WI ファイルを更新"""
    current = parse_work_item_file(wi_file)
    if not current:
        return {"error": "Failed to parse file"}

    changes = []
    frontmatter = current["frontmatter"].copy()

    # 更新可能なフィールド
    field_mapping = {
        "Status": None,  # Status はファイルには直接保存しない（state.yaml で管理）
        "Mode": "mode",
        "Complexity": "complexity",
    }

    for project_field, file_field in field_mapping.items():
        if project_field in updates and file_field:
            old_value = frontmatter.get(file_field)
            new_value = updates[project_field].lower() if updates[project_field] else None
            if old_value != new_value and new_value:
                frontmatter[file_field] = new_value
                changes.append(f"{file_field}: {old_value} → {new_value}")

    if not changes:
        return {"changes": [], "skipped": True}

    if dry_run:
        return {"changes": changes, "dry_run": True}

    # ファイルを書き換え
    new_frontmatter = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
    new_content = f"---\n{new_frontmatter}---\n{current['body']}"
    wi_file.write_text(new_content)

    return {"changes": changes}


def _normalize_work_items(work_items: list, default_mode: str = "autopilot") -> tuple[list, list]:
    """旧スキーマ（文字列配列）を正統スキーマ（dict配列）に正規化

    Args:
        work_items: 元の work_items リスト
        default_mode: 文字列→dict変換時のデフォルトmode

    Returns:
        (正規化後のリスト, 変更内容のリスト)
    """
    normalized = []
    changes = []

    for item in work_items:
        if isinstance(item, dict):
            # 既に dict: mode 欠落時は補完
            if "wi_id" in item:
                if "mode" not in item:
                    item["mode"] = default_mode
                    changes.append(f"mode補完: {item['wi_id']} → {default_mode}")
                normalized.append(item)
        elif isinstance(item, str):
            # 旧スキーマ: 文字列 → dict に変換
            normalized.append({
                "wi_id": item,
                "status": "pending",
                "mode": default_mode,
            })
            changes.append(f"schema: {item} を dict 形式に変換")
        # それ以外は無視（不正データ）

    return normalized, changes


def update_state_yaml(
    feature_dir: Path,
    wi_id: str,
    new_status: str,
    mode: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """state.yaml を更新

    正統スキーマ (work_items 配列形式):
        work_items:
          - wi_id: WI-XXX
            status: pending
            mode: autopilot

    旧スキーマ (文字列配列) は自動的に正規化されます。

    Args:
        feature_dir: Feature ディレクトリ
        wi_id: Work Item ID
        new_status: 新しいステータス（Projects 形式）
        mode: Mode (新規追加時、または既存WIのmode補完時に使用)
        dry_run: 変更せずに結果のみ返す
    """
    state_file = feature_dir / "state" / "state.yaml"
    if not state_file.exists():
        return {"error": "state.yaml not found"}

    with open(state_file) as f:
        state = yaml.safe_load(f) or {}

    # Status マッピング (Projects → state.yaml)
    status_mapping = {
        "pending_pre_approval": "pending",
        "in_progress": "in_progress",
        "pending_walkthrough": "in_progress",
        "pending_ci": "in_progress",
        "pending_ops": "in_progress",
        "done": "done",
    }

    mapped_status = status_mapping.get(new_status, new_status)

    # work_items 配列を正規化（旧スキーマ対応）
    # 注意: 正規化時の default_mode は常に "autopilot" に固定
    # 理由: 現在処理中の WI の mode が他の WI に波及するのを防ぐ
    # WI ファイルの frontmatter が mode の正本であり、Forward sync で正しく同期される
    work_items = state.get("work_items", [])
    if not isinstance(work_items, list):
        work_items = []

    work_items, normalize_changes = _normalize_work_items(work_items, default_mode="autopilot")

    # 現在の WI 用の effective_mode（引数があればそれを使用）
    effective_mode = (mode.lower() if mode else "autopilot")

    wi_found = False
    old_status = None
    changes = list(normalize_changes)  # 正規化による変更を先に追加

    for wi in work_items:
        if wi.get("wi_id") == wi_id:
            wi_found = True
            old_status = wi.get("status")
            old_mode = wi.get("mode")

            # 現在の WI については effective_mode を使用
            # (正規化で autopilot になっていても、指定された mode に更新)
            if old_mode != effective_mode:
                wi["mode"] = effective_mode
                changes.append(f"mode: {old_mode} → {effective_mode}")

            # status が同じ場合でも、正規化や mode 変更があれば書き込む
            if old_status == mapped_status and not changes:
                return {"changes": [], "skipped": True}

            if old_status != mapped_status:
                changes.append(f"status: {old_status} → {mapped_status}")
                wi["status"] = mapped_status
            break

    if not wi_found:
        # WI が state.yaml にない場合は追加
        changes.append(f"status: (new) → {mapped_status}")
        new_wi = {
            "wi_id": wi_id,
            "status": mapped_status,
            "mode": effective_mode,  # 常に mode を設定
        }
        work_items.append(new_wi)

    if dry_run:
        return {"changes": changes, "dry_run": True}

    state["work_items"] = work_items
    with open(state_file, "w") as f:
        yaml.dump(state, f, allow_unicode=True, default_flow_style=False)

    return {"changes": changes}


def update_approval_file(feature_dir: Path, wi_id: str, approvals: dict, dry_run: bool = False) -> dict:
    """WI の approval.md を更新"""
    approval_file = feature_dir / "work_items" / f"{wi_id}.approval.md"

    if not approval_file.exists():
        # 承認ファイルがない場合は作成しない（人間が作成すべき）
        return {"skipped": True, "reason": "approval file does not exist"}

    content = approval_file.read_text()
    changes = []

    # チェックボックスの更新
    checkbox_mapping = {
        "walkthrough_reviewed": (r'\[ \]\s*(walkthrough|ウォークスルー)', '[x] '),
        "ci_passed": (r'\[ \]\s*(CI|テスト)', '[x] '),
        "ops_reviewed": (r'\[ \]\s*(ops|運用)', '[x] '),
    }

    for field, (pattern, replacement) in checkbox_mapping.items():
        if approvals.get(field):
            if re.search(pattern, content, re.IGNORECASE):
                # 未チェックの項目があれば更新
                new_content = re.sub(
                    r'\[ \](\s*(?:' + pattern.split('|')[0].replace(r'\[ \]\s*', '') + '|' +
                    pattern.split('|')[1].replace(')', '') + '))',
                    replacement + r'\1',
                    content,
                    flags=re.IGNORECASE
                )
                if new_content != content:
                    content = new_content
                    changes.append(f"{field}: ✓")

    if not changes:
        return {"changes": [], "skipped": True}

    if dry_run:
        return {"changes": changes, "dry_run": True}

    approval_file.write_text(content)
    return {"changes": changes}


# =============================================================================
# Conflict Detection
# =============================================================================

def detect_conflict(
    wi_file: Path,
    project_item: dict,
    feature_dir: Path,
    include_status: bool = True,
) -> dict:
    """ファイルと Projects の競合を検出

    Args:
        wi_file: Work Item ファイルパス
        project_item: Projects から取得したアイテム
        feature_dir: Feature ディレクトリ
        include_status: Status も競合判定に含めるか（--prefer file 時に重要）

    Returns:
        dict with keys:
        - conflict: bool - 競合があるか
        - reason: str - 競合がない場合の理由 ("file_not_found", "recent_sync")
        - file_newer: bool - ファイル側が新しいか（競合時のみ）
        - differences: list - 差異のリスト（競合時のみ）

    Note:
        5分以内の更新差は「recent_sync」として競合扱いしない。
        これは Forward Sync 直後の Reverse Sync で意図しない上書きを防ぐため。
        ただし、この grace period 中は --prefer file でも Projects 側の変更が
        反映される可能性がある（仕様）。
    """
    file_data = parse_work_item_file(wi_file)
    if not file_data:
        return {"conflict": False, "reason": "file_not_found"}

    # WI ファイルと state.yaml の両方の mtime を考慮
    file_mtime = file_data["mtime"]
    state_file = feature_dir / "state" / "state.yaml"
    if state_file.exists():
        state_mtime = datetime.fromtimestamp(state_file.stat().st_mtime, tz=timezone.utc)
        # より新しい方を採用
        file_mtime = max(file_mtime, state_mtime)

    project_updated = datetime.fromisoformat(project_item["updatedAt"].replace("Z", "+00:00"))

    # 5分以内の差は許容（同期による更新の可能性）
    time_diff = abs((file_mtime - project_updated).total_seconds())
    if time_diff < 300:
        return {"conflict": False, "reason": "recent_sync"}

    # 内容の差異をチェック
    file_mode = file_data["frontmatter"].get("mode", "").lower()
    project_mode = (project_item["fields"].get("Mode") or "").lower()

    file_complexity = file_data["frontmatter"].get("complexity", "").lower()
    project_complexity = (project_item["fields"].get("Complexity") or "").lower()

    differences = []
    if file_mode and project_mode and file_mode != project_mode:
        differences.append(f"mode: file={file_mode}, project={project_mode}")
    if file_complexity and project_complexity and file_complexity != project_complexity:
        differences.append(f"complexity: file={file_complexity}, project={project_complexity}")

    # Status の差異もチェック（include_status=True の場合）
    if include_status:
        wi_id = file_data["frontmatter"].get("wi_id")
        if wi_id:
            file_status = _get_status_from_state(feature_dir, wi_id)
            project_status = project_item["fields"].get("Status", "")
            # Projects の詳細ステータスを state.yaml の簡易ステータスに変換して比較
            mapped_project_status = _map_project_status_to_state(project_status)
            if file_status and mapped_project_status and file_status != mapped_project_status:
                differences.append(f"status: file={file_status}, project={project_status}→{mapped_project_status}")

    if differences:
        return {
            "conflict": True,
            "file_newer": file_mtime > project_updated,
            "file_mtime": file_mtime.isoformat(),
            "project_updated": project_updated.isoformat(),
            "differences": differences,
        }

    return {"conflict": False}


def _get_status_from_state(feature_dir: Path, wi_id: str) -> Optional[str]:
    """state.yaml から WI の status を取得"""
    state_file = feature_dir / "state" / "state.yaml"
    if not state_file.exists():
        return None
    with open(state_file) as f:
        state = yaml.safe_load(f) or {}
    for wi in state.get("work_items", []):
        if isinstance(wi, dict) and wi.get("wi_id") == wi_id:
            return wi.get("status")
    return None


def _map_project_status_to_state(project_status: str) -> str:
    """Projects の Status を state.yaml のステータスにマッピング"""
    mapping = {
        "pending_pre_approval": "pending",
        "in_progress": "in_progress",
        "pending_walkthrough": "in_progress",
        "pending_ci": "in_progress",
        "pending_ops": "in_progress",
        "done": "done",
    }
    return mapping.get(project_status, project_status)


# =============================================================================
# Main Sync Logic
# =============================================================================

def sync_project_item_to_file(
    item: dict,
    feature_dir: Path,
    prefer: str = "auto",
    dry_run: bool = False,
) -> dict:
    """1つの Project アイテムをファイルに同期

    Args:
        item: Projects から取得したアイテム
        feature_dir: Feature ディレクトリ
        prefer: 競合解決戦略 (auto/file/projects)
        dry_run: 変更せずに結果のみ返す
    """
    wi_id = item["fields"].get("WI ID")
    if not wi_id:
        return {"skipped": True, "reason": "no_wi_id"}

    wi_file = feature_dir / "work_items" / f"{wi_id}.md"
    if not wi_file.exists():
        return {"skipped": True, "reason": "file_not_found", "wi_id": wi_id}

    # 競合検出（Status も含めて検出）
    conflict_result = detect_conflict(wi_file, item, feature_dir, include_status=True)

    # 競合時の処理
    if conflict_result["conflict"]:
        if prefer == "auto":
            # 新しい方を採用
            if conflict_result["file_newer"]:
                return {
                    "skipped": True,
                    "reason": "file_newer",
                    "conflict": conflict_result,
                    "wi_id": wi_id,
                }
            # Project が新しい場合は続行
        elif prefer == "file":
            # ファイル優先：全ての更新をスキップ
            return {
                "skipped": True,
                "reason": "prefer_file",
                "conflict": conflict_result,
                "wi_id": wi_id,
            }
        # prefer == "projects" の場合は続行

    results = {"wi_id": wi_id, "changes": []}

    # WI ファイル更新（mode, complexity）
    wi_updates = {
        "Mode": item["fields"].get("Mode"),
        "Complexity": item["fields"].get("Complexity"),
    }
    wi_result = update_work_item_file(wi_file, wi_updates, dry_run)
    if wi_result.get("changes"):
        results["changes"].extend([f"WI: {c}" for c in wi_result["changes"]])

    # State 更新（status）
    status = item["fields"].get("Status")
    mode = item["fields"].get("Mode")
    if status:
        # Status 更新条件:
        # 1. 競合がない場合 → 更新
        # 2. --prefer projects → 強制更新
        # 3. --prefer auto かつ Project が新しい → 更新
        is_project_newer = conflict_result.get("conflict") and not conflict_result.get("file_newer", True)
        should_update_status = (
            not conflict_result.get("conflict") or
            prefer == "projects" or
            (prefer == "auto" and is_project_newer)
        )
        if should_update_status:
            state_result = update_state_yaml(feature_dir, wi_id, status, mode=mode, dry_run=dry_run)
            if state_result.get("changes"):
                results["changes"].extend([f"State: {c}" for c in state_result["changes"]])

    results["dry_run"] = dry_run
    return results


def sync_feature_from_projects(
    feature_dir: Path,
    config: dict,
    prefer: str = "auto",
    dry_run: bool = False,
) -> dict:
    """Feature を Projects から同期"""
    print(f"\n📂 Syncing from Projects: {feature_dir}")

    if not config["token"]:
        return {"error": "GH_TOKEN not set"}

    if not config["project_number"] or not config["owner"]:
        return {"error": "GITHUB_PROJECT_NUMBER or GITHUB_OWNER not set"}

    try:
        project_id = get_project_id(
            config["owner"],
            int(config["project_number"]),
            config["token"],
            config["owner_type"],
        )
        print(f"  🔗 Project ID: {project_id[:20]}...")

        items = get_project_items_with_details(project_id, config["token"])
        print(f"  📦 Found {len(items)} items in Projects")

        # Feature に属するアイテムをフィルタ
        feature_name = feature_dir.name
        synced = 0
        skipped = 0
        conflicts = []

        for item in items:
            wi_id = item["fields"].get("WI ID", "")
            # Feature に属するかチェック（WI ID に Feature 名が含まれるか）
            if not wi_id:
                continue

            wi_file = feature_dir / "work_items" / f"{wi_id}.md"
            if not wi_file.exists():
                continue

            result = sync_project_item_to_file(item, feature_dir, prefer, dry_run)

            if result.get("conflict"):
                conflicts.append(result)
                icon = "⚠️"
            elif result.get("skipped"):
                skipped += 1
                icon = "⏭️"
            elif result.get("changes"):
                synced += 1
                icon = "🔄" if not dry_run else "🔍"
            else:
                skipped += 1
                icon = "✓"

            changes_str = ", ".join(result.get("changes", [])) or "no changes"
            print(f"    {icon} {wi_id}: {changes_str}")

        return {
            "feature": feature_name,
            "synced": synced,
            "skipped": skipped,
            "conflicts": conflicts,
        }

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"error": str(e)}


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Sync GitHub Projects to STRIDE files")
    parser.add_argument("--feature", help="Feature directory (e.g., specs/my_feature/)")
    parser.add_argument("--wi-id", help="Specific WI ID to sync")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--prefer", choices=["auto", "file", "projects"], default="auto",
                        help="Conflict resolution preference (default: auto = newer wins)")
    args = parser.parse_args()

    config = get_config()

    print("=" * 60)
    print("GitHub Projects → STRIDE Sync (Reverse)")
    print("=" * 60)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")

    if args.wi_id:
        # 特定の WI を同期
        feature_dir = find_feature_dir_for_wi(args.wi_id)
        if not feature_dir:
            print(f"❌ Feature not found for WI: {args.wi_id}")
            sys.exit(1)
        result = sync_feature_from_projects(feature_dir, config, args.prefer, args.dry_run)
    elif args.feature:
        feature_dir = Path(args.feature)
        if not feature_dir.exists():
            print(f"❌ Directory not found: {feature_dir}")
            sys.exit(1)
        result = sync_feature_from_projects(feature_dir, config, args.prefer, args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    if "error" in result:
        print(f"  ❌ Error: {result['error']}")
    else:
        print(f"  Synced: {result.get('synced', 0)}")
        print(f"  Skipped: {result.get('skipped', 0)}")
        if result.get("conflicts"):
            print(f"  ⚠️  Conflicts: {len(result['conflicts'])}")
            for c in result["conflicts"]:
                print(f"      - {c.get('wi_id')}: {c.get('conflict', {}).get('differences', [])}")


if __name__ == "__main__":
    main()
