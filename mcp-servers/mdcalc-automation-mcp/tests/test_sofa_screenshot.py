#!/usr/bin/env python3
"""
Test script specifically for debugging SOFA calculator screenshot issues.
Run this directly to test without going through the MCP agent.
"""

import asyncio
import sys
import os
import base64
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mdcalc_client import MDCalcClient

async def test_sofa_screenshot():
    """Test screenshot capture for SOFA calculator specifically."""
    print("\n" + "="*60)
    print("Testing SOFA Calculator Screenshot Issue")
    print("="*60)
    print("\nThis test will:")
    print("1. Open SOFA calculator")
    print("2. Try to capture screenshot")
    print("3. Save it to file so we can inspect what's captured")
    print("4. Check if PaO2/FiO2 fields are included")
    print("="*60)

    client = MDCalcClient()

    try:
        # Initialize with headless=False so we can see what's happening
        print("\n1. Initializing browser (visible mode)...")
        await client.initialize(headless=False)

        # Test SOFA calculator specifically
        calculator_id = "691"  # SOFA Score

        print(f"\n2. Loading SOFA calculator (ID: {calculator_id})...")
        print("   Watch the browser window to see what happens...")

        # Add a pause so we can see the initial state
        await asyncio.sleep(2)

        print("\n3. Getting calculator details (this triggers screenshot)...")
        details = await client.get_calculator_details(calculator_id)

        print(f"\n4. Results:")
        print(f"   - Title: {details.get('title')}")
        print(f"   - URL: {details.get('url')}")
        print(f"   - Fields detected: {details.get('fields_detected')}")
        print(f"   - Screenshot captured: {details.get('screenshot_included')}")

        # Save screenshot to file for inspection
        if details.get('screenshot_base64'):
            screenshot_data = base64.b64decode(details['screenshot_base64'])

            # Create screenshots directory if it doesn't exist
            screenshots_dir = Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)

            # Save in screenshots directory with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = screenshots_dir / f"sofa_screenshot_{timestamp}.jpg"

            with open(output_file, 'wb') as f:
                f.write(screenshot_data)

            print(f"\n5. Screenshot saved to: {output_file}")
            print(f"   - Size: {len(screenshot_data):,} bytes ({len(screenshot_data)//1024}KB)")
            print(f"   - Base64 size: {len(details['screenshot_base64']):,} characters")

            # Try to open the screenshot (works on macOS)
            try:
                os.system(f"open {output_file}")
                print(f"\n6. Screenshot opened in default viewer")
            except:
                print(f"\n6. Please manually open: {output_file}")

            print("\n" + "="*60)
            print("PLEASE CHECK THE SCREENSHOT:")
            print("="*60)
            print("❓ Does it show PaO₂ field at the top?")
            print("❓ Does it show FiO₂ field?")
            print("❓ Does it show 'On mechanical ventilation'?")
            print("❓ Does it show all fields down to Creatinine?")
            print("\nIf PaO₂/FiO₂ are missing, the screenshot is starting too low!")
            print("="*60)

            # Keep browser open for inspection
            print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
            await asyncio.sleep(10)

        else:
            print("\n❌ ERROR: No screenshot was captured!")

    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n7. Cleaning up...")
        await client.cleanup()
        print("   Test complete!")

async def test_with_debug_logging():
    """Run the same test but with debug logging enabled."""
    # Enable detailed logging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    await test_sofa_screenshot()

def main():
    """Main entry point."""
    print("\n🧪 SOFA Screenshot Debug Test")
    print("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        print("Running with DEBUG logging enabled...")
        asyncio.run(test_with_debug_logging())
    else:
        asyncio.run(test_sofa_screenshot())

if __name__ == "__main__":
    main()