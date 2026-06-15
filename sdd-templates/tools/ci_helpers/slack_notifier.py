"""slack_notifier — Slack incoming webhook for #method-board / #ops-channel.

Reads SLACK_WEBHOOK_URL from environment by default. In dry-run mode prints
the payload without making any network call.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass


@dataclass
class NotifyResult:
    sent: bool
    channel: str
    status: int
    output: str


def notify(message: str, channel: str = "#method-board",
           urgent: bool = False, dry_run: bool = False) -> NotifyResult:
    """Post a Slack message via incoming webhook.

    Args:
      message: text body.
      channel: target channel (e.g. #method-board, #ops-channel).
      urgent: if True, prefix with :rotating_light: emoji and bold text.
      dry_run: skip network call; useful for unit tests and local validation.
    """
    payload = {
        "text": (":rotating_light: *URGENT* — " + message) if urgent else message,
        "channel": channel,
        "username": "method-board-bot",
        "icon_emoji": ":sparkles:" if not urgent else ":rotating_light:",
    }

    if dry_run:
        return NotifyResult(False, channel, 0,
                            f"(dry-run) Slack payload: {json.dumps(payload, ensure_ascii=False)[:300]}")

    webhook = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook:
        return NotifyResult(False, channel, 0,
                            "ERROR: SLACK_WEBHOOK_URL env not set")

    try:
        from urllib import request

        req = request.Request(
            webhook,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=10) as r:
            status = r.status
            body = r.read().decode("utf-8", errors="replace")[:200]
        return NotifyResult(200 <= status < 300, channel, status, body)
    except Exception as e:
        return NotifyResult(False, channel, 0, f"Slack post failed: {e}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="slack_notifier")
    parser.add_argument("--message", required=True)
    parser.add_argument("--channel", default="#method-board")
    parser.add_argument("--urgent", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    res = notify(args.message, args.channel, args.urgent, args.dry_run)
    print(json.dumps({
        "sent": res.sent,
        "channel": res.channel,
        "status": res.status,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
