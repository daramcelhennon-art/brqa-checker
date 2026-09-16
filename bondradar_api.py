#!/usr/bin/env python3
"""
Bond Radar admin API client used by the QA checker.

Reads cookies from cookies.json (produced by refresh_cookies.py).
On 401, invokes refresh_cookies.py and retries once.

Usage as a library:
    from bondradar_api import BondRadar
    br = BondRadar()
    hits = br.find_by_issuer("World Bank", categories=("hg","hy","em"))
    for deal in hits:
        print(deal["id"], deal["type"], deal["headline"])

Usage as a CLI (for the scheduled task to shell out to):
    python3 bondradar_api.py search "World Bank"
    python3 bondradar_api.py list hg 20
    python3 bondradar_api.py get hg 14620427
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence
from urllib import request, error

HERE = Path(__file__).resolve().parent
COOKIES_PATH = HERE / "cookies.json"
REFRESH_SCRIPT = HERE / "refresh_cookies.py"

BASE = "https://www.bondradar.com/admin/api"
DEFAULT_CATEGORIES: tuple[str, ...] = ("hg", "em")  # only valid MarketType slugs; HY/SSA/FIG are flags within items


class BondRadar:
    def __init__(self, cookies_path: Path = COOKIES_PATH):
        self.cookies_path = cookies_path
        self._load()

    def _load(self) -> None:
        if not self.cookies_path.exists():
            self._refresh()
        data = json.loads(self.cookies_path.read_text())
        self._cookies = data["cookies"]
        self._basic = data["basic_auth"]
        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in self._cookies)
        basic = base64.b64encode(
            f"{self._basic['user']}:{self._basic['pass']}".encode()
        ).decode()
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://www.bondradar.com/admin/",
            "Cookie": cookie_header,
            "Authorization": f"Basic {basic}",
            # Cloudflare in front of bondradar.com blocks the default Python UA.
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/151.0.0.0 Safari/537.36",
        }

    def _refresh(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REFRESH_SCRIPT)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"refresh_cookies.py failed (code {result.returncode}):\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

    def _get(self, path: str, *, retried: bool = False) -> object:
        req = request.Request(f"{BASE}{path}", headers=self._headers, method="GET")
        try:
            with request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except error.HTTPError as e:
            if e.code == 401 and not retried:
                self._refresh()
                self._load()
                return self._get(path, retried=True)
            raise

    def list_deals(self, category: str, page: int = 0, size: int = 20) -> list[dict]:
        payload = self._get(f"/news/{category}?page={page}&size={size}")
        return payload["content"] if isinstance(payload, dict) else []

    def get_news(self, category: str, news_id: int) -> dict:
        """Full news-detail response (includes tranches, dealHistory, pricedDeals summary)."""
        return self._get(f"/news/{category}/{news_id}")

    def get_priced_deal(self, category: str, priced_id: int) -> dict:
        """Full priced-deal form record — every field the admin UI shows.

        The frontend URL is `/admin/#/{cat}/priced-deals/{id}`; the API is
        `/priced-deals/{cat}/{id}` (cat=hg|em). Returns fields: fpr, spread,
        yield, fxRate, isin, figi, tier, dealBanks, priceEvolution, all the
        format/additional-info flags as booleans, etc.
        """
        return self._get(f"/priced-deals/{category}/{priced_id}")

    def find_by_issuer(
        self,
        issuer: str,
        categories: Sequence[str] = DEFAULT_CATEGORIES,
        pages: int = 3,
    ) -> list[dict]:
        needle_tokens = _tokenize(issuer)
        if not needle_tokens:
            return []
        scored: list[tuple[int, dict]] = []
        for cat in categories:
            for pg in range(pages):
                items = self.list_deals(cat, page=pg)
                if not items:
                    break
                for it in items:
                    score = _score_match(
                        needle_tokens,
                        borrower=it.get("borrowerName") or "",
                        headline=it.get("headline") or "",
                        message=it.get("message") or "",
                    )
                    if score > 0:
                        scored.append((score, {**it, "_category": cat, "_match_score": score}))
        # sort by score desc, then recency desc
        scored.sort(key=lambda t: (t[0], t[1].get("changed") or t[1].get("created") or ""), reverse=True)
        seen: set[int] = set()
        deduped: list[dict] = []
        for _, m in scored:
            if m["id"] in seen:
                continue
            seen.add(m["id"])
            deduped.append(m)
        return deduped


_STOP = {
    "THE", "AND", "OF", "A",
    # legal-form suffixes only — never strip "BANK", "GROUP" (they're often part of the name)
    "INC", "CORP", "CORPORATION", "LTD", "LIMITED", "PLC", "SA", "NV", "AG",
    "GMBH", "LLC", "CO", "HOLDINGS", "HOLDING",
}


def _tokenize(s: str) -> list[str]:
    import re
    s = s.upper()
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    return [t for t in s.split() if t not in _STOP and len(t) >= 2]


def _score_match(needle_tokens: list[str], *, borrower: str, headline: str, message: str) -> int:
    """
    Score how well the needle matches this deal. Higher = better match.
      100 = exact whole-tokens match in borrowerName
       80 = all needle tokens appear as whole words in borrowerName (order-free)
       60 = all needle tokens appear as whole words in headline
       30 = all needle tokens appear as whole words anywhere in message
        0 = no match
    """
    b_tokens = _tokenize(borrower)
    h_tokens = _tokenize(headline)
    m_tokens = _tokenize(message)

    if not needle_tokens:
        return 0
    if b_tokens == needle_tokens:
        return 100
    b_set, h_set, m_set = set(b_tokens), set(h_tokens), set(m_tokens)
    needle_set = set(needle_tokens)
    if needle_set.issubset(b_set):
        return 80
    if needle_set.issubset(h_set):
        return 60
    if needle_set.issubset(m_set):
        return 30
    return 0


# Fields in the deal record that Claude never checks — strip to save tokens.
_DEAL_STRIP = frozenset({
    "legacyId", "createdAt", "changedAt", "created", "changed",
    "priority", "borrowerId", "expectedPageIdStored", "expectedPages",
    "fromLinkedIncrease", "dealHistory",
})

# Fields in the priced record that Claude never checks.
_PRICED_STRIP = frozenset({
    "legacyId", "createdAt", "createdAtDate", "changedAt", "borrowerId",
    "pricingTime", "headlineComment", "expectedDealHistory",
    "increaseNominal", "increaseExchange", "increaseRetained",
    "nominalSecond", "nominalTotal", "exchangeTotal", "retainedTotal",
    "fxRate", "oldSpread", "bloombergNsnCode", "increaseExchange",
    "attachmentName", "attachmentId", "newAttachmentId", "attachmentExists",
    "ownAttachments", "parentPricedDeal", "copyFromPricedDeal",
    "fromExpectedDealId", "storyId", "currentTimeRequested",
    "priceEvolutionMigrated", "statsClassificationMigrated", "tierMigrated",
    "additionalInfoMigrated", "finalStatsMigrated", "rating", "grade",
    "increase", "lastIncrease", "messageFilled", "pricingMessage",
    "orderType", "ggb",
})


def _slim(d: object, strip: frozenset) -> object:
    if isinstance(d, dict):
        return {k: _slim(v, strip) for k, v in d.items() if k not in strip}
    if isinstance(d, list):
        return [_slim(i, strip) for i in d]
    return d


def _cli(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: bondradar_api.py {search ISSUER | list CAT [SIZE] | get CAT ID | news CAT ID | priced CAT ID}", file=sys.stderr)
        return 2
    br = BondRadar()
    cmd = argv[1]
    if cmd == "search":
        issuer = " ".join(argv[2:])
        hits = br.find_by_issuer(issuer)
        print(json.dumps(_slim(hits, _DEAL_STRIP), default=str))
    elif cmd == "list":
        cat = argv[2]
        size = int(argv[3]) if len(argv) > 3 else 20
        print(json.dumps(_slim(br.list_deals(cat, size=size), _DEAL_STRIP), default=str))
    elif cmd == "get":
        cat, dealid = argv[2], int(argv[3])
        for pg in range(20):
            items = br.list_deals(cat, page=pg)
            if not items:
                break
            for it in items:
                if it["id"] == dealid:
                    print(json.dumps(_slim(it, _DEAL_STRIP), default=str))
                    return 0
        print(f"deal {dealid} not found in {cat}", file=sys.stderr)
        return 1
    elif cmd == "news":
        cat, dealid = argv[2], int(argv[3])
        print(json.dumps(_slim(br.get_news(cat, dealid), _DEAL_STRIP), default=str))
    elif cmd == "priced":
        cat, priced_id = argv[2], int(argv[3])
        print(json.dumps(_slim(br.get_priced_deal(cat, priced_id), _PRICED_STRIP), default=str))
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
