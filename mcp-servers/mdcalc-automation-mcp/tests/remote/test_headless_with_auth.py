#!/usr/bin/env python3
"""
Direct test of MDCalcClient search functionality.
Tests if the browser context issue is in the client or server.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path for imports (go up two levels from tests/remote)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mdcalc_client import MDCalcClient

async def test():
    client = MDCalcClient()
    print("1. Initializing with authentication...")
    await client.initialize(headless=True, use_auth=True)  # Use saved auth state
    print(f"2. Browser: {client.browser}")
    print(f"3. Context: {client.context}")

    # Check if browser is actually connected
    print(f"4. Browser connected: {client.browser.is_connected()}")

    # Try creating a simple page and navigating to a simple URL first
    print("5. Testing basic navigation...")
    try:
        test_page = await client.context.new_page()
        print(f"   Test page created: {test_page}")
        print(f"   Browser still connected: {client.browser.is_connected()}")

        # Try a simple navigation first
        print("   Navigating to example.com...")
        await test_page.goto("https://example.com", wait_until='networkidle', timeout=30000)
        print(f"   SUCCESS! Page loaded: {test_page.url}")

        # Now try mdcalc.com homepage
        print("   Navigating to mdcalc.com homepage...")
        try:
            await test_page.goto("https://www.mdcalc.com", wait_until='networkidle', timeout=30000)
            print(f"   SUCCESS! MDCalc homepage loaded: {test_page.url}")
        except Exception as e:
            print(f"   FAILED on homepage: {e}")

        # Try navigating to a SPECIFIC calculator page
        print("   Navigating to specific calculator (HEART Score)...")
        try:
            await test_page.goto("https://www.mdcalc.com/calc/1752/heart-score", wait_until='networkidle', timeout=30000)
            print(f"   SUCCESS! Calculator page loaded: {test_page.url}")
        except Exception as e:
            print(f"   FAILED on calculator page: {e}")

        await test_page.close()
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()

    print("\n6. Testing get_calculator_details (CRITICAL for screenshots)...")
    try:
        details = await client.get_calculator_details("1752")  # HEART Score
        print(f"7. SUCCESS! Got calculator details")
        print(f"   Title: {details.get('title')}")
        print(f"   URL: {details.get('url')}")
        print(f"   Screenshot included: {bool(details.get('screenshot_base64'))}")
        if details.get('screenshot_base64'):
            print(f"   Screenshot size: {len(details['screenshot_base64'])} bytes")
    except Exception as e:
        print(f"7. ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n8. Testing execute_calculator (CRITICAL for calculations)...")
    try:
        result = await client.execute_calculator("1752", {
            "age": "≥65",
            "history": "Slightly suspicious",
            "ecg": "Normal",
            "risk_factors": "≥3",
            "troponin": "≤ normal limit"
        })
        print(f"9. SUCCESS! Calculator executed")
        print(f"   Score: {result.get('score')}")
        print(f"   Risk: {result.get('risk')}")
    except Exception as e:
        print(f"9. ERROR: {e}")
        import traceback
        traceback.print_exc()

    await client.cleanup()

if __name__ == "__main__":
    asyncio.run(test())
