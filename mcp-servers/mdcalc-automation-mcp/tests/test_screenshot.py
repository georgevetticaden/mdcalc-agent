#!/usr/bin/env python3
"""
Test screenshot capability for universal calculator support.
Tests various calculators including simple and complex ones.
"""

import asyncio
import sys
import os
import base64
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mdcalc_client import MDCalcClient


async def test_single_calculator(client, calc_id, calc_name, save_screenshot=True):
    """Test screenshot capture for a single calculator."""
    print(f"\n📸 Testing {calc_name} (ID: {calc_id})...")
    print("-" * 40)

    try:
        details = await client.get_calculator_details(calc_id)

        print(f"✅ Title: {details.get('title', 'Unknown')}")
        print(f"✅ URL: {details.get('url', 'Unknown')}")
        print(f"✅ Fields detected: {details.get('fields_detected', 0)}")

        if 'screenshot_base64' in details and details['screenshot_base64']:
            screenshot_data = details['screenshot_base64']
            screenshot_bytes = base64.b64decode(screenshot_data)

            size_kb = len(screenshot_bytes) / 1024
            print(f"✅ Screenshot captured: {size_kb:.1f} KB")

            if save_screenshot:
                # Save to screenshots folder with timestamp
                screenshots_dir = Path(__file__).parent / "screenshots"
                screenshots_dir.mkdir(exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = calc_name.replace(" ", "_").replace("/", "_")
                output_path = screenshots_dir / f"{safe_name}_{timestamp}.jpg"

                with open(output_path, 'wb') as f:
                    f.write(screenshot_bytes)
                print(f"✅ Screenshot saved to: {output_path.name}")

                # Check for quality issues
                if size_kb > 100:
                    print("⚠️  Screenshot larger than 100KB")
                elif size_kb < 20:
                    print("⚠️  Screenshot might be too low quality")

            return True
        else:
            print("❌ No screenshot captured")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_all_calculators(client):
    """Test all calculators including original and complex ones."""
    print("\n" + "="*60)
    print("Testing All Calculators")
    print("="*60)

    test_calculators = [
        # Original calculators from first test
        ("1752", "HEART_Score"),
        ("801", "CHA2DS2_VASc"),

        # Complex/Long calculators
        ("691", "SOFA_Score"),
        ("1868", "APACHE_II_Score"),

        # Additional calculators for variety
        ("43", "Creatinine_Clearance"),
        ("807", "HAS_BLED_Score"),
        ("64", "Glasgow_Coma_Scale"),
    ]

    results = []
    for calc_id, calc_name in test_calculators:
        success = await test_single_calculator(client, calc_id, calc_name)
        results.append((calc_name, success))
        await asyncio.sleep(1)  # Brief pause between calculators

    return results


async def main_test_suite(headless=False):
    """Main test suite for screenshot functionality."""
    print("\n🧪 MDCalc Screenshot Test Suite")
    print("=" * 60)

    client = MDCalcClient()

    # Enable debug logging if requested
    if "--debug" in sys.argv:
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    try:
        print(f"\nInitializing browser (headless={headless})...")
        await client.initialize(headless=headless)

        # Run the main test
        results = await test_all_calculators(client)

        # Print results summary
        print("\n" + "="*60)
        print("Test Results Summary:")
        print("="*60)
        for name, success in results:
            status = "✅" if success else "❌"
            print(f"{status} {name}")

        # Keep browser open briefly if not headless
        if not headless:
            print("\n⏸️  Browser will close in 5 seconds...")
            await asyncio.sleep(5)

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nCleaning up...")
        await client.cleanup()
        print("✅ Test suite complete!")


def print_usage():
    """Print usage instructions."""
    print("\nUsage: python test_screenshot.py [options]")
    print("\nOptions:")
    print("  --debug   - Enable debug logging")
    print("  --headless - Run in headless mode")
    print("\nExamples:")
    print("  python test_screenshot.py")
    print("  python test_screenshot.py --debug")
    print("  python test_screenshot.py --headless")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        sys.exit(0)

    # Parse command line arguments
    headless = "--headless" in sys.argv

    # Run the test suite
    asyncio.run(main_test_suite(headless=headless))