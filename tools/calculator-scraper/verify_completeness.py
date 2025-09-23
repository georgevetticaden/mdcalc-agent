#!/usr/bin/env python3
"""
Verify that ALL calculators from MDCalc page were extracted.
Compares scraped catalog against live page.
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_completeness():
    """Compare scraped catalog against actual MDCalc page."""

    # Load the scraped catalog
    catalog_path = Path(__file__).parent.parent.parent / "mcp-servers" / "mdcalc-automation-mcp" / "src" / "calculator-catalog" / "mdcalc_catalog.json"

    if not catalog_path.exists():
        print(f"❌ Catalog not found at: {catalog_path}")
        print("Run: python tools/calculator-scraper/scrape_mdcalc.py first")
        return

    with open(catalog_path, 'r') as f:
        catalog_data = json.load(f)

    scraped_calculators = catalog_data.get('calculators', [])
    scraped_ids = set(calc['id'] for calc in scraped_calculators)

    print("🔍 Verifying Extraction Completeness")
    print("=" * 60)
    print(f"📂 Scraped catalog has: {len(scraped_calculators)} calculators")
    print("\nNow checking the live MDCalc page...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        await page.goto("https://www.mdcalc.com/#All", wait_until='networkidle')
        await page.wait_for_timeout(5000)

        # Count ALL calculators visible on initial load
        initial_count = await page.evaluate('''
            () => {
                const links = document.querySelectorAll('a[href*="/calc/"]');
                const unique = new Set();
                links.forEach(link => {
                    const match = link.href.match(/calc\\/(\\d+)\\//);
                    if (match) unique.add(match[1]);
                });
                return unique.size;
            }
        ''')

        print(f"\n📊 Initial page load shows: {initial_count} calculators")

        # Now scroll to the very bottom to load everything
        print("\nScrolling to load all content...")

        total_height = await page.evaluate('document.body.scrollHeight')
        current_position = 0
        step = 500

        while current_position < total_height:
            await page.evaluate(f'window.scrollTo(0, {current_position})')
            current_position += step
            await page.wait_for_timeout(200)

            # Update total height in case more content loaded
            new_height = await page.evaluate('document.body.scrollHeight')
            if new_height > total_height:
                total_height = new_height

        # Count all unique calculator IDs after full scroll
        all_page_ids = await page.evaluate('''
            () => {
                const links = document.querySelectorAll('a[href*="/calc/"]');
                const uniqueIds = new Set();
                const calculators = [];

                links.forEach(link => {
                    const match = link.href.match(/calc\\/(\\d+)\\//);
                    if (match && !uniqueIds.has(match[1])) {
                        uniqueIds.add(match[1]);
                        calculators.push({
                            id: match[1],
                            name: link.textContent.trim(),
                            url: link.href
                        });
                    }
                });

                return {
                    ids: Array.from(uniqueIds),
                    count: uniqueIds.size,
                    calculators: calculators
                };
            }
        ''')

        page_ids = set(all_page_ids['ids'])
        page_count = all_page_ids['count']

        print(f"\n✅ After full scroll, page has: {page_count} unique calculators")

        # Compare scraped vs actual
        print("\n📋 Comparison Results:")
        print(f"  - Scraped catalog: {len(scraped_ids)} calculators")
        print(f"  - Live page total: {page_count} calculators")

        # Find missing calculators
        missing_from_catalog = page_ids - scraped_ids
        extra_in_catalog = scraped_ids - page_ids

        if missing_from_catalog:
            print(f"\n⚠️  Missing from catalog: {len(missing_from_catalog)} calculators")
            # Show first 10 missing
            for calc_id in list(missing_from_catalog)[:10]:
                calc = next((c for c in all_page_ids['calculators'] if c['id'] == calc_id), None)
                if calc:
                    print(f"   - ID {calc_id}: {calc['name']}")
            if len(missing_from_catalog) > 10:
                print(f"   ... and {len(missing_from_catalog) - 10} more")
        else:
            print("\n✅ No calculators missing from catalog!")

        if extra_in_catalog:
            print(f"\n⚠️  Extra in catalog (not on page): {len(extra_in_catalog)} calculators")
            for calc_id in list(extra_in_catalog)[:5]:
                calc = next((c for c in scraped_calculators if c['id'] == calc_id), None)
                if calc:
                    print(f"   - ID {calc_id}: {calc['name']}")
        else:
            print("✅ No extra calculators in catalog")

        # Calculate completeness percentage
        if page_count > 0:
            completeness = (len(scraped_ids) / page_count) * 100
            overlap = len(scraped_ids & page_ids)

            print(f"\n📊 Extraction Completeness:")
            print(f"  - Coverage: {completeness:.1f}%")
            print(f"  - Matching IDs: {overlap}/{page_count}")

            if completeness >= 99:
                print("  ✅ EXCELLENT: Nearly perfect extraction!")
            elif completeness >= 95:
                print("  ✅ VERY GOOD: 95%+ extraction")
            elif completeness >= 90:
                print("  ⚠️  GOOD: 90%+ extraction")
            else:
                print("  ❌ INCOMPLETE: Less than 90% extracted")

        # Also check the displayed count on the page if available
        displayed_count = await page.evaluate('''
            () => {
                // Look for text that says "X calculators" or similar
                const texts = Array.from(document.querySelectorAll('*')).map(el => el.textContent);
                const matches = texts.filter(t => t && t.match(/\\d+\\s*(calculators?|tools?|calc)/i));
                return matches;
            }
        ''')

        if displayed_count:
            for text in displayed_count[:3]:
                if text and len(text) < 100:  # Only show short texts
                    print(f"\n📝 Page text: '{text.strip()}'")

        await browser.close()

        return {
            'scraped': len(scraped_ids),
            'on_page': page_count,
            'missing': len(missing_from_catalog),
            'completeness': completeness if page_count > 0 else 0
        }


if __name__ == "__main__":
    result = asyncio.run(verify_completeness())

    print("\n" + "=" * 60)
    if result and result['completeness'] >= 99:
        print("✅ Extraction is COMPLETE! You have all calculators.")
    elif result and result['completeness'] >= 95:
        print("✅ Extraction is nearly complete (95%+)")
    else:
        print("⚠️  Some calculators may be missing. Consider re-running scraper.")