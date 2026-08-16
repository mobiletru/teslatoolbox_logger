#!/usr/bin/env python3
"""Log into Tesla Toolbox 3 (https://toolbox.tesla.com/) with Playwright.

Tesla's SSO (auth.tesla.com) is Akamai-protected. This script is meant to run
on a normal shop/home network, not a blocked datacenter IP.

Environment:
  TESLA_TOOLBOX_EMAIL     required
  TESLA_TOOLBOX_PASSWORD  required
  TESLA_TOOLBOX_OTP       optional TOTP/SMS code if MFA is enabled

On success, writes Playwright storage state to .toolbox-session.json so later
CAN Explorer runs can reuse the session.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

TOOLBOX_URL = "https://toolbox.tesla.com/"
SESSION_PATH = Path(".toolbox-session.json")


def env(name: str, required: bool = True) -> str:
    value = os.environ.get(name, "").strip()
    if required and not value:
        raise SystemExit(
            f"Missing {name}. Set it before running:\n"
            f"  export TESLA_TOOLBOX_EMAIL='you@shop.example'\n"
            f"  export TESLA_TOOLBOX_PASSWORD='…'\n"
            f"  export TESLA_TOOLBOX_OTP='123456'   # only if MFA is on"
        )
    return value


def first_visible(page, selectors: list[str], timeout_ms: int = 15000):
    last_error = None
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout_ms)
            return locator
        except PlaywrightTimeout as exc:
            last_error = exc
    raise PlaywrightTimeout(f"None of {selectors} became visible") from last_error


def wait_for_toolbox_home(page, timeout_ms: int = 120000) -> None:
    page.wait_for_url(
        lambda url: "toolbox.tesla.com" in url and "authorize" not in url,
        timeout=timeout_ms,
    )


def login(headed: bool, session_path: Path) -> None:
    email = env("TESLA_TOOLBOX_EMAIL")
    password = env("TESLA_TOOLBOX_PASSWORD")
    otp = env("TESLA_TOOLBOX_OTP", required=False)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=not headed,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(TOOLBOX_URL, wait_until="domcontentloaded", timeout=60000)

        if "Access Denied" in (page.title() + page.inner_text("body")):
            browser.close()
            raise SystemExit(
                "Tesla SSO returned Access Denied (Akamai). "
                "This IP/network is blocked from auth.tesla.com. "
                "Run this script from a shop or home network that can open "
                "https://toolbox.tesla.com/ in a normal browser."
            )

        # Tesla SSO identity step
        email_box = first_visible(
            page,
            [
                'input[name="identity"]',
                'input[name="email"]',
                'input[type="email"]',
                "#form-input-identity",
                'input[autocomplete="username"]',
            ],
        )
        email_box.fill(email)
        next_btn = page.locator(
            'button:has-text("Next"), button:has-text("Continue"), button[type="submit"]'
        ).first
        if next_btn.count():
            next_btn.click()

        password_box = first_visible(
            page,
            [
                'input[name="credential"]',
                'input[type="password"]',
                "#form-input-credential",
                'input[autocomplete="current-password"]',
            ],
        )
        password_box.fill(password)
        sign_in = page.locator(
            'button:has-text("Sign In"), button:has-text("Log In"), button[type="submit"]'
        ).first
        sign_in.click()

        # Optional MFA
        try:
            otp_box = first_visible(
                page,
                [
                    'input[name="passcode"]',
                    'input[name="code"]',
                    'input[autocomplete="one-time-code"]',
                    'input[inputmode="numeric"]',
                ],
                timeout_ms=8000,
            )
            if not otp:
                print(
                    "MFA prompt detected. Set TESLA_TOOLBOX_OTP or type the code in the browser.",
                    file=sys.stderr,
                )
                if headed:
                    page.wait_for_timeout(120_000)
                else:
                    raise SystemExit("MFA required: export TESLA_TOOLBOX_OTP and retry with --headed.")
            else:
                otp_box.fill(otp)
                page.locator('button[type="submit"], button:has-text("Verify")').first.click()
        except PlaywrightTimeout:
            pass

        try:
            wait_for_toolbox_home(page)
        except PlaywrightTimeout:
            screenshot = Path("toolbox-login-failed.png")
            page.screenshot(path=str(screenshot), full_page=True)
            raise SystemExit(
                f"Login did not reach Toolbox. Current URL: {page.url}\n"
                f"Screenshot: {screenshot}"
            )

        context.storage_state(path=str(session_path))
        print(f"Logged into Toolbox 3 as {email}")
        print(f"Session saved to {session_path.resolve()}")
        print(f"Landed on {page.url}")
        time.sleep(1)
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Log into Tesla Toolbox 3 with Playwright")
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Show the browser (recommended; MFA and recaptcha are easier)",
    )
    parser.add_argument(
        "--session",
        default=str(SESSION_PATH),
        help="Where to write Playwright storage state",
    )
    args = parser.parse_args()
    login(headed=args.headed, session_path=Path(args.session))


if __name__ == "__main__":
    main()
