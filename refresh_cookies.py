#!/usr/bin/env python3
"""
Log into Bond Radar admin and persist auth cookies to cookies.json.

Two-layer auth:
  1. nginx Basic auth at the edge  -> handled via httpCredentials
  2. SPA user-level login form     -> yields JSESSIONID cookie

Reads BR_USERNAME / BR_PASSWORD / BR_NGINX_USER / BR_NGINX_PASS from
~/.bondradar-env (or the current env). Writes cookies to ./cookies.json
next to this file.

Run manually the first time to confirm selectors, then let the QA checker
invoke it on 401 to refresh.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COOKIES_PATH = HERE / "cookies.json"
ENV_FILE = Path.home() / ".bondradar-env"

ADMIN_URL = "https://www.bondradar.com/admin/"

# Cloudflare Access service-token headers — required since 2026-11-11 when
# CF Access SSO was placed in front of bondradar.com/admin. Without these,
# the browser hits the Cloudflare email-code challenge instead of the BR
# login page. Set CF_ACCESS_CLIENT_ID and CF_ACCESS_CLIENT_SECRET as GitHub
# Secrets (and locally in ~/.bondradar-env). The BR team creates the service
# token in Cloudflare Zero Trust → Access → Service Auth → Service Tokens.
CF_CLIENT_ID_ENV = "CF_ACCESS_CLIENT_ID"
CF_CLIENT_SECRET_ENV = "CF_ACCESS_CLIENT_SECRET"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> int:
    load_env_file(ENV_FILE)
    username = os.environ.get("BR_USERNAME")
    password = os.environ.get("BR_PASSWORD")
    nginx_user = os.environ.get("BR_NGINX_USER")
    nginx_pass = os.environ.get("BR_NGINX_PASS")
    missing = [
        n for n, v in [
            ("BR_USERNAME", username),
            ("BR_PASSWORD", password),
            ("BR_NGINX_USER", nginx_user),
            ("BR_NGINX_PASS", nginx_pass),
        ] if not v
    ]
    if missing:
        print(
            f"Missing env vars: {', '.join(missing)}. Set them in {ENV_FILE} "
            f"(chmod 600) or export them in the current shell / GH Secrets.",
            file=sys.stderr,
        )
        return 2

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "playwright is not installed. Run:\n"
            "  pip3 install playwright && python3 -m playwright install chromium",
            file=sys.stderr,
        )
        return 3

    with sync_playwright() as p:
        # Prefer system Chrome (no CDN download needed — avoids corp-proxy TLS issues).
        # Fall back to bundled Chromium if system Chrome isn't installed.
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            http_credentials={"username": nginx_user, "password": nginx_pass},
        )
        # Inject the CF_Authorization cookie before navigating so Cloudflare Access
        # lets the browser through to the Bond Radar login page.
        cf_auth = os.environ.get("CF_AUTHORIZATION", "")
        if cf_auth:
            context.add_cookies([{
                "name": "CF_Authorization",
                "value": cf_auth,
                "domain": "www.bondradar.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            }])
        page = context.new_page()
        page.goto(ADMIN_URL, wait_until="networkidle", timeout=30_000)

        # SPA takes a beat to render the login form. Wait for a password field.
        try:
            page.wait_for_selector('input[type="password"]', timeout=15_000)
        except Exception as e:
            html_dump = HERE / "_login_page_debug.html"
            html_dump.write_text(page.content())
            png_dump = HERE / "_login_page_debug.png"
            page.screenshot(path=str(png_dump), full_page=True)
            print(
                f"Never found a password field. Dumped {html_dump} and {png_dump} "
                f"— open them, find the actual username/password selectors, and update "
                f"USERNAME_SELECTOR / PASSWORD_SELECTOR / SUBMIT_SELECTOR below.",
                file=sys.stderr,
            )
            return 4

        # Best-effort discovery of the username input near the password field.
        # If your login form uses non-standard selectors, override these:
        USERNAME_SELECTOR = 'input[type="text"], input[type="email"], input[name*="user" i], input[name*="email" i]'
        PASSWORD_SELECTOR = 'input[type="password"]'
        SUBMIT_SELECTOR = 'button[type="submit"], button:has-text("Log in"), button:has-text("Login"), button:has-text("Sign in")'

        page.fill(USERNAME_SELECTOR, username)
        page.fill(PASSWORD_SELECTOR, password)
        page.click(SUBMIT_SELECTOR)

        # Give the SPA time to set cookies after successful login.
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass

        cookies = context.cookies()
        # Sanity: we need JSESSIONID from bondradar.com
        needed = {"JSESSIONID"}
        got = {c["name"] for c in cookies if "bondradar" in c.get("domain", "")}
        if not needed.issubset(got):
            html_dump = HERE / "_post_login_debug.html"
            html_dump.write_text(page.content())
            png_dump = HERE / "_post_login_debug.png"
            page.screenshot(path=str(png_dump), full_page=True)
            print(
                f"Login submitted but no JSESSIONID cookie was issued. "
                f"Dumped {html_dump} and {png_dump}. Cookies seen: "
                f"{sorted(c['name'] for c in cookies)}",
                file=sys.stderr,
            )
            return 5

        payload = {
            "cookies": cookies,
            "basic_auth": {"user": nginx_user, "pass": nginx_pass},
        }
        COOKIES_PATH.write_text(json.dumps(payload, indent=2))
        os.chmod(COOKIES_PATH, 0o600)
        print(f"Saved {len(cookies)} cookies to {COOKIES_PATH}")
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
