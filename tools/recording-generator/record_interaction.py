#!/usr/bin/env python3
"""
MDCalc Interaction Recorder
Records user interactions with MDCalc website to extract selectors and patterns.
Uses Playwright's pause() for interactive recording and saves HAR files for analysis.
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
import argparse

# Ensure we can run this script directly
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MDCalcRecorder:
    """Records interactions with MDCalc for selector extraction."""

    def __init__(self, base_dir=None):
        """Initialize recorder with base directory for recordings."""
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent / "recordings"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir = self.base_dir / "videos"
        self.videos_dir.mkdir(exist_ok=True)

    def record_interaction(self, scenario_name, headless=False, use_auth=False):
        """
        Record interaction with MDCalc for a specific scenario.

        Args:
            scenario_name: Name of the scenario (e.g., 'heart_score', 'search')
            headless: Whether to run browser in headless mode
            use_auth: Whether to use saved authentication state
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        har_path = self.base_dir / f"{scenario_name}_{timestamp}.har"
        trace_path = self.base_dir / f"{scenario_name}_{timestamp}_trace.zip"

        print(f"\n🎬 Starting recording for: {scenario_name}")
        print(f"📁 Recordings will be saved to: {self.base_dir}")

        # Check for authentication state
        auth_state_file = self.base_dir / "auth" / "mdcalc_auth_state.json"
        if use_auth and auth_state_file.exists():
            print(f"🔐 Using saved authentication from: {auth_state_file}")
            storage_state = str(auth_state_file)
        else:
            storage_state = None
            if use_auth:
                print("⚠️  No saved authentication found. Recording without login.")
                print("   To login first: python tools/recording-generator/record_with_auth.py --login")

        with sync_playwright() as p:
            # Launch browser with recording capabilities
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )

            # Create context with recording enabled
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36',
                'record_har_path': str(har_path),
                'record_har_omit_content': False,
                'record_video_dir': str(self.videos_dir),
                'record_video_size': {'width': 1920, 'height': 1080}
            }

            # Add authentication state if available
            if storage_state:
                context_options['storage_state'] = storage_state

            context = browser.new_context(**context_options)

            # Start tracing for detailed capture
            context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True
            )

            # Create page
            page = context.new_page()

            # Navigate to MDCalc
            print("📍 Navigating to MDCalc...")
            page.goto("https://www.mdcalc.com", wait_until='networkidle')

            # Print instructions
            self._print_recording_instructions(scenario_name)

            # Pause for interactive recording
            # This opens Playwright Inspector for manual interaction
            page.pause()

            # After user closes the browser, save traces
            print("\n💾 Saving recording data...")

            # Stop tracing and save
            context.tracing.stop(path=str(trace_path))

            # Close context to finalize recordings
            context.close()
            browser.close()

        # Post-process the recording
        self._post_process_recording(har_path, scenario_name)

        print(f"\n✅ Recording complete!")
        print(f"📄 HAR file: {har_path}")
        print(f"🎯 Trace file: {trace_path}")
        print(f"🎥 Video saved in: {self.videos_dir}")

        return str(har_path)

    def _print_recording_instructions(self, scenario_name):
        """Print scenario-specific instructions for recording."""
        instructions = {
            'search': """
            🔍 SEARCH RECORDING INSTRUCTIONS:
            1. Click on the search box/icon
            2. Type a search term (e.g., "chest pain" or "HEART score")
            3. Wait for search results to appear
            4. Click on a calculator from results
            5. Note the selectors for search input and result cards
            """,

            'heart_score': """
            ❤️ HEART SCORE RECORDING INSTRUCTIONS:
            1. Navigate to HEART Score (search or direct)
            2. Fill in ALL inputs:
               - History (select option)
               - ECG (select option)
               - Age (enter value)
               - Risk factors (enter number)
               - Troponin (select option)
            3. Click Calculate button
            4. Wait for results to appear
            5. Note result display elements
            """,

            'cha2ds2_vasc': """
            🧠 CHA2DS2-VASc RECORDING INSTRUCTIONS:
            1. Navigate to CHA2DS2-VASc Score
            2. Fill in ALL checkboxes/inputs:
               - CHF history
               - Hypertension
               - Age ≥75
               - Diabetes
               - Stroke/TIA/TE
               - Vascular disease
               - Age 65-74
               - Sex category
            3. Click Calculate
            4. Observe result and recommendations
            """,

            'sofa': """
            🏥 SOFA SCORE RECORDING INSTRUCTIONS:
            1. Navigate to SOFA Score
            2. Fill in organ system parameters:
               - Respiration (PaO2/FiO2)
               - Coagulation (Platelets)
               - Liver (Bilirubin)
               - Cardiovascular (MAP/pressors)
               - CNS (GCS)
               - Renal (Creatinine/UOP)
            3. Calculate and observe results
            """,

            'navigation': """
            🧭 NAVIGATION RECORDING INSTRUCTIONS:
            1. Explore the homepage
            2. Click on specialty categories
            3. Browse calculator lists
            4. Use filters if available
            5. Note navigation patterns
            """
        }

        print(instructions.get(scenario_name, """
            📝 GENERAL RECORDING INSTRUCTIONS:
            1. Interact with the calculator/feature
            2. Fill in relevant inputs
            3. Execute calculations
            4. Observe results
            5. Close browser when done
        """))

        print("\n⏸️  Playwright Inspector is now open.")
        print("👆 Interact with the page manually.")
        print("✅ Close the browser when you're done recording.\n")

    def _post_process_recording(self, har_path, scenario_name):
        """Extract and save selectors from HAR file."""
        if not har_path.exists():
            return

        try:
            with open(har_path, 'r') as f:
                har_data = json.load(f)

            # Extract interactions from HAR
            selectors = self._extract_selectors_from_har(har_data, scenario_name)

            # Save selectors
            selectors_file = self.base_dir / f"{scenario_name}_selectors.json"
            with open(selectors_file, 'w') as f:
                json.dump(selectors, f, indent=2)

            print(f"📋 Selectors saved to: {selectors_file}")

        except Exception as e:
            print(f"⚠️ Could not post-process HAR file: {e}")

    def _extract_selectors_from_har(self, har_data, scenario_name):
        """Extract potential selectors from HAR data."""
        selectors = {
            "scenario": scenario_name,
            "timestamp": datetime.now().isoformat(),
            "extracted_patterns": {
                "search": [],
                "inputs": [],
                "buttons": [],
                "results": []
            }
        }

        # Analyze requests for form submissions
        for entry in har_data.get('log', {}).get('entries', []):
            request = entry.get('request', {})
            url = request.get('url', '')

            if 'mdcalc.com' in url:
                # Track API endpoints
                if '/api/' in url or '/calc/' in url:
                    selectors['extracted_patterns']['api_endpoints'] = \
                        selectors['extracted_patterns'].get('api_endpoints', [])
                    selectors['extracted_patterns']['api_endpoints'].append(url)

        return selectors

    def create_scenario_list(self):
        """Create a list of all scenarios to record."""
        scenarios = [
            'search',
            'navigation',
            'heart_score',
            'cha2ds2_vasc',
            'sofa',
            'perc_rule',
            'creatinine_clearance'
        ]

        scenarios_file = self.base_dir / "scenarios_to_record.json"
        with open(scenarios_file, 'w') as f:
            json.dump({
                "scenarios": scenarios,
                "priority": [
                    "heart_score",
                    "cha2ds2_vasc",
                    "sofa"
                ],
                "status": {scenario: "pending" for scenario in scenarios}
            }, f, indent=2)

        print(f"📝 Scenario list created: {scenarios_file}")
        return scenarios


def main():
    """Main entry point for the recording script."""
    parser = argparse.ArgumentParser(
        description="Record MDCalc interactions for selector extraction"
    )
    parser.add_argument(
        'scenario',
        nargs='?',
        default='navigation',
        choices=[
            'search', 'navigation', 'heart_score',
            'cha2ds2_vasc', 'sofa', 'perc_rule',
            'creatinine_clearance', 'custom'
        ],
        help='Scenario to record'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (not recommended for recording)'
    )
    parser.add_argument(
        '--auth',
        action='store_true',
        help='Use saved authentication state if available'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all scenarios to record'
    )

    args = parser.parse_args()

    # Initialize recorder
    recorder = MDCalcRecorder()

    if args.list:
        scenarios = recorder.create_scenario_list()
        print("\n📋 Scenarios to record:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"  {i}. {scenario}")
        return

    # Record the specified scenario
    recorder.record_interaction(args.scenario, args.headless, args.auth)


if __name__ == "__main__":
    main()