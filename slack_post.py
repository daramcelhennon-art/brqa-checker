#!/usr/bin/env python3
"""Post a threaded reply as the BR QA bot (not as the calling user).

Uses SLACK_BOT_TOKEN from ~/.bondradar-env — same token that reads reactors/files.
This is the ONLY way to make the message appear from `br_qa_reactor_reader` in
Slack instead of the human user whose OAuth backs the MCP connector.

CLI:
    python3 slack_post.py <channel_id> <thread_ts> "<message text>"

Or read message from stdin:
    python3 slack_post.py <channel_id> <thread_ts> -    <<'EOF'
    <@USERID>
    :white_check_mark: BR QA — id `X` at <stage> — Perfect! Great job
    ...
    EOF

Prints the posted message's permalink JSON on success; non-zero exit on failure.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
from pathlib import Path
from urllib import request, error

ENV_FILE = Path.home() / ".bondradar-env"
SLACK_API = "https://slack.com/api"


def _token() -> str:
    tok = os.environ.get("SLACK_BOT_TOKEN")
    if tok:
        return tok
    if not ENV_FILE.exists():
        raise RuntimeError(f"{ENV_FILE} not found and SLACK_BOT_TOKEN not in env")
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("SLACK_BOT_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"SLACK_BOT_TOKEN not found in {ENV_FILE}")


def _get(method: str, params: dict) -> dict:
    url = f"{SLACK_API}/{method}?{urllib.parse.urlencode(params)}"
    req = request.Request(url, headers={"Authorization": f"Bearer {_token()}"})
    try:
        with request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
    except error.HTTPError as e:
        raise RuntimeError(f"Slack API {method} HTTP {e.code}: {e.read().decode()[:200]}")
    if not body.get("ok"):
        raise RuntimeError(f"Slack API {method} error: {body.get('error', 'unknown')}")
    return body


_BOT_IDENTITY: dict | None = None


def _bot_identity() -> dict:
    """Cached auth.test — returns {user_id, bot_id}."""
    global _BOT_IDENTITY
    if _BOT_IDENTITY is None:
        r = _get("auth.test", {})
        _BOT_IDENTITY = {"user_id": r.get("user_id"), "bot_id": r.get("bot_id")}
    return _BOT_IDENTITY


def bot_already_in_thread(channel: str, thread_ts: str, exclude_marker: str | None = None) -> bool:
    """True iff this bot has any reply in the thread already.

    `exclude_marker`, if given, is a substring that disqualifies a reply from
    counting - used so a mechanical pre_check.py flag (tagged with its own
    marker) doesn't block a later, separate Claude AI-pass post in the same
    thread. Each layer should only guard against duplicating ITSELF.
    """
    ident = _bot_identity()
    replies = _get("conversations.replies",
                   {"channel": channel, "ts": thread_ts, "limit": 200}).get("messages") or []
    for m in replies[1:]:  # skip the parent message
        is_this_bot = (m.get("bot_id") and m.get("bot_id") == ident["bot_id"]) or \
                      (m.get("user") and m.get("user") == ident["user_id"])
        if not is_this_bot:
            continue
        if exclude_marker and exclude_marker in (m.get("text") or ""):
            continue
        return True
    return False


def post_thread(channel: str, thread_ts: str, text: str) -> dict:
    payload = json.dumps({
        "channel": channel,
        "thread_ts": thread_ts,
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False,
    }).encode("utf-8")
    req = request.Request(
        f"{SLACK_API}/chat.postMessage",
        data=payload,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
    except error.HTTPError as e:
        raise RuntimeError(f"Slack chat.postMessage HTTP {e.code}: {e.read().decode()[:200]}")
    if not body.get("ok"):
        raise RuntimeError(f"Slack chat.postMessage error: {body.get('error', 'unknown')}")
    return body


def _cli(argv: list[str]) -> int:
    if len(argv) < 4:
        print("usage: slack_post.py <channel_id> <thread_ts> <text|->", file=sys.stderr)
        return 2
    channel, thread_ts, text_arg = argv[1], argv[2], argv[3]
    text = sys.stdin.read() if text_arg == "-" else text_arg

    # Idempotency guard: never post twice in the same thread.
    # state.json push can fail intermittently (concurrent runs, transient
    # push errors) which lets stale state re-QA the same message on a later
    # tick. The thread itself is the source of truth for "already posted".
    #
    # Excludes pre_check.py's mechanical-flag posts (tagged "· pre-check)")
    # from counting here - a mechanical flag firing doesn't mean the AI pass
    # has run yet, so it must not block this (the AI pass's own) post.
    if bot_already_in_thread(channel, thread_ts, exclude_marker="· pre-check)"):
        print(json.dumps({
            "skipped": True,
            "reason": "bot_already_in_thread",
            "channel": channel,
            "thread_ts": thread_ts,
        }))
        return 0

    body = post_thread(channel, thread_ts, text)
    print(json.dumps({
        "ts": body["ts"],
        "channel": body["channel"],
        "as_user_id": (body.get("message") or {}).get("bot_id") or (body.get("message") or {}).get("user"),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
