#!/usr/bin/env python3
"""
Test Known Calculators
Focus on testing mechanics with calculators we understand well.
Not trying to solve "any calculator" - that's Claude's job with vision!
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mdcalc_client import MDCalcClient


class KnownCalculatorTests:
    """Test suite for known calculators with predictable inputs."""

    def __init__(self):
        self.client = None
        self.test_results = []

    async def initialize(self, headless=True):
        """Initialize the test client."""
        self.client = MDCalcClient()
        await self.client.initialize(headless=headless)

    async def test_heart_score(self) -> Dict:
        """
        Test HEART Score (ID: 1752) - Button-based calculator
        """
        print("\n" + "="*60)
        print("Testing HEART Score (Button-based)")
        print("="*60)

        result = {"calculator": "HEART Score", "success": False}

        try:
            # Get calculator details
            print("Getting calculator details...")
            details = await self.client.get_calculator_details("1752")
            print(f"✅ Title: {details.get('title', 'Unknown')}")
            print(f"✅ Found {len(details.get('fields', []))} fields")

            # Execute with known good inputs
            print("\nExecuting with test data...")
            # Use exact field names from UI, omit pre-selected fields
            test_inputs = {
                'History': 'Moderately suspicious',  # Capital H
                'Age': '45-64',
                'Risk factors': '1-2 risk factors'
                # Omitting pre-selected fields:
                # 'EKG': 'Normal' - already selected by default
                # 'Initial troponin': '≤normal limit' - already selected by default
            }

            execution_result = await self.client.execute_calculator("1752", test_inputs)

            if execution_result.get('success'):
                result['success'] = True
                result['score'] = execution_result.get('score')
                print(f"✅ Execution successful! Score: {execution_result.get('score')}")
            else:
                print("⚠️ Execution completed but no score extracted")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")

        self.test_results.append(result)
        return result

    async def test_ldl_calculated(self) -> Dict:
        """
        Test LDL Calculated (ID: 70) - Numeric input calculator
        """
        print("\n" + "="*60)
        print("Testing LDL Calculated (Numeric inputs)")
        print("="*60)

        result = {"calculator": "LDL Calculated", "success": False}

        try:
            # Get calculator details
            print("Getting calculator details...")
            details = await self.client.get_calculator_details("70")
            print(f"✅ Title: {details.get('title', 'Unknown')}")

            # Execute with known good inputs
            print("\nExecuting with test data...")
            # Use exact field names from UI (with spaces and capitals)
            test_inputs = {
                'Total Cholesterol': '200',
                'HDL Cholesterol': '50',
                'Triglycerides': '150'
            }

            execution_result = await self.client.execute_calculator("70", test_inputs)

            if execution_result.get('success'):
                result['success'] = True
                result['ldl_value'] = execution_result.get('score')
                print(f"✅ Execution successful! LDL: {execution_result.get('score')}")
            else:
                print("⚠️ Execution completed but no result extracted")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")

        self.test_results.append(result)
        return result

    async def test_cha2ds2_vasc(self) -> Dict:
        """
        Test CHA2DS2-VASc (ID: 801) - Mixed checkbox/button calculator
        """
        print("\n" + "="*60)
        print("Testing CHA2DS2-VASc (Mixed inputs)")
        print("="*60)

        result = {"calculator": "CHA2DS2-VASc", "success": False}

        try:
            # Get calculator details
            print("Getting calculator details...")
            details = await self.client.get_calculator_details("801")
            print(f"✅ Title: {details.get('title', 'Unknown')}")

            # Execute with known good inputs
            print("\nExecuting with test data...")
            # Use exact field names from UI
            # Only change fields from their defaults (all history fields default to "No")
            test_inputs = {
                'Age': '65-74',
                'Sex': 'Female',
                'CHF history': 'Yes',
                'Hypertension history': 'Yes',
                # Don't set these to 'No' - they're already at default 'No'
                # 'Stroke/TIA/thromboembolism history': 'No',
                # 'Vascular disease history': 'No',
                'Diabetes history': 'Yes'
            }

            execution_result = await self.client.execute_calculator("801", test_inputs)

            if execution_result.get('success'):
                result['success'] = True
                result['score'] = execution_result.get('score')
                print(f"✅ Execution successful! Score: {execution_result.get('score')}")
            else:
                print("⚠️ Execution completed but no score extracted")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")

        self.test_results.append(result)
        return result

    async def test_search_functionality(self) -> Dict:
        """
        Test search functionality
        """
        print("\n" + "="*60)
        print("Testing Search Functionality")
        print("="*60)

        result = {"test": "Search", "success": False}

        try:
            # Test search
            print("Searching for 'heart'...")
            search_results = await self.client.search_calculators("heart", limit=5)

            if search_results:
                result['success'] = True
                result['count'] = len(search_results)
                print(f"✅ Found {len(search_results)} results")

                # Show first result
                if search_results:
                    first = search_results[0]
                    print(f"   First result: {first.get('title')}")
                    print(f"   ID: {first.get('id')}")
            else:
                print("⚠️ No search results found")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")

        self.test_results.append(result)
        return result

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        total = len(self.test_results)
        successful = sum(1 for r in self.test_results if r.get('success'))

        print(f"\nTotal tests: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")

        if total > 0:
            print(f"Success rate: {(successful/total)*100:.1f}%")

        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result.get('success') else "❌"
            test_name = result.get('calculator', result.get('test', 'Unknown'))
            print(f"{status} {test_name}")
            if result.get('error'):
                print(f"   Error: {result['error']}")

    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.cleanup()


async def main():
    """Run tests for known calculators."""
    tester = KnownCalculatorTests()

    print("\n" + "="*60)
    print("MDCalc Known Calculator Tests")
    print("Testing mechanics with predictable calculators")
    print("(Claude handles 'any calculator' with vision)")
    print("="*60)

    # Ask about headless mode
    headless_input = input("\nRun headless? (y/n, default=y): ").strip().lower()
    headless = headless_input != 'n'

    await tester.initialize(headless=headless)

    try:
        # Run all tests
        await tester.test_search_functionality()
        await tester.test_heart_score()
        await tester.test_ldl_calculated()
        await tester.test_cha2ds2_vasc()

        # Print summary
        tester.print_summary()

    finally:
        await tester.cleanup()

    print("\n✅ Tests complete!")
    print("\nNote: These tests verify mechanics work.")
    print("Full 'any calculator' support happens when Claude uses vision in production.")


if __name__ == "__main__":
    asyncio.run(main())