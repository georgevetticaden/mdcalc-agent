#!/usr/bin/env python3
"""
Test screenshot capability for universal calculator support.
"""

import asyncio
import sys
import base64
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mdcalc_client import MDCalcClient


async def test_screenshot_capture():
    """Test that screenshot capture works and returns base64 data."""
    client = MDCalcClient()

    print("\n" + "="*60)
    print("Testing Screenshot Capability")
    print("="*60)

    await client.initialize(headless=False)  # Show browser for debugging

    try:
        # Test with HEART Score calculator
        print("\n📸 Testing screenshot for HEART Score (ID: 1752)...")
        details = await client.get_calculator_details("1752")

        print(f"✅ Title: {details.get('title', 'Unknown')}")
        print(f"✅ URL: {details.get('url', 'Unknown')}")
        print(f"✅ Found {len(details.get('fields', []))} fields")

        if 'screenshot_base64' in details:
            screenshot_data = details['screenshot_base64']
            screenshot_bytes = base64.b64decode(screenshot_data)

            print(f"✅ Screenshot captured: {len(screenshot_bytes)} bytes")
            print(f"✅ Base64 length: {len(screenshot_data)} characters")

            # Save to dedicated screenshots folder
            screenshots_dir = Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)

            output_path = screenshots_dir / "heart_score_screenshot.jpg"
            with open(output_path, 'wb') as f:
                f.write(screenshot_bytes)
            print(f"✅ Screenshot saved to: {output_path}")

            # Estimate file size
            size_kb = len(screenshot_bytes) / 1024
            print(f"✅ File size: {size_kb:.1f} KB")

            if size_kb > 100:
                print("⚠️  Screenshot larger than 100KB, consider adjusting quality")
        else:
            print("❌ No screenshot captured")

        # Test with another calculator
        print("\n📸 Testing screenshot for CHA2DS2-VASc (ID: 801)...")
        details2 = await client.get_calculator_details("801")

        if 'screenshot_base64' in details2:
            screenshot_bytes2 = base64.b64decode(details2['screenshot_base64'])
            size_kb2 = len(screenshot_bytes2) / 1024
            print(f"✅ CHA2DS2-VASc screenshot: {size_kb2:.1f} KB")

            # Save this screenshot too
            output_path2 = screenshots_dir / "cha2ds2_vasc_screenshot.jpg"
            with open(output_path2, 'wb') as f:
                f.write(screenshot_bytes2)
            print(f"✅ Screenshot saved to: {output_path2}")
        else:
            print("❌ No screenshot captured for CHA2DS2-VASc")

    finally:
        await client.cleanup()

    print("\n✅ Screenshot test complete!")
    print("\nThis screenshot capability enables Claude to:")
    print("1. SEE all calculator fields visually")
    print("2. UNDERSTAND complex UI patterns")
    print("3. WORK with any of the 900+ calculators")
    print("4. HANDLE dynamic React components")


if __name__ == "__main__":
    asyncio.run(test_screenshot_capture())