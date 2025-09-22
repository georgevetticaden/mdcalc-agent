#!/usr/bin/env python3
"""
Test script to verify recording infrastructure is working.
Run this to test the recording setup before actual MDCalc recordings.
"""

import sys
import os
from pathlib import Path

# Add parent directory and tools directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / "tools" / "recording-generator"))

from record_interaction import MDCalcRecorder


def main():
    """Test the recording infrastructure."""
    print("=" * 60)
    print("MDCalc Recording Infrastructure Test")
    print("=" * 60)

    recorder = MDCalcRecorder()

    print("\nThis test will:")
    print("1. Open a browser window")
    print("2. Navigate to MDCalc")
    print("3. Open Playwright Inspector")
    print("4. Allow you to interact with the page")
    print("5. Save recordings when you close the browser")

    print("\n⚠️  IMPORTANT:")
    print("   - The Playwright Inspector will pause execution")
    print("   - Interact with MDCalc manually")
    print("   - Close the browser when done")

    input("\nPress Enter to start test recording...")

    try:
        # Test with navigation scenario
        har_file = recorder.record_interaction("test_navigation", headless=False)
        print(f"\n✅ Test recording successful!")
        print(f"📁 Recording saved to: {har_file}")

        # Check if selectors can be parsed
        from parse_recording import RecordingParser
        parser = RecordingParser()

        print("\n🔍 Testing selector parsing...")
        selectors = parser.parse_all_recordings()

        if selectors:
            print("✅ Selector parsing successful!")
            print(f"   Found {len(selectors.get('selectors', {}))} scenario recordings")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return 1

    print("\n✅ All tests passed! Recording infrastructure is ready.")
    print("\nNext steps:")
    print("1. Run: python tools/recording-generator/record_interaction.py heart_score")
    print("2. Record interactions with the HEART Score calculator")
    print("3. Parse recordings: python tools/recording-generator/parse_recording.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())