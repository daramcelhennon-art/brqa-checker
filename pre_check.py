#!/usr/bin/env python3
"""
Pre-check: pure-code QA checks run BEFORE Claude.

Handles two cases without invoking Claude at all:
  1. Non-deals (tender/LM/exchange/consent) → post "skipped", react nothing
  2. Mechanical field failures on the BR record → post flags, react exclamation

If the message passes all mechanical checks the script exits 0 with
PRE_CHECK=needs_ai printed, and Claude runs normally.

Env:
    SHARD_FILE          — path to shard JSON (array of Slack messages)
    STATE_DELTA_FILE    — path to write {ts: {checked_at, verdict}} delta
    SLACK_BOT_TOKEN     — bot token
    BR_USERNAME / BR_PASSWORD — for cookie refresh fallback
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib import request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bondradar_api import BondRadar
from slack_post import bot_already_in_thread, post_thread
from slack_react import add_reaction

CHANNEL = "C09JX51GAKH"

# ── non-deal keyword filter ────────────────────────────────────────────────
NON_DEAL_PATTERNS = re.compile(
    r"\b(tender offer|exchange offer|consent solicitation|liability management"
    r"|buyback|buy-back|LM exercise|repurchase offer|self tender"
    # "make whole" only in LM context — NOT "make whole call" which is a bond covenant
    r"|make whole\s+(?:offer|redemption|purchase|tender))\b",
    re.IGNORECASE,
)

# ── stage detection ────────────────────────────────────────────────────────
STAGE_RE = re.compile(
    r":\s*(Priced|Allocations\s+Out|Allocations|Book\s+Update|Revised\s+Guidance"
    r"|Guidance|Launched|Final\s+Terms|IPTs|Mandate)(?:\s+at\b[^:]*)?$",
    re.IGNORECASE,
)

# ── format flags (exactly one must be true on priced form) ─────────────────
FORMAT_FLAG_FIELDS = [
    "dealRegsOnly", "deal144aOnly", "deal144aRegs",
    "secRegistered", "hg3a2", "hgSecExempt",
]


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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


def _post(channel: str, thread_ts: str, text: str) -> None:
    if bot_already_in_thread(channel, thread_ts):
        print(f"  already posted in thread {thread_ts}, skipping")
        return
    post_thread(channel, thread_ts, text)


def _react(channel: str, ts: str, emoji: str) -> None:
    try:
        add_reaction(channel, ts, emoji)
    except Exception as e:
        print(f"  react {emoji} failed: {e}", file=sys.stderr)


def _write_delta(delta_path: str, ts: str, verdict: str) -> None:
    existing = {}
    if Path(delta_path).exists():
        try:
            existing = json.loads(Path(delta_path).read_text())
        except Exception:
            pass
    existing[ts] = {"checked_at": _now(), "verdict": verdict}
    Path(delta_path).write_text(json.dumps(existing, indent=2))


def _stage_from_headline(headline: str) -> str | None:
    m = STAGE_RE.search(headline or "")
    if m:
        return m.group(1).replace(" ", "_").lower()
    return None


def _has_accents(text: str) -> bool:
    for ch in text:
        if ord(ch) > 127 and unicodedata.category(ch) not in ("Zs",):
            return True
    return False


def _stats_sum_ok(cats: list[dict], category_type: str) -> tuple[bool, float]:
    """Return (ok, total) for a given statsCategories type."""
    total = sum(
        float(c.get("percentage", 0))
        for c in cats
        if c.get("type") == category_type
    )
    return abs(total - 100.0) <= 0.15, total


def check_deal(br: BondRadar, cat: str, deal: dict, source_text: str) -> list[str]:
    """Run all mechanical checks. Returns list of flag strings."""
    flags: list[str] = []
    deal_id = deal["id"]
    headline = deal.get("headline") or ""
    body = deal.get("message") or ""
    stage = _stage_from_headline(headline)
    hg = deal.get("hgDetails") or {}
    em = deal.get("emDetails") or {}

    # 1. highYield requires hyExpectedPageId (pre-priced only)
    if hg.get("highYield") and stage != "priced":
        hype = hg.get("hyExpectedPageId")
        if not hype:
            flags.append("`hyExpectedPageId` — null → populate HYRE## (`highYield=true` requires it)")

    # 3. Common terms: count on multi-tranche body
    ct_count = body.count("Common terms:")
    if ct_count > 1:
        flags.append(f"`Common terms:` appears {ct_count}× in body — must be exactly 1 on multi-tranche")

    # 4. Accentuated chars in body (not at Mandate)
    if stage and stage != "mandate" and _has_accents(body):
        bad = [ch for ch in body if ord(ch) > 127 and unicodedata.category(ch) not in ("Zs",)]
        flags.append(f"Body contains accented characters — strip diacritics: {''.join(set(bad))[:30]}")

    # 5. Priced-form checks (only when stage == priced)
    if stage == "priced" and deal.get("pricedDeals"):
        priced_id = deal["pricedDeals"][0]["id"]
        try:
            pd = br.get_priced_deal(cat, priced_id)
        except Exception as e:
            print(f"  could not fetch priced deal {priced_id}: {e}", file=sys.stderr)
            pd = None

        if pd:
            # 5a. isin / figi / bloombergCode must all be populated.
            # Re-fetch once before flagging — priced form may not yet be saved
            # if the associate is still entering codes when the bot runs.
            missing_fields = [f for f in ("isin", "figi", "bloombergCode") if not pd.get(f)]
            if missing_fields:
                try:
                    pd2 = br.get_priced_deal(cat, priced_id)
                    missing_fields = [f for f in missing_fields if not pd2.get(f)]
                except Exception:
                    pass
            for field in missing_fields:
                flags.append(f"`{field}` — null → must be populated on priced record")

            # 5b. Exactly one format flag true
            true_flags = [f for f in FORMAT_FLAG_FIELDS if pd.get(f)]
            if len(true_flags) == 0:
                flags.append(f"Format flags — none set; exactly one of {FORMAT_FLAG_FIELDS} must be true")
            elif len(true_flags) > 1:
                flags.append(f"Format flags — multiple set ({true_flags}); exactly one must be true")

            # 5c. statsCategories each sum to 100.0 (±0.15)
            cats_data = pd.get("statsCategories") or []
            if cats_data:
                for cat_type in ("GEOGRAPHY", "INVESTOR"):
                    ok, total = _stats_sum_ok(cats_data, cat_type)
                    if not ok:
                        flags.append(
                            f"`statsCategories` {cat_type} sums to {total:.1f} — must be 100.0"
                        )

    return flags


def process_message(br: BondRadar, msg: dict, delta_path: str) -> str:
    """Process one Slack message. Returns verdict string."""
    ts = msg["ts"]
    text = msg.get("text") or ""

    # ── 1. Non-deal skip ───────────────────────────────────────────────────
    # Only check the first 5 lines — real tender/LM/buyback messages declare
    # themselves at the top. New-issue messages that merely mention "Tender Offer"
    # in use-of-proceeds deep in the body must not be skipped.
    header_text = "\n".join(text.splitlines()[:5])
    if NON_DEAL_PATTERNS.search(header_text):
        print(f"  {ts}: non-deal keywords detected — skipping")
        _write_delta(delta_path, ts, "skipped")
        return "skipped"

    # ── 2. Find deal in BR ─────────────────────────────────────────────────
    # Extract issuer from first *** / ★★★ / €€€ header line
    # Bloomberg messages start with a stage word before the colon: "PRICED: Issuer Name..."
    # In that case the stage word is NOT the issuer — use the text after the colon instead.
    _STAGE_PREFIX_RE = re.compile(
        r"^(PRICED|ICED|LAUNCH(?:ED)?|NEW\s+DEAL|FINAL\s+SPREAD|MANDATE"
        r"|GUIDANCE|FINAL\s+TERMS|ALLOCAT(?:ED|IONS?)|BOOK\s+UPDATE"
        r"|REVISED\s+GUIDANCE|UPDATE\s+\#?\d*|IPT[S]?)\s*[:\-]\s*",
        re.IGNORECASE,
    )
    issuer = None
    for line in text.splitlines():
        line = line.strip()
        # Strip common decorators
        clean = re.sub(r"^[*★€\s]+|[*★€\s]+$", "", line)
        if not clean:
            continue
        # If line starts with a stage prefix word, strip it and use the remainder
        clean = _STAGE_PREFIX_RE.sub("", clean)
        if not clean:
            continue
        # Take everything before the first " – " or ":"
        m = re.split(r"\s[–—-]\s|:", clean, maxsplit=1)
        candidate = m[0].strip()
        if len(candidate) > 4:
            issuer = candidate
            break

    if not issuer:
        print(f"  {ts}: could not parse issuer — deferring to Claude")
        return "needs_ai"

    hits = br.find_by_issuer(issuer)
    if not hits:
        print(f"  {ts}: issuer '{issuer}' not found in BR — deferring to Claude")
        return "needs_ai"

    deal = hits[0]
    cat = deal.get("_category", "hg")
    deal_id = deal["id"]
    headline = deal.get("headline") or ""
    stage = _stage_from_headline(headline) or "unknown"
    print(f"  {ts}: matched deal {deal_id} ({headline[:60]}) stage={stage}")

    # ── 3. Mechanical checks ───────────────────────────────────────────────
    flags = check_deal(br, cat, deal, text)

    if not flags:
        print(f"  {ts}: mechanical checks clean — deferring to Claude for content")
        return "needs_ai"

    # ── 4. Post mechanical flags ───────────────────────────────────────────
    # Find reactor (person who ✅'d the message)
    reactor_id = None
    for r in (msg.get("reactions") or []):
        if r.get("name") == "white_check_mark" and r.get("users"):
            reactor_id = r["users"][0]
            break

    mention = f"<@{reactor_id}>\n" if reactor_id else ""
    bullets = "\n".join(f"• {f}" for f in flags)
    post_text = (
        f"{mention}:warning: BR QA — id `{deal_id}` at {stage.replace('_',' ').title()} "
        f"— {len(flags)} field issue{'s' if len(flags) > 1 else ''}\n"
        f"Fix:\n{bullets}\n"
        f"_(automated · BR QA Checker)_"
    )

    _post(CHANNEL, ts, post_text)
    _react(CHANNEL, ts, "exclamation")
    _write_delta(delta_path, ts, "flagged")
    print(f"  {ts}: posted {len(flags)} mechanical flag(s)")
    return "flagged"


def main() -> int:
    shard_path = os.environ.get("SHARD_FILE", "shard_0.json")
    delta_path = os.environ.get("STATE_DELTA_FILE", "state_delta_0.json")

    if not Path(shard_path).exists():
        print("PRE_CHECK=needs_ai")
        return 0

    msgs = json.loads(Path(shard_path).read_text())
    if not msgs:
        print("PRE_CHECK=skipped_empty")
        return 0

    br = BondRadar()
    verdicts = []
    for msg in msgs:
        v = process_message(br, msg, delta_path)
        verdicts.append(v)
        print(f"  verdict: {v}")

    # If every message was handled (skipped or flagged mechanically) → no Claude needed
    if all(v in ("skipped", "flagged") for v in verdicts):
        print("PRE_CHECK=done")
        return 0

    print("PRE_CHECK=needs_ai")
    return 0


if __name__ == "__main__":
    sys.exit(main())
