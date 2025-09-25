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

    async def test_sofa_score(self) -> Dict:
        """
        Test SOFA Score (ID: 691) - Mixed numeric and dropdown inputs
        Using exact inputs from the demo scenario logs
        """
        print("\n" + "="*60)
        print("Testing SOFA Score (Mixed numeric/dropdown)")
        print("="*60)

        result = {"calculator": "SOFA Score", "success": False}

        try:
            # Get calculator details
            print("Getting calculator details...")
            details = await self.client.get_calculator_details("691")
            print(f"✅ Title: {details.get('title', 'Unknown')}")
            print(f"✅ Found {len(details.get('fields', []))} fields")

            # Execute with exact inputs from the logs
            # Note: MDCalc uses regular hyphens (-) for integer ranges, en dash (–) for decimal ranges
            print("\nExecuting with test data from demo scenario...")
            test_inputs = {
                'PaO₂': '90',  # Numeric input field
                'FiO₂': '60',  # Numeric input field
                'On mechanical ventilation': 'Yes',
                'Platelets, ×10³/μL': '50-99',  # Regular hyphen for integer range
                'Glasgow Coma Score': '10-12',  # Regular hyphen for integer range (also note capital S in Score)
                'Bilirubin, mg/dL': '2.0–5.9 (33-101)',  # En dash for decimal range, hyphen in parentheses
                'Mean arterial pressure OR administration of vasoactive agents required': 'MAP <70 mmHg',  # Note: "vasoactive agents" not "vasopressors", and includes "mmHg"
                'Creatinine, mg/dL (or urine output)': '2.0–3.4 (171-299)'  # En dash for decimal range, hyphen in parentheses
            }

            execution_result = await self.client.execute_calculator("691", test_inputs)

            if execution_result.get('success'):
                result['success'] = True
                result['score'] = execution_result.get('score')
                print(f"✅ Execution successful! SOFA Score: {execution_result.get('score')}")
            else:
                print("⚠️ Execution completed but no score extracted")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")

        self.test_results.append(result)
        return result

    async def test_apache_ii(self) -> Dict:
        """
        Test APACHE II (ID: 1868) - Complex calculator with many numeric inputs
        Using exact inputs from the demo scenario logs
        """
        print("\n" + "="*60)
        print("Testing APACHE II (Complex numeric inputs)")
        print("="*60)

        result = {"calculator": "APACHE II", "success": False}

        try:
            # Get calculator details
            print("Getting calculator details...")
            details = await self.client.get_calculator_details("1868")
            print(f"✅ Title: {details.get('title', 'Unknown')}")
            print(f"✅ Found {len(details.get('fields', []))} fields")

            # Execute with exact inputs from the logs
            # Based on the screenshot, APACHE II uses text inputs with normal ranges shown as placeholders
            print("\nExecuting with test data from demo scenario...")
            test_inputs = {
                'Age': '68',  # Numeric input field
                'Temperature': '38.5',  # Numeric input (Norm: 97-100)
                'Mean arterial pressure': '65',  # Numeric input (Norm: 70-100)
                'pH': '7.32',  # Numeric input (Norm: 7.38-7.44)
                'Heart rate/pulse': '115',  # Numeric input (Norm: 60-100)
                'Respiratory rate': '28',  # Numeric input (Norm: 12-20)
                'Sodium': '135',  # Numeric input (Norm: 136-145)
                'Potassium': '4.1',  # Numeric input (Norm: 3.5-5.2)
                'Creatinine': '1.8',  # Numeric input (Norm: 0.7-1.3)
                'Acute renal failure': 'Yes',  # Yes/No toggle
                'Hematocrit': '32',  # Numeric input (Norm: 36-51)
                'White blood cell count': '14',  # Numeric input (Norm: 3.7-10.7)
                'Glasgow Coma Scale': '10',  # Numeric input (Norm: 3-15)
                'FiO₂': '≥50%',  # Dropdown selection
                # After selecting FiO₂ ≥50%, A-a gradient field appears with range buttons
                'A-a gradient': '<200',  # Button selection for A-a gradient
                # Additional fields that are visible in the form
                'History of severe organ failure or immunocompromise': 'No',  # Yes/No toggle
                'Type of admission': 'Elective postoperative',  # Dropdown/button selection
            }

            execution_result = await self.client.execute_calculator("1868", test_inputs)

            if execution_result.get('success'):
                result['success'] = True
                result['score'] = execution_result.get('score')
                print(f"✅ Execution successful! APACHE II Score: {execution_result.get('score')}")
            else:
                print("⚠️ Execution completed but no score extracted")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")

        self.test_results.append(result)
        return result

    async def test_creatinine_clearance(self) -> Dict:
        """
        Test Creatinine Clearance (Cockcroft-Gault) (ID: 43) - Mixed numeric inputs with buttons
        This calculator has pre-selected "Female" and needs all numeric fields filled
        """
        print("\n" + "="*60)
        print("Testing Creatinine Clearance (Cockcroft-Gault)")
        print("="*60)

        result = {"calculator": "Creatinine Clearance", "success": False}

        try:
            # Get calculator details
            print("Getting calculator details...")
            details = await self.client.get_calculator_details("43")
            print(f"✅ Title: {details.get('title', 'Unknown')}")
            print(f"✅ Found {len(details.get('fields', []))} fields")

            # Execute with test data - all numeric fields must be filled
            print("\nExecuting with test data...")
            test_inputs = {
                'Age': '72',         # Numeric input
                'Sex': 'Female',     # Button selection (Female is pre-selected by default)
                'Weight': '172',     # Numeric input
                'Creatinine': '1.3', # Numeric input
                'Height': '64'       # Numeric input (optional but we'll provide it)
            }

            execution_result = await self.client.execute_calculator("43", test_inputs)

            if execution_result.get('success'):
                result['success'] = True
                result['creatinine_clearance'] = execution_result.get('score')
                print(f"✅ Execution successful! CrCl: {execution_result.get('score')}")
            else:
                print("⚠️ Execution completed but no result extracted")

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
    import argparse

    parser = argparse.ArgumentParser(description='Test MDCalc calculators')
    parser.add_argument('--calc', type=str, help='Specific calculator to test (heart, ldl, cha2ds2, sofa, apache, search)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--no-headless', dest='headless', action='store_false', help='Run with browser visible')
    parser.set_defaults(headless=None)

    args = parser.parse_args()

    tester = KnownCalculatorTests()

    print("\n" + "="*60)
    print("MDCalc Known Calculator Tests")
    print("Testing mechanics with predictable calculators")
    print("(Claude handles 'any calculator' with vision)")
    print("="*60)

    # Determine headless mode
    if args.headless is None:
        # Ask if not specified via command line
        headless_input = input("\nRun headless? (y/n, default=y): ").strip().lower()
        headless = headless_input != 'n'
    else:
        headless = args.headless

    await tester.initialize(headless=headless)

    try:
        # Run specific test or all tests
        if args.calc:
            calc_map = {
                'heart': tester.test_heart_score,
                'ldl': tester.test_ldl_calculated,
                'cha2ds2': tester.test_cha2ds2_vasc,
                'sofa': tester.test_sofa_score,
                'apache': tester.test_apache_ii,
                'creatinine': tester.test_creatinine_clearance,
                'search': tester.test_search_functionality
            }

            if args.calc.lower() in calc_map:
                print(f"\nRunning specific test: {args.calc}")
                await calc_map[args.calc.lower()]()
            else:
                print(f"Unknown calculator: {args.calc}")
                print(f"Available options: {', '.join(calc_map.keys())}")
                return
        else:
            # Run all tests
            await tester.test_search_functionality()
            await tester.test_heart_score()
            await tester.test_ldl_calculated()
            await tester.test_cha2ds2_vasc()
            await tester.test_creatinine_clearance()
            await tester.test_sofa_score()
            await tester.test_apache_ii()

        # Print summary
        tester.print_summary()

    finally:
        await tester.cleanup()

    print("\n✅ Tests complete!")
    print("\nNote: These tests verify mechanics work.")
    print("Full 'any calculator' support happens when Claude uses vision in production.")


if __name__ == "__main__":
    asyncio.run(main())