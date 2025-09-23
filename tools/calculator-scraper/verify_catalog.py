#!/usr/bin/env python3
"""
Verify the scraped MDCalc catalog for completeness and quality.
"""

import json
from pathlib import Path
from collections import Counter

def verify_catalog():
    """Verify the MDCalc catalog extraction."""

    catalog_path = Path(__file__).parent.parent.parent / "mcp-servers" / "mdcalc-automation-mcp" / "src" / "calculator-catalog" / "mdcalc_catalog.json"

    if not catalog_path.exists():
        print(f"❌ Catalog not found at: {catalog_path}")
        return

    with open(catalog_path, 'r') as f:
        data = json.load(f)

    calculators = data.get('calculators', [])

    print("📊 MDCalc Catalog Verification Report")
    print("=" * 60)

    # Basic stats
    print(f"\n✅ Total Calculators: {len(calculators)}")

    # Check for duplicates
    ids = [c['id'] for c in calculators]
    id_counts = Counter(ids)
    duplicates = [id for id, count in id_counts.items() if count > 1]

    if duplicates:
        print(f"⚠️  Found {len(duplicates)} duplicate IDs: {duplicates[:5]}")
    else:
        print("✅ No duplicate IDs found")

    # Check for missing data
    missing_names = [c for c in calculators if not c.get('name')]
    missing_urls = [c for c in calculators if not c.get('url')]

    print(f"\n📝 Data Completeness:")
    print(f"  - Calculators with names: {len(calculators) - len(missing_names)}/{len(calculators)}")
    print(f"  - Calculators with URLs: {len(calculators) - len(missing_urls)}/{len(calculators)}")

    # Category distribution
    categories = Counter(c.get('category', 'Unknown') for c in calculators)

    print(f"\n📂 Categories ({len(categories)}):")
    for category, count in categories.most_common():
        percentage = (count / len(calculators)) * 100
        print(f"  - {category}: {count} ({percentage:.1f}%)")

    # Check for known important calculators
    important_calcs = {
        '1752': 'HEART Score',
        '801': 'CHA2DS2-VASc',
        '691': 'SOFA Score',
        '324': 'CURB-65',
        '115': 'Wells Criteria PE',
        '78': 'MELD Score',
        '404': 'NIH Stroke Scale',
        '64': 'Glasgow Coma Scale',
        '111': 'TIMI Risk Score',
        '1785': 'HAS-BLED'
    }

    print(f"\n🔍 Verification of Key Calculators:")
    found_important = 0
    for calc_id, expected_name in important_calcs.items():
        found = any(c['id'] == calc_id for c in calculators)
        if found:
            calc = next(c for c in calculators if c['id'] == calc_id)
            status = "✅" if expected_name.lower() in calc['name'].lower() else "⚠️"
            print(f"  {status} {expected_name} (ID: {calc_id}): {calc['name']}")
            found_important += 1
        else:
            print(f"  ❌ {expected_name} (ID: {calc_id}): NOT FOUND")

    print(f"\n  Found {found_important}/{len(important_calcs)} important calculators")

    # Sample output
    print(f"\n📝 Sample Calculators:")
    for calc in calculators[:10]:
        print(f"  - [{calc['id']}] {calc['name']} ({calc.get('category', 'Unknown')})")

    # Overall assessment
    print(f"\n🎯 Overall Assessment:")
    if len(calculators) >= 800:
        print("  ✅ Excellent extraction - 800+ calculators found!")
    elif len(calculators) >= 500:
        print("  ⚠️  Good extraction - 500+ calculators (MDCalc has 900+)")
    else:
        print("  ❌ Incomplete extraction - less than 500 calculators")

    if found_important >= 8:
        print("  ✅ All major calculators present")
    else:
        print("  ⚠️  Some major calculators missing")

    return {
        'total': len(calculators),
        'categories': len(categories),
        'duplicates': len(duplicates),
        'complete': len(calculators) >= 800
    }

if __name__ == "__main__":
    verify_catalog()