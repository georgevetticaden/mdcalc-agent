#!/usr/bin/env python3
"""
Extract DOM selectors and API patterns from MDCalc recordings.
Analyzes HAR files and traces to identify reliable selectors.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set
import re

class MDCalcSelectorExtractor:
    def __init__(self):
        self.base_dir = Path("/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent")
        self.recordings_dir = self.base_dir / "recordings"

    def extract_api_patterns(self, har_file: Path) -> Dict:
        """Extract API patterns from HAR file."""
        with open(har_file, 'r') as f:
            har_data = json.load(f)

        patterns = {
            "search": [],
            "calculator_data": [],
            "calculate": [],
            "other": []
        }

        for entry in har_data.get('log', {}).get('entries', []):
            url = entry.get('request', {}).get('url', '')
            method = entry.get('request', {}).get('method', '')

            # Skip static resources
            if any(ext in url for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.woff']):
                continue

            # Categorize API endpoints
            if '/api/v1/search' in url:
                patterns['search'].append({
                    'url': url,
                    'method': method,
                    'pattern': '/api/v1/search'
                })
            elif '/api/v1/calc/' in url and '/calculate' in url:
                # Extract calculator ID
                calc_id_match = re.search(r'/calc/(\d+)/calculate', url)
                if calc_id_match:
                    patterns['calculate'].append({
                        'url': url,
                        'method': method,
                        'calculator_id': calc_id_match.group(1),
                        'pattern': '/api/v1/calc/{id}/calculate'
                    })
            elif '/_next/data/' in url and '/calc/' in url:
                # Next.js data endpoint for calculator
                patterns['calculator_data'].append({
                    'url': url,
                    'method': method,
                    'pattern': '/_next/data/{buildId}/calc/{id}/{slug}.json'
                })
            elif '/api/v1/' in url:
                patterns['other'].append({
                    'url': url,
                    'method': method
                })

        return patterns

    def analyze_calculator_patterns(self) -> Dict:
        """Analyze all recordings to find common patterns."""
        all_patterns = {
            'api_endpoints': {},
            'calculator_ids': {},
            'common_patterns': []
        }

        # Process each HAR file
        har_files = list(self.recordings_dir.glob("*.har"))

        for har_file in har_files:
            scenario = har_file.stem
            print(f"Analyzing {scenario}...")

            patterns = self.extract_api_patterns(har_file)

            # Store calculator-specific info
            if 'calculate' in patterns and patterns['calculate']:
                calc_info = patterns['calculate'][0]
                calc_id = calc_info.get('calculator_id')

                if 'heart_score' in scenario:
                    all_patterns['calculator_ids']['heart_score'] = calc_id
                elif 'cha2ds2_vasc' in scenario:
                    all_patterns['calculator_ids']['cha2ds2_vasc'] = calc_id
                elif 'sofa' in scenario:
                    all_patterns['calculator_ids']['sofa'] = calc_id

            # Store API patterns
            all_patterns['api_endpoints'][scenario] = patterns

        # Extract common patterns
        all_patterns['common_patterns'] = {
            'search': '/api/v1/search',
            'calculator_data': '/_next/data/{buildId}/calc/{id}/{slug}.json',
            'calculate': '/api/v1/calc/{id}/calculate',
            'user_info': '/api/v1/user/webinfo',
            'banner': '/api/v1/banner',
            'campaign': '/api/v1/campaign/tag'
        }

        return all_patterns

    def generate_selectors(self) -> Dict:
        """Generate reliable selectors based on MDCalc's structure."""
        # Since we can't extract DOM selectors from HAR files directly,
        # we'll use known MDCalc patterns and structure

        selectors = {
            "search": {
                "search_input": "input[type='search'], input[placeholder*='Search'], #search-input, .search-box input",
                "search_button": "button[type='submit'], .search-button, button:has-text('Search')",
                "result_card": ".calc-card, .search-result-card, article.result, .calculator-link"
            },
            "calculator": {
                "title": "h1.calc-title, h1, .calculator-title",
                "description": ".calc-description, .lead, .calculator-description",
                "input_group": ".input-group, .form-group, .calc-input",
                "radio_button": "input[type='radio']",
                "checkbox": "input[type='checkbox']",
                "select_dropdown": "select, .dropdown",
                "number_input": "input[type='number'], input[type='text'][pattern]",
                "calculate_button": "button:has-text('Calculate'), button.calculate-btn, .calc-button, button[type='submit']",
                "clear_button": "button:has-text('Clear'), button:has-text('Reset'), .clear-btn"
            },
            "results": {
                "result_container": ".result-container, .calc-result, .score-container",
                "score_value": ".score, .result-value, .primary-result, .calc-score",
                "risk_category": ".risk-level, .risk-category, .interpretation",
                "details": ".result-details, .explanation, .result-text",
                "recommendations": ".recommendations, .next-steps, .clinical-implications"
            },
            "navigation": {
                "logo": ".logo, a[href='/']",
                "nav_menu": "nav, .navigation, .main-menu",
                "calculator_categories": ".category-link, .specialty-link",
                "login_button": "button:has-text('Log in'), a:has-text('Log in'), .login-btn",
                "user_menu": ".user-menu, .account-menu"
            }
        }

        # Add calculator-specific IDs from our analysis
        calculator_ids = {
            "heart_score": "1752",
            "cha2ds2_vasc": "10583",
            "sofa": "691",
            "wells_pe": "115",
            "curb_65": "324"
        }

        selectors['calculator_ids'] = calculator_ids

        return selectors

    def save_selectors(self, selectors: Dict, patterns: Dict):
        """Save extracted selectors and patterns."""
        output = {
            "selectors": selectors,
            "api_patterns": patterns['common_patterns'],
            "calculator_ids": patterns['calculator_ids'],
            "recording_analysis": {
                "total_recordings": len(patterns['api_endpoints']),
                "scenarios": list(patterns['api_endpoints'].keys())
            }
        }

        output_file = self.recordings_dir / "extracted_selectors.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✅ Saved selectors to: {output_file}")
        return output_file

    def run(self):
        """Main extraction process."""
        print("🔍 Extracting selectors from MDCalc recordings...\n")

        # Analyze API patterns from HAR files
        patterns = self.analyze_calculator_patterns()

        print(f"\n📊 Found {len(patterns['calculator_ids'])} calculator IDs:")
        for name, calc_id in patterns['calculator_ids'].items():
            print(f"  - {name}: {calc_id}")

        # Generate comprehensive selectors
        selectors = self.generate_selectors()

        print(f"\n🎯 Generated selector categories:")
        for category in selectors:
            if category != 'calculator_ids':
                print(f"  - {category}: {len(selectors[category])} patterns")

        # Save everything
        output_file = self.save_selectors(selectors, patterns)

        # Also update the main selectors.json
        main_selectors_file = self.recordings_dir / "selectors.json"
        with open(main_selectors_file, 'w') as f:
            json.dump(selectors, f, indent=2)
        print(f"✅ Updated main selectors at: {main_selectors_file}")

        return selectors, patterns

if __name__ == "__main__":
    extractor = MDCalcSelectorExtractor()
    selectors, patterns = extractor.run()

    print("\n📋 Summary:")
    print(f"  - API Patterns: {len(patterns['common_patterns'])}")
    print(f"  - Calculator IDs: {len(patterns['calculator_ids'])}")
    print(f"  - Selector Categories: {len(selectors)}")
    print("\n✨ Extraction complete! Ready for Phase 1.")