#!/usr/bin/env python3
"""
Manual login helper for MDCalc.
Opens browser and lets you login manually, then saves the session.
"""

import os
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Ensure we can run this script directly
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def manual_login():
    """Open browser for manual login and save session."""

    recordings_dir = Path(__file__).parent.parent.parent / "recordings"
    auth_dir = recordings_dir / "auth"
    auth_dir.mkdir(parents=True, exist_ok=True)
    state_file = auth_dir / "mdcalc_auth_state.json"

    print("\n🔐 MDCalc Manual Login")
    print("=" * 50)
    print("\nThis will open a browser window.")
    print("Please:")
    print("1. Click 'Log in' in the top right")
    print("2. Enter your credentials in the modal")
    print("3. Complete the login")
    print("4. Press Enter here when you're logged in\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        print("📍 Opening MDCalc...")
        page.goto("https://www.mdcalc.com")

        print("\n👆 Browser is open. Please login manually.")
        print("   1. Click 'Log in' button in top right")
        print("   2. Fill in your email and password")
        print("   3. Click 'LOG IN' button in modal")

        input("\n✋ Press Enter here after you've successfully logged in...")

        # Check if logged in by looking for logout button or user menu
        print("\n🔍 Verifying login status...")

        try:
            # Check for signs of being logged in
            page.wait_for_selector("text=Log out, a[href*='logout'], .user-menu, [data-user]", timeout=5000)
            print("✅ Login successful!")
        except:
            print("⚠️  Could not verify login. Saving session anyway...")

        # Save authentication state
        print("💾 Saving authentication state...")
        context.storage_state(path=str(state_file))

        # Save cookies separately
        cookies = context.cookies()
        cookies_file = auth_dir / "cookies.json"
        with open(cookies_file, 'w') as f:
            json.dump(cookies, f, indent=2)

        print(f"✅ Session saved to: {state_file}")
        print(f"🍪 Cookies saved to: {cookies_file}")

        # Keep browser open for a moment
        print("\n📋 You can now close the browser.")
        input("Press Enter to close browser and exit...")

        browser.close()

    print("\n✅ Done! Your session has been saved.")
    print("\nYou can now use the authenticated recording scripts:")
    print("  python tools/recording-generator/record_interaction.py heart_score --auth")
    print("  python tools/recording-generator/record_with_auth.py heart_score")


if __name__ == "__main__":
    manual_login()