#!/usr/bin/env python3
"""
Dispatcher: fetch recent ✅'d messages from #bond-deal-alerts, filter out
ones already in state.json, and trigger a separate GitHub Actions workflow
run for each new deal via workflow_dispatch.

CLI:
    python3 dispatch_deals.py

Env:
    SLACK_BOT_TOKEN — required
    GITHUB_TOKEN    — required (the default GITHUB_TOKEN from the workflow)
    GITHUB_REPOSITORY — required (set automatically by GitHub Actions)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
from pathlib import Path
from urllib import request, error

CHANNEL = "C09JX51GAKH"
WINDOW_SECONDS = 21600  # 6h
SLACK_API = "https://slack.com/api"
GH_API = "https://api.github.com"


def _slack_token() -> str:
    tok = os.environ.get("SLACK_BOT_TOKEN")
    if tok:
        return tok
    envf = Path.home() / ".bondradar-env"
    if envf.exists():
        for line in envf.read_text().splitlines():
            if line.startswith("SLACK_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("SLACK_BOT_TOKEN not set")


def _slack_get(method: str, params: dict) -> dict:
    url = f"{SLACK_API}/{method}?" + urllib.parse.urlencode(params)
    req = request.Request(url, headers={"Authorization": f"Bearer {_slack_token()}"})
    with request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode())
    if not body.get("ok"):
        raise RuntimeError(f"Slack API {method}: {body.get('error')}")
    return body


def _trigger_workflow(message_ts: str, message_json: str) -> bool:
    """Trigger the qa-deal.yml workflow for a single deal. Returns True on success."""
    gh_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not gh_token or not repo:
        print(f"  GITHUB_TOKEN or GITHUB_REPOSITORY not set, skipping dispatch for {message_ts}", file=sys.stderr)
        return False

    url = f"{GH_API}/repos/{repo}/actions/workflows/qa-deal.yml/dispatches"
    payload = json.dumps({
        "ref": "main",
        "inputs": {
            "message_ts": message_ts,
            "message_json": message_json,
        }
    }).encode()
    req = request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {gh_token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            if resp.status in (200, 204):
                return True
    except error.HTTPError as e:
        body = e.read().decode()[:500]
        print(f"  dispatch failed for {message_ts}: HTTP {e.code} — {body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  dispatch failed for {message_ts}: {e}", file=sys.stderr)
        return False
    return False


def main() -> int:
    state_path = Path("state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}

    resp = _slack_get("conversations.history", {
        "channel": CHANNEL,
        "oldest": f"{time.time() - WINDOW_SECONDS:.6f}",
        "limit": 200,
    })
    msgs = resp.get("messages") or []

    candidates = []
    for m in msgs:
        ts = m.get("ts")
        if not ts or ts in state:
            continue
        if any(r.get("name") == "white_check_mark" for r in (m.get("reactions") or [])):
            candidates.append(m)

    candidates.sort(key=lambda m: float(m["ts"]))

    if not candidates:
        print("no new deals to dispatch")
        return 0

    print(f"found {len(candidates)} new deal(s) to dispatch")

    dispatched = 0
    for m in candidates:
        ts = m["ts"]
        msg_json = json.dumps(m)
        if _trigger_workflow(ts, msg_json):
            print(f"  dispatched {ts}")
            dispatched += 1
        else:
            print(f"  failed to dispatch {ts}")

    print(f"dispatched {dispatched}/{len(candidates)} deals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
