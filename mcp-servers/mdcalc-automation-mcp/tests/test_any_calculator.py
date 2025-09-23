#!/usr/bin/env python3
"""
Universal MDCalc Calculator Tester
Test ANY calculator to verify the automation works correctly.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mdcalc_client import MDCalcClient


class UniversalCalculatorTester:
    """Test any MDCalc calculator to ensure compatibility."""

    def __init__(self):
        self.client = None
        self.test_results = []

    async def initialize(self, headless=True):
        """Initialize the test client."""
        self.client = MDCalcClient()
        await self.client.initialize(headless=headless)

    async def test_calculator(self, calc_id: str, test_inputs: Dict = None, verbose=True):
        """
        Test a specific calculator.

        Args:
            calc_id: Calculator ID (e.g., "1752") or slug (e.g., "wells-pe")
            test_inputs: Optional manual test inputs. If None, will auto-generate.
            verbose: Print detailed output
        """
        print(f"\n{'='*60}")
        print(f"Testing Calculator: {calc_id}")
        print(f"{'='*60}")

        result = {
            'calculator_id': calc_id,
            'success': False,
            'errors': [],
            'details': {}
        }

        try:
            # Step 1: Get calculator details
            print("\n📋 Step 1: Getting calculator details...")
            details = await self.client.get_calculator_details(calc_id)

            if not details or not details.get('title'):
                result['errors'].append("Failed to load calculator page")
                print("❌ Failed to load calculator")
                return result

            result['details']['title'] = details.get('title', 'Unknown')
            result['details']['fields_count'] = len(details.get('fields', []))

            print(f"✅ Title: {details['title']}")
            print(f"✅ Found {len(details.get('fields', []))} input fields")

            if verbose and details.get('fields'):
                print("\n📝 Field Structure:")
                for field in details['fields']:
                    print(f"\n  • {field['label']} ({field['name']})")
                    if field.get('options'):
                        for opt in field['options'][:3]:  # Show first 3 options
                            print(f"    - {opt['text']}")
                        if len(field['options']) > 3:
                            print(f"    ... and {len(field['options']) - 3} more options")

            # Step 2: Generate or use test inputs
            if test_inputs:
                print(f"\n🔧 Step 2: Using provided test inputs")
                inputs = test_inputs
            else:
                print(f"\n🔧 Step 2: Auto-generating test inputs")
                inputs = self.generate_test_inputs(details)
                if verbose:
                    print("Generated inputs:")
                    for key, value in inputs.items():
                        print(f"  • {key}: {value}")

            if not inputs:
                result['errors'].append("Could not generate test inputs")
                print("❌ No inputs to test with")
                return result

            # Step 3: Execute calculator
            print(f"\n🚀 Step 3: Executing calculator with test inputs...")
            execution_result = await self.client.execute_calculator(calc_id, inputs)

            if execution_result.get('success'):
                result['success'] = True
                result['details']['score'] = execution_result.get('score')
                result['details']['risk'] = execution_result.get('risk')

                print(f"✅ Execution successful!")
                if execution_result.get('score'):
                    print(f"   Score: {execution_result['score']}")
                if execution_result.get('risk'):
                    # Clean up risk text
                    risk_text = execution_result['risk']
                    if len(risk_text) > 100:
                        risk_text = risk_text[:100] + "..."
                    print(f"   Risk: {risk_text}")
                if execution_result.get('interpretation'):
                    interp = execution_result['interpretation']
                    if len(interp) > 100:
                        interp = interp[:100] + "..."
                    print(f"   Interpretation: {interp}")
            else:
                result['errors'].append("Execution failed")
                print("⚠️  Execution completed but no results extracted")
                print(f"   Raw result: {execution_result}")

        except Exception as e:
            result['errors'].append(str(e))
            print(f"❌ Error: {e}")

        self.test_results.append(result)
        return result

    def generate_test_inputs(self, details: Dict) -> Dict:
        """
        Auto-generate SIMPLE test inputs based on field structure.
        This is just for testing - Claude Agent will do intelligent mapping in production.
        """
        inputs = {}
        fields = details.get('fields', [])

        for field in fields:
            field_name = field['name']
            field_label = field.get('label', field_name)
            options = field.get('options', [])

            if options:
                # For button/select fields, pick middle option
                middle_index = len(options) // 2
                if middle_index >= len(options):
                    middle_index = 0
                selected_option = options[middle_index]
                inputs[field_name] = selected_option['text']

            else:
                # For numeric/text inputs, generate simple test values
                # This is where Claude would do intelligent mapping in production
                field_label_lower = field_label.lower()

                # Simple test values for common field types
                if 'age' in field_label_lower:
                    inputs[field_name] = '65'
                elif 'cholesterol' in field_label_lower or 'ldl' in field_label_lower:
                    inputs[field_name] = '130'
                elif 'hdl' in field_label_lower:
                    inputs[field_name] = '45'
                elif 'triglyceride' in field_label_lower:
                    inputs[field_name] = '150'
                elif 'creatinine' in field_label_lower:
                    inputs[field_name] = '1.2'
                elif 'weight' in field_label_lower:
                    inputs[field_name] = '70'
                elif 'height' in field_label_lower:
                    inputs[field_name] = '170'
                elif 'pressure' in field_label_lower or 'bp' in field_label_lower:
                    inputs[field_name] = '120'
                elif 'glucose' in field_label_lower or 'sugar' in field_label_lower:
                    inputs[field_name] = '110'
                elif 'sodium' in field_label_lower or 'na' in field_label_lower:
                    inputs[field_name] = '140'
                elif 'potassium' in field_label_lower or 'k' in field_label_lower:
                    inputs[field_name] = '4.0'
                else:
                    # Generic default for unknown numeric fields
                    inputs[field_name] = '100'

        return inputs

    async def test_multiple_calculators(self, calculator_list: List[Dict]):
        """
        Test multiple calculators.

        Args:
            calculator_list: List of dicts with 'id' and optional 'inputs'
                           e.g., [{'id': '1752', 'inputs': {...}}, {'id': 'wells-pe'}]
        """
        print("\n" + "="*60)
        print("BATCH TESTING MULTIPLE CALCULATORS")
        print("="*60)

        for calc_info in calculator_list:
            calc_id = calc_info.get('id')
            test_inputs = calc_info.get('inputs')

            await self.test_calculator(calc_id, test_inputs)

            # Brief pause between tests
            await asyncio.sleep(1)

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        total = len(self.test_results)
        successful = sum(1 for r in self.test_results if r['success'])

        print(f"\nTotal calculators tested: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")

        if total > 0:
            print(f"Success rate: {(successful/total)*100:.1f}%")

        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            title = result['details'].get('title', 'Unknown')
            print(f"\n{status} {result['calculator_id']}: {title}")
            if result['errors']:
                for error in result['errors']:
                    print(f"   Error: {error}")
            if result['success']:
                if result['details'].get('score'):
                    print(f"   Score: {result['details']['score']}")

    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.cleanup()


# Predefined test sets for common calculator types
TEST_SETS = {
    'cardiac': [
        {'id': '1752', 'name': 'HEART Score'},
        {'id': '111', 'name': 'TIMI Score'},
        {'id': '1858', 'name': 'CHADS2 Score'},
        {'id': '801', 'name': 'CHA2DS2-VASc'},
        {'id': '1785', 'name': 'HAS-BLED Score'}
    ],
    'respiratory': [
        {'id': '324', 'name': 'CURB-65'},
        {'id': '33', 'name': 'PSI/PORT Score'},
        {'id': '4062', 'name': 'SMART-COP'},
        {'id': '797', 'name': 'BODE Index'},
        {'id': '3916', 'name': 'qSOFA'}
    ],
    'emergency': [
        {'id': '115', 'name': 'Wells Criteria for PE'},
        {'id': '1750', 'name': 'PERC Rule'},
        {'id': '347', 'name': 'Canadian CT Head Rule'},
        {'id': '608', 'name': 'NEXUS Criteria'},
        {'id': '64', 'name': 'Glasgow Coma Scale'}
    ],
    'renal': [
        {'id': '43', 'name': 'Creatinine Clearance'},
        {'id': '76', 'name': 'MDRD GFR'},
        {'id': '3939', 'name': 'CKD-EPI'},
        {'id': '2316', 'name': 'FENa'},
        {'id': '60', 'name': 'Corrected Calcium'}
    ],
    'hepatic': [
        {'id': '78', 'name': 'MELD Score'},
        {'id': '340', 'name': 'Child-Pugh Score'},
        {'id': '2693', 'name': 'FIB-4 Index'},
        {'id': '2200', 'name': 'APRI Score'},
        {'id': '3081', 'name': 'NAFLD Fibrosis Score'}
    ],
    'sepsis': [
        {'id': '691', 'name': 'SOFA Score'},
        {'id': '3916', 'name': 'qSOFA'},
        {'id': '1096', 'name': 'APACHE II'},
        {'id': '1868', 'name': 'SIRS Criteria'},
        {'id': '1875', 'name': 'NEWS Score'}
    ]
}


async def main():
    """Main test runner."""
    tester = UniversalCalculatorTester()

    print("MDCalc Universal Calculator Tester")
    print("="*60)
    print("\nOptions:")
    print("1. Test specific calculator by ID/slug/name")
    print("2. Test predefined set (cardiac, respiratory, emergency, etc.)")
    print("3. Test custom list")
    print("4. Quick test (5 diverse calculators)")
    print("5. Search for calculator by name")

    choice = input("\nEnter choice (1-5): ").strip()

    # Set headless mode
    headless_input = input("Run headless? (y/n, default=n): ").strip().lower()
    headless = headless_input == 'y'

    await tester.initialize(headless=headless)

    try:
        if choice == "1":
            # Test specific calculator
            calc_id = input("Enter calculator ID or slug (e.g., '1752' or 'wells-pe'): ").strip()

            custom_inputs = input("Provide custom inputs? (y/n): ").strip().lower()
            if custom_inputs == 'y':
                print("\nEnter inputs as JSON (e.g., {'age': '45-64', 'history': 'slightly_suspicious'}):")
                inputs_str = input().strip()
                try:
                    inputs = json.loads(inputs_str.replace("'", '"'))
                except:
                    print("Invalid JSON, will auto-generate inputs")
                    inputs = None
            else:
                inputs = None

            await tester.test_calculator(calc_id, inputs)

        elif choice == "2":
            # Test predefined set
            print("\nAvailable sets:")
            for key in TEST_SETS.keys():
                print(f"  - {key}")

            set_name = input("Enter set name: ").strip().lower()
            if set_name in TEST_SETS:
                calc_list = [{'id': calc['id']} for calc in TEST_SETS[set_name]]
                await tester.test_multiple_calculators(calc_list)
            else:
                print("Invalid set name")

        elif choice == "3":
            # Test custom list
            print("\nEnter calculator IDs separated by commas (e.g., 1752,324,691):")
            ids_str = input().strip()
            ids = [id.strip() for id in ids_str.split(',')]
            calc_list = [{'id': id} for id in ids]
            await tester.test_multiple_calculators(calc_list)

        elif choice == "4":
            # Quick diverse test
            print("\nRunning quick test with 5 diverse calculators...")
            diverse_calcs = [
                {'id': '1752'},  # HEART Score (cardiac)
                {'id': '324'},   # CURB-65 (respiratory)
                {'id': '115'},   # Wells PE (emergency)
                {'id': '43'},    # Creatinine Clearance (renal)
                {'id': '691'}    # SOFA Score (sepsis)
            ]
            await tester.test_multiple_calculators(diverse_calcs)

        elif choice == "5":
            # Search for calculator
            print("\nEnter calculator name to search for:")
            search_term = input().strip()

            print(f"\nSearching for '{search_term}'...")
            search_results = await tester.client.search_calculators(search_term, limit=5)

            if search_results:
                print(f"\nFound {len(search_results)} results:")
                for i, result in enumerate(search_results, 1):
                    print(f"{i}. {result['title']}")
                    print(f"   ID: {result.get('id', 'Unknown')}")
                    print(f"   URL: {result.get('url', '')}")

                selection = input("\nEnter selection (1-5) or calculator ID directly (or 0 to cancel): ").strip()
                if selection and selection != "0":
                    try:
                        # Check if it's a small number (1-5) for list selection
                        num = int(selection)
                        if 1 <= num <= len(search_results):
                            # List selection
                            calc_id = search_results[num - 1].get('id')
                            if calc_id:
                                print(f"\n✅ Selected: {search_results[num - 1]['title']}")
                                await tester.test_calculator(calc_id)
                            else:
                                print("Could not extract calculator ID")
                        else:
                            # Might be a direct calculator ID
                            print(f"\n📊 Testing calculator ID: {selection}")
                            await tester.test_calculator(selection)
                    except ValueError:
                        # Not a number, might be a slug
                        print(f"\n📊 Testing calculator: {selection}")
                        await tester.test_calculator(selection)
                    except Exception as e:
                        print(f"Error: {e}")
            else:
                print("No calculators found")

        else:
            print("Invalid choice")

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())