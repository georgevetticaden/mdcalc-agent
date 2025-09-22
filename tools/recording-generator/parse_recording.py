#!/usr/bin/env python3
"""
Parse recordings to extract reliable selectors for MDCalc automation.
Analyzes HAR files, traces, and creates a unified selector strategy.
"""

import json
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Set
import argparse
import sys

# Ensure we can run this script directly
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class RecordingParser:
    """Parse Playwright recordings to extract selectors."""

    def __init__(self, recordings_dir=None):
        """Initialize parser with recordings directory."""
        if recordings_dir is None:
            recordings_dir = Path(__file__).parent.parent.parent / "recordings"
        self.recordings_dir = Path(recordings_dir)

        # Common MDCalc selector patterns based on typical medical calculator sites
        self.selector_patterns = {
            'search': [
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'input[name*="search" i]',
                '#search',
                '.search-input',
                '[data-testid*="search"]',
                'input.form-control[type="text"]'  # Common Bootstrap pattern
            ],
            'calculator_card': [
                '.calc-card',
                '.calculator-card',
                '.search-result',
                'article.calculator',
                '[data-calc-id]',
                '.list-group-item',
                'a[href*="/calc/"]'
            ],
            'input_field': [
                'input[type="number"]',
                'input[type="text"]',
                'select',
                'input[type="radio"]',
                'input[type="checkbox"]',
                '.form-control',
                '.calc-input',
                '[data-input-name]'
            ],
            'calculate_button': [
                'button:has-text("Calculate")',
                'button:has-text("Calc")',
                'input[type="submit"]',
                'button[type="submit"]',
                '.calculate-btn',
                '.btn-calculate',
                '#calculate',
                'button.btn-primary'
            ],
            'result_container': [
                '.result',
                '.score',
                '.output',
                '.result-container',
                '.calc-result',
                '.primary-result',
                '[data-result]',
                '.alert'  # Often used for results
            ]
        }

    def parse_all_recordings(self) -> Dict:
        """Parse all recordings and create unified selector map."""
        print("🔍 Parsing all recordings in directory...")

        selector_map = {
            "version": "1.0",
            "base_url": "https://www.mdcalc.com",
            "selectors": {},
            "calculators": {}
        }

        # Parse HAR files
        har_files = list(self.recordings_dir.glob("*.har"))
        print(f"Found {len(har_files)} HAR files")

        for har_file in har_files:
            scenario = self._extract_scenario_name(har_file.name)
            print(f"  Parsing: {scenario}")
            har_selectors = self._parse_har_file(har_file)
            selector_map['selectors'][scenario] = har_selectors

        # Parse trace files
        trace_files = list(self.recordings_dir.glob("*_trace.zip"))
        print(f"Found {len(trace_files)} trace files")

        for trace_file in trace_files:
            scenario = self._extract_scenario_name(trace_file.name)
            trace_selectors = self._parse_trace_file(trace_file)

            # Merge with existing selectors
            if scenario in selector_map['selectors']:
                selector_map['selectors'][scenario].update(trace_selectors)
            else:
                selector_map['selectors'][scenario] = trace_selectors

        # Add default selector patterns
        selector_map['default_patterns'] = self.selector_patterns

        # Save unified selector map
        output_file = self.recordings_dir / "selectors.json"
        with open(output_file, 'w') as f:
            json.dump(selector_map, f, indent=2)

        print(f"\n✅ Selector map saved to: {output_file}")
        return selector_map

    def _extract_scenario_name(self, filename: str) -> str:
        """Extract scenario name from filename."""
        # Remove timestamp and extension
        name = filename.split('_')[0]
        return name.replace('.har', '').replace('.zip', '')

    def _parse_har_file(self, har_path: Path) -> Dict:
        """Parse HAR file to extract network patterns and selectors."""
        selectors = {
            "api_endpoints": set(),
            "form_actions": set(),
            "query_params": set()
        }

        try:
            with open(har_path, 'r') as f:
                har_data = json.load(f)

            for entry in har_data.get('log', {}).get('entries', []):
                request = entry.get('request', {})
                url = request.get('url', '')
                method = request.get('method', '')

                # Track API endpoints
                if 'mdcalc.com' in url:
                    if '/api/' in url or '/calc/' in url:
                        # Extract calculator ID from URL
                        calc_id_match = re.search(r'/calc/(\d+|[\w-]+)', url)
                        if calc_id_match:
                            selectors['api_endpoints'].add(calc_id_match.group(1))

                    # Track form submissions
                    if method == 'POST':
                        selectors['form_actions'].add(url)

                    # Track query parameters
                    if '?' in url:
                        params = url.split('?')[1]
                        selectors['query_params'].add(params)

            # Convert sets to lists for JSON serialization
            return {k: list(v) for k, v in selectors.items()}

        except Exception as e:
            print(f"  ⚠️ Error parsing HAR file: {e}")
            return {}

    def _parse_trace_file(self, trace_path: Path) -> Dict:
        """Parse Playwright trace file to extract DOM selectors."""
        selectors = {
            "dom_selectors": [],
            "actions": []
        }

        try:
            with zipfile.ZipFile(trace_path, 'r') as trace_zip:
                # Look for trace events
                if 'trace.json' in trace_zip.namelist():
                    with trace_zip.open('trace.json') as f:
                        trace_data = json.load(f)

                    # Extract selector information from events
                    for event in trace_data.get('events', []):
                        if event.get('type') == 'action':
                            metadata = event.get('metadata', {})

                            # Extract selector from action
                            if 'selector' in metadata:
                                selectors['dom_selectors'].append(metadata['selector'])

                            # Track action types
                            action_type = metadata.get('type', '')
                            if action_type:
                                selectors['actions'].append({
                                    'type': action_type,
                                    'selector': metadata.get('selector', '')
                                })

            return selectors

        except Exception as e:
            print(f"  ⚠️ Error parsing trace file: {e}")
            return {}

    def generate_calculator_config(self, calculator_name: str) -> Dict:
        """Generate configuration for a specific calculator."""
        config = {
            "name": calculator_name,
            "selectors": {},
            "inputs": [],
            "validation": {}
        }

        # Map calculator names to IDs (will be populated from actual recordings)
        calculator_ids = {
            'heart_score': '1752',
            'cha2ds2_vasc': '1785',
            'sofa': '691',
            'perc_rule': '347',
            'creatinine_clearance': '43'
        }

        if calculator_name in calculator_ids:
            config['id'] = calculator_ids[calculator_name]
            config['url'] = f"https://www.mdcalc.com/calc/{config['id']}"

        # Add calculator-specific selector patterns
        if calculator_name == 'heart_score':
            config['inputs'] = [
                {"name": "history", "type": "select", "required": True},
                {"name": "ecg", "type": "select", "required": True},
                {"name": "age", "type": "number", "required": True},
                {"name": "risk_factors", "type": "number", "required": True},
                {"name": "troponin", "type": "select", "required": True}
            ]
        elif calculator_name == 'cha2ds2_vasc':
            config['inputs'] = [
                {"name": "chf", "type": "checkbox"},
                {"name": "hypertension", "type": "checkbox"},
                {"name": "age_75", "type": "checkbox"},
                {"name": "diabetes", "type": "checkbox"},
                {"name": "stroke", "type": "checkbox"},
                {"name": "vascular", "type": "checkbox"},
                {"name": "age_65_74", "type": "checkbox"},
                {"name": "sex_female", "type": "checkbox"}
            ]

        return config

    def validate_selectors(self) -> Dict:
        """Validate that we have selectors for critical operations."""
        validation_results = {
            "complete": [],
            "missing": [],
            "warnings": []
        }

        required_scenarios = ['search', 'heart_score', 'cha2ds2_vasc', 'sofa']

        selectors_file = self.recordings_dir / "selectors.json"
        if not selectors_file.exists():
            validation_results['missing'].append("No selectors.json file found")
            return validation_results

        with open(selectors_file, 'r') as f:
            selector_map = json.load(f)

        for scenario in required_scenarios:
            if scenario in selector_map.get('selectors', {}):
                validation_results['complete'].append(scenario)
            else:
                validation_results['missing'].append(scenario)

        # Check for critical selector patterns
        if 'default_patterns' not in selector_map:
            validation_results['warnings'].append("No default selector patterns defined")

        return validation_results


def main():
    """Main entry point for parsing recordings."""
    parser = argparse.ArgumentParser(
        description="Parse MDCalc recordings to extract selectors"
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate selector completeness'
    )
    parser.add_argument(
        '--calculator',
        help='Generate config for specific calculator'
    )

    args = parser.parse_args()

    # Initialize parser
    recording_parser = RecordingParser()

    if args.calculator:
        # Generate config for specific calculator
        config = recording_parser.generate_calculator_config(args.calculator)
        print(json.dumps(config, indent=2))
    elif args.validate:
        # Validate selectors
        results = recording_parser.validate_selectors()
        print("\n📋 Selector Validation Results:")
        print(f"✅ Complete: {', '.join(results['complete']) or 'None'}")
        print(f"❌ Missing: {', '.join(results['missing']) or 'None'}")
        print(f"⚠️  Warnings: {', '.join(results['warnings']) or 'None'}")
    else:
        # Parse all recordings
        recording_parser.parse_all_recordings()


if __name__ == "__main__":
    main()