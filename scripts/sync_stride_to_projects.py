#!/usr/bin/env python3
"""
STRIDE → GitHub Projects 同期スクリプト (Option C: 一方向同期)

state.yaml と work_items/*.md を読み取り、GitHub Projects に反映する。
ファイルが正本、GitHub Projects は可視化専用。

Usage:
    python scripts/sync_stride_to_projects.py specs/<feature>/
    python scripts/sync_stride_to_projects.py --all  # 全feature同期
    python scripts/sync_stride_to_projects.py --dry-run specs/<feature>/

Environment:
    GH_TOKEN: GitHub Personal Access Token (project:write scope)
    GITHUB_PROJECT_NUMBER: Project番号 (e.g., 1)
    GITHUB_OWNER: Organization or User名

Requirements:
    - PyYAML
    - requests (for GraphQL API)
"""

import argparse
import json
import os
import re
import subprocess
import sys
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
        "owner_type": os.environ.get("GITHUB_OWNER_TYPE", "organization"),  # or "user"
    }


# =============================================================================
# File Parsing
# =============================================================================

def parse_state_yaml(feature_dir: Path) -> Optional[dict]:
    """state/state.yaml を読み取り"""
    state_file = feature_dir / "state" / "state.yaml"
    if not state_file.exists():
        return None
    with open(state_file) as f:
        return yaml.safe_load(f)


def parse_work_item(wi_file: Path) -> Optional[dict]:
    """WI-*.md の YAML frontmatter を解析"""
    if not wi_file.exists():
        return None

    content = wi_file.read_text()

    # YAML frontmatter を抽出 (--- で囲まれた部分)
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None

    try:
        data = yaml.safe_load(match.group(1))
        data["_file_path"] = str(wi_file)
        return data
    except yaml.YAMLError:
        return None


def parse_approval(approval_file: Path) -> dict:
    """WI-*.approval.md からチェックボックス状態を解析"""
    result = {
        "pre_run_approved": False,
        "post_run_approved": False,
        "walkthrough_reviewed": False,
        "ci_passed": False,
        "ops_reviewed": False,
    }

    if not approval_file.exists():
        return result

    content = approval_file.read_text()

    # チェックボックスパターン: [x] または [X]
    if re.search(r'\[x\]\s*(Pre-run|事前承認)', content, re.IGNORECASE):
        result["pre_run_approved"] = True
    if re.search(r'\[x\]\s*(Post-run|事後承認)', content, re.IGNORECASE):
        result["post_run_approved"] = True
    if re.search(r'\[x\]\s*(walkthrough|ウォークスルー)', content, re.IGNORECASE):
        result["walkthrough_reviewed"] = True
    if re.search(r'\[x\]\s*(CI|テスト)', content, re.IGNORECASE):
        result["ci_passed"] = True
    if re.search(r'\[x\]\s*(ops|運用)', content, re.IGNORECASE):
        result["ops_reviewed"] = True

    return result


def check_run_status(feature_dir: Path, wi_id: str) -> dict:
    """runs/<wi_id>/ の存在と中身を確認"""
    runs_dir = feature_dir / "runs" / wi_id
    result = {
        "has_run": False,
        "run_id": None,
        "has_walkthrough": False,
        "has_test_results": False,
    }

    if not runs_dir.exists():
        return result

    # RUN-* ディレクトリを探す
    run_dirs = list(runs_dir.glob("RUN-*"))
    if run_dirs:
        result["has_run"] = True
        result["run_id"] = run_dirs[0].name

        run_dir = run_dirs[0]
        result["has_walkthrough"] = (run_dir / "walkthrough.md").exists()
        result["has_test_results"] = (run_dir / "test_results.md").exists()

    return result


def collect_feature_data(feature_dir: Path) -> dict:
    """Feature ディレクトリから全データを収集"""
    feature_dir = Path(feature_dir)

    # state.yaml
    state = parse_state_yaml(feature_dir)
    if not state:
        state = {"feature": feature_dir.name, "work_items": []}

    # work_items/*.md
    work_items_dir = feature_dir / "work_items"
    work_items = []

    if work_items_dir.exists():
        for wi_file in sorted(work_items_dir.glob("WI-*.md")):
            if ".approval.md" in wi_file.name:
                continue

            wi_data = parse_work_item(wi_file)
            if not wi_data:
                continue

            wi_id = wi_data.get("wi_id", wi_file.stem)

            # approval 状態
            approval_file = wi_file.with_suffix(".approval.md")
            approval = parse_approval(approval_file)

            # run 状態
            run_status = check_run_status(feature_dir, wi_id)

            # 統合
            work_items.append({
                "wi_id": wi_id,
                "title": wi_data.get("title", ""),
                "mode": wi_data.get("mode", "autopilot"),
                "complexity": wi_data.get("complexity", "medium"),
                "risk_flags": wi_data.get("risk_flags", []),
                "status": determine_status(wi_data, approval, run_status),
                "approval": approval,
                "run": run_status,
                "owners": wi_data.get("owners", {}),
            })

    return {
        "feature": state.get("feature", feature_dir.name),
        "current_gate": state.get("current_gate", "Unknown"),
        "work_items": work_items,
    }


def determine_status(wi_data: dict, approval: dict, run: dict) -> str:
    """WI の状態を判定"""
    mode = wi_data.get("mode", "autopilot")

    # Pre-run チェック (confirm/validate)
    if mode in ("confirm", "validate"):
        if not approval.get("pre_run_approved"):
            return "pending_pre_approval"

    # Run 存在チェック
    if not run.get("has_run"):
        return "in_progress"

    # Post-run チェック (全モード必須)
    if not approval.get("walkthrough_reviewed"):
        return "pending_walkthrough"
    if not approval.get("ci_passed"):
        return "pending_ci"
    if not approval.get("ops_reviewed"):
        return "pending_ops"

    return "done"


# =============================================================================
# GitHub Projects API (GraphQL)
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
    return response.json()


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


def get_project_fields(project_id: str, token: str) -> dict:
    """Project のカスタムフィールドを取得"""
    query = """
    query($projectId: ID!) {
        node(id: $projectId) {
            ... on ProjectV2 {
                fields(first: 50) {
                    nodes {
                        ... on ProjectV2Field {
                            id
                            name
                        }
                        ... on ProjectV2SingleSelectField {
                            id
                            name
                            options {
                                id
                                name
                            }
                        }
                    }
                }
            }
        }
    }
    """
    result = graphql_request(query, {"projectId": project_id}, token)
    fields = {}
    for field in result["data"]["node"]["fields"]["nodes"]:
        fields[field["name"]] = field
    return fields


def get_project_items(project_id: str, token: str) -> list:
    """Project の既存アイテムを取得"""
    query = """
    query($projectId: ID!, $cursor: String) {
        node(id: $projectId) {
            ... on ProjectV2 {
                items(first: 100, after: $cursor) {
                    nodes {
                        id
                        fieldValues(first: 20) {
                            nodes {
                                ... on ProjectV2ItemFieldTextValue {
                                    text
                                    field { ... on ProjectV2Field { name } }
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
        items.extend(items_data["nodes"])
        if not items_data["pageInfo"]["hasNextPage"]:
            break
        cursor = items_data["pageInfo"]["endCursor"]
    return items


def find_item_by_wi_id(items: list, wi_id: str) -> Optional[str]:
    """WI ID でアイテムを検索"""
    for item in items:
        for fv in item.get("fieldValues", {}).get("nodes", []):
            if fv.get("field", {}).get("name") == "WI ID" and fv.get("text") == wi_id:
                return item["id"]
    return None


def add_draft_issue(project_id: str, title: str, token: str) -> str:
    """Draft Issue を追加"""
    mutation = """
    mutation($projectId: ID!, $title: String!) {
        addProjectV2DraftIssue(input: {projectId: $projectId, title: $title}) {
            projectItem {
                id
            }
        }
    }
    """
    result = graphql_request(mutation, {"projectId": project_id, "title": title}, token)
    return result["data"]["addProjectV2DraftIssue"]["projectItem"]["id"]


def update_field_value(project_id: str, item_id: str, field_id: str, value: Any, token: str, field_type: str = "text"):
    """フィールド値を更新"""
    if field_type == "text":
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
            updateProjectV2ItemFieldValue(input: {
                projectId: $projectId
                itemId: $itemId
                fieldId: $fieldId
                value: { text: $value }
            }) {
                projectV2Item { id }
            }
        }
        """
    elif field_type == "single_select":
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
            updateProjectV2ItemFieldValue(input: {
                projectId: $projectId
                itemId: $itemId
                fieldId: $fieldId
                value: { singleSelectOptionId: $value }
            }) {
                projectV2Item { id }
            }
        }
        """
    else:
        return

    graphql_request(mutation, {
        "projectId": project_id,
        "itemId": item_id,
        "fieldId": field_id,
        "value": value,
    }, token)


def sync_work_item_to_project(
    project_id: str,
    fields: dict,
    existing_items: list,
    wi: dict,
    token: str,
    dry_run: bool = False,
) -> dict:
    """1つの WI を GitHub Projects に同期"""
    wi_id = wi["wi_id"]

    # 既存アイテムを検索
    item_id = find_item_by_wi_id(existing_items, wi_id)

    action = "update" if item_id else "create"

    if dry_run:
        return {"action": action, "wi_id": wi_id, "dry_run": True}

    # 新規作成
    if not item_id:
        title = f"[{wi_id}] {wi['title']}"
        item_id = add_draft_issue(project_id, title, token)

    # フィールド更新
    field_updates = {
        "WI ID": (wi_id, "text"),
        "Mode": (wi["mode"], "single_select"),
        "Complexity": (wi["complexity"], "single_select"),
        "Status": (wi["status"], "single_select"),
        "Risk Flags": (", ".join(wi.get("risk_flags", [])), "text"),
        "Walkthrough": ("Yes" if wi["run"].get("has_walkthrough") else "No", "single_select"),
        "Run ID": (wi["run"].get("run_id") or "", "text"),
    }

    for field_name, (value, field_type) in field_updates.items():
        if field_name not in fields:
            continue

        field = fields[field_name]
        field_id = field["id"]

        if field_type == "single_select" and "options" in field:
            # オプション ID を検索
            option_id = None
            for opt in field["options"]:
                if opt["name"].lower() == str(value).lower():
                    option_id = opt["id"]
                    break
            if option_id:
                update_field_value(project_id, item_id, field_id, option_id, token, "single_select")
        else:
            update_field_value(project_id, item_id, field_id, str(value), token, "text")

    return {"action": action, "wi_id": wi_id, "item_id": item_id}


# =============================================================================
# Main
# =============================================================================

def sync_feature(feature_dir: Path, config: dict, dry_run: bool = False) -> dict:
    """1つの Feature を同期"""
    print(f"\n📂 Processing: {feature_dir}")

    # データ収集
    data = collect_feature_data(feature_dir)

    if not data["work_items"]:
        print("  ⚠️  No work items found")
        return {"feature": data["feature"], "synced": 0, "skipped": True}

    print(f"  📋 Found {len(data['work_items'])} work items")

    if not config["token"]:
        print("  ❌ GH_TOKEN not set - showing local data only")
        for wi in data["work_items"]:
            print(f"    - {wi['wi_id']}: {wi['status']} (mode={wi['mode']})")
        return {"feature": data["feature"], "work_items": data["work_items"], "synced": 0}

    if not config["project_number"] or not config["owner"]:
        print("  ❌ GITHUB_PROJECT_NUMBER or GITHUB_OWNER not set")
        return {"feature": data["feature"], "synced": 0, "error": "config_missing"}

    # GitHub Projects 同期
    try:
        project_id = get_project_id(
            config["owner"],
            int(config["project_number"]),
            config["token"],
            config["owner_type"],
        )
        print(f"  🔗 Project ID: {project_id[:20]}...")

        fields = get_project_fields(project_id, config["token"])
        print(f"  📊 Fields: {', '.join(fields.keys())}")

        existing_items = get_project_items(project_id, config["token"])
        print(f"  📦 Existing items: {len(existing_items)}")

        synced = 0
        for wi in data["work_items"]:
            result = sync_work_item_to_project(
                project_id, fields, existing_items, wi, config["token"], dry_run
            )
            action_icon = "🆕" if result["action"] == "create" else "🔄"
            if dry_run:
                action_icon = "🔍"
            print(f"    {action_icon} {wi['wi_id']}: {wi['status']}")
            synced += 1

        return {"feature": data["feature"], "synced": synced}

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"feature": data["feature"], "synced": 0, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Sync STRIDE state to GitHub Projects")
    parser.add_argument("feature_dir", nargs="?", help="Feature directory (e.g., specs/my_feature/)")
    parser.add_argument("--all", action="store_true", help="Sync all features in specs/")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced without making changes")
    parser.add_argument("--local-only", action="store_true", help="Only show local data, don't sync")
    args = parser.parse_args()

    config = get_config()

    if args.local_only:
        config["token"] = None

    print("=" * 60)
    print("STRIDE → GitHub Projects Sync")
    print("=" * 60)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")

    if args.all:
        specs_dir = Path("specs")
        if not specs_dir.exists():
            print("❌ specs/ directory not found")
            sys.exit(1)

        features = [d for d in specs_dir.iterdir() if d.is_dir()]
        results = []
        for feature_dir in sorted(features):
            result = sync_feature(feature_dir, config, args.dry_run)
            results.append(result)

        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        total_synced = sum(r.get("synced", 0) for r in results)
        print(f"  Features processed: {len(results)}")
        print(f"  Work items synced: {total_synced}")

    elif args.feature_dir:
        feature_dir = Path(args.feature_dir)
        if not feature_dir.exists():
            print(f"❌ Directory not found: {feature_dir}")
            sys.exit(1)
        sync_feature(feature_dir, config, args.dry_run)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
