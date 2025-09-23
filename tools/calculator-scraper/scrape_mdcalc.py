#!/usr/bin/env python3
"""
Progressive MDCalc catalog scraper.
Extracts calculators WHILE scrolling to capture lazy-loaded content.
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
import logging
from typing import Set, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape_mdcalc_progressive():
    """Scrape MDCalc catalog by extracting data progressively while scrolling."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show browser for debugging
            args=['--disable-web-security', '--disable-features=IsolateOrigins,site-per-process']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        page = await context.new_page()

        logger.info("Navigating to MDCalc catalog...")

        # Try multiple approaches to load the page
        try:
            # First try with the fragment URL
            await page.goto("https://www.mdcalc.com/#All", wait_until='domcontentloaded', timeout=60000)
        except Exception as e:
            logger.warning(f"First attempt failed: {e}")
            logger.info("Trying alternative approach...")
            # Try loading main page first, then navigating to #All
            await page.goto("https://www.mdcalc.com/", wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            await page.goto("https://www.mdcalc.com/#All", wait_until='domcontentloaded', timeout=30000)

        # Wait for the page to stabilize and content to load
        logger.info("Waiting for content to load...")
        await page.wait_for_timeout(8000)  # Give more time for initial load

        # Wait for calculator links to appear
        try:
            await page.wait_for_selector('a[href*="/calc/"]', timeout=10000)
            logger.info("Calculator links found, proceeding with extraction...")
        except:
            logger.warning("No calculator links found initially, proceeding anyway...")

        # Initialize JavaScript to track calculators as we scroll
        await page.evaluate('''
            () => {
                window.mdcalcScraperData = {
                    calculators: {},
                    seenUrls: new Set()
                };

                // Function to extract calculators from current viewport
                window.extractVisibleCalculators = () => {
                    const links = document.querySelectorAll('a[href*="/calc/"]');
                    let newCount = 0;

                    links.forEach(link => {
                        const href = link.href;
                        if (!href || !href.includes('/calc/')) return;

                        // Skip if we've already seen this URL
                        if (window.mdcalcScraperData.seenUrls.has(href)) return;

                        // Extract ID from URL
                        const match = href.match(/calc\\/(\\d+)\\//);
                        if (!match) return;

                        const id = match[1];

                        // Mark as seen
                        window.mdcalcScraperData.seenUrls.add(href);

                        // Extract slug
                        const slugMatch = href.match(/calc\\/\\d+\\/([^/]+)/);
                        const slug = slugMatch ? slugMatch[1] : '';

                        // Get calculator name
                        let name = link.textContent?.trim() || '';
                        name = name.replace(/\\s+/g, ' ').trim();
                        name = name.replace(/\\([^)]+\\)$/, '').trim();

                        // Look for description
                        const parent = link.closest('.calc-item, article, li, div[class*="calc"], div[class*="row"]');
                        let description = '';
                        let category = 'General';

                        if (parent) {
                            // Try to find description
                            const descEl = parent.querySelector('.description, .excerpt, p:not(:has(a))');
                            if (descEl) {
                                description = descEl.textContent?.trim() || '';
                            }

                            // Try to find category from parent sections
                            let categoryEl = parent.closest('section, div[class*="category"], div[class*="specialty"]');
                            if (categoryEl) {
                                const heading = categoryEl.querySelector('h2, h3, h4');
                                if (heading) {
                                    category = heading.textContent?.trim() || 'General';
                                }
                            }
                        }

                        if (id && name) {
                            window.mdcalcScraperData.calculators[id] = {
                                id: id,
                                name: name,
                                slug: slug,
                                category: category,
                                url: href,
                                description: description
                            };
                            newCount++;
                        }
                    });

                    return {
                        totalFound: Object.keys(window.mdcalcScraperData.calculators).length,
                        newFound: newCount
                    };
                };
            }
        ''')

        logger.info("Starting progressive extraction while scrolling...")

        # Scroll and extract progressively
        scroll_distance = 500  # pixels to scroll each time
        total_extracted = 0
        last_count = 0
        no_new_count = 0

        while True:
            # Extract calculators from current viewport
            result = await page.evaluate('window.extractVisibleCalculators()')
            total_extracted = result['totalFound']
            new_found = result['newFound']

            if new_found > 0:
                logger.info(f"  Extracted {new_found} new calculators (total: {total_extracted})")
                no_new_count = 0
            else:
                no_new_count += 1

            # Scroll down
            await page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            await page.wait_for_timeout(500)  # Wait for content to load

            # Check if we've reached the bottom
            at_bottom = await page.evaluate('''
                () => {
                    return (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100;
                }
            ''')

            # If we're at the bottom and found no new calculators for several scrolls, we're done
            if at_bottom and no_new_count > 3:
                logger.info("Reached bottom of page")
                break

            # Safety check - stop if we haven't found new calculators in many scrolls
            if no_new_count > 10:
                logger.info("No new calculators found after multiple scrolls")
                break

        # Extract the final accumulated data
        all_calculators = await page.evaluate('''
            () => {
                return Object.values(window.mdcalcScraperData.calculators);
            }
        ''')

        logger.info(f"Total calculators extracted: {len(all_calculators)}")

        # Try to get more by visiting specialty pages if we didn't get enough
        if len(all_calculators) < 500:
            logger.info("Trying specialty pages to get more calculators...")

            specialty_paths = [
                "specialties/cardiology",
                "specialties/emergency-medicine",
                "specialties/critical-care",
                "specialties/nephrology",
                "specialties/pulmonology",
                "specialties/gastroenterology",
                "specialties/hematology-oncology",
                "specialties/infectious-disease",
                "specialties/neurology",
                "specialties/endocrinology"
            ]

            for specialty_path in specialty_paths:
                try:
                    specialty = specialty_path.split('/')[-1].replace('-', ' ').title()
                    logger.info(f"  Checking {specialty}...")

                    await page.goto(f"https://www.mdcalc.com/{specialty_path}", wait_until='networkidle')
                    await page.wait_for_timeout(2000)

                    # Extract from this specialty page
                    specialty_calcs = await page.evaluate(f'''
                        () => {{
                            const calcs = [];
                            const links = document.querySelectorAll('a[href*="/calc/"]');

                            links.forEach(link => {{
                                const href = link.href;
                                const match = href.match(/calc\\/(\\d+)\\//);
                                if (!match) return;

                                const id = match[1];
                                const slugMatch = href.match(/calc\\/\\d+\\/([^/]+)/);
                                const slug = slugMatch ? slugMatch[1] : '';

                                let name = link.textContent?.trim() || '';
                                name = name.replace(/\\s+/g, ' ').trim();

                                if (id && name) {{
                                    calcs.push({{
                                        id: id,
                                        name: name,
                                        slug: slug,
                                        category: "{specialty}",
                                        url: href
                                    }});
                                }}
                            }});

                            return calcs;
                        }}
                    ''')

                    # Add new calculators
                    for calc in specialty_calcs:
                        if not any(c['id'] == calc['id'] for c in all_calculators):
                            all_calculators.append(calc)

                    logger.info(f"    Added {len(specialty_calcs)} from {specialty}")

                except Exception as e:
                    logger.error(f"    Failed to scrape {specialty}: {e}")

        # Enhance categories
        all_calculators = enhance_with_categories(all_calculators)

        # Save to JSON
        output_path = Path(__file__).parent.parent.parent / "mcp-servers" / "mdcalc-automation-mcp" / "src" / "calculator-catalog" / "mdcalc_catalog.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                'version': '3.0',
                'total_count': len(all_calculators),
                'calculators': sorted(all_calculators, key=lambda x: x.get('name', ''))
            }, f, indent=2)

        logger.info(f"\n✅ Saved {len(all_calculators)} calculators to {output_path}")

        # Print summary
        categories = {}
        for calc in all_calculators:
            cat = calc.get('category', 'General')
            categories[cat] = categories.get(cat, 0) + 1

        print("\n📊 Category Summary:")
        for cat, count in sorted(categories.items()):
            print(f"   {cat}: {count} calculators")

        # Show a few examples
        print("\n📝 Sample calculators:")
        for calc in all_calculators[:5]:
            print(f"   - {calc['name']} (ID: {calc['id']}, Category: {calc['category']})")

        await browser.close()
        return all_calculators


def enhance_with_categories(calculators: List[Dict]) -> List[Dict]:
    """Enhance calculators with proper medical categories."""

    category_keywords = {
        'Cardiology': ['heart', 'cardiac', 'chads', 'chf', 'timi', 'grace', 'hf', 'mi', 'acs', 'afib', 'atrial', 'has-bled'],
        'Pulmonology': ['lung', 'pulmon', 'asthma', 'copd', 'pneumonia', 'pe ', 'pulmonary', 'perc', 'wells', 'curb'],
        'Emergency Medicine': ['emergency', 'trauma', 'ottawa', 'nexus', 'pecarn', 'canadian', 'news'],
        'Critical Care': ['icu', 'sofa', 'apache', 'saps', 'sepsis', 'qsofa', 'ventilat'],
        'Nephrology': ['renal', 'kidney', 'egfr', 'gfr', 'creatinine', 'mdrd', 'ckd', 'fena'],
        'Hepatology': ['liver', 'hepat', 'meld', 'child-pugh', 'cirrhosis', 'fibrosis'],
        'Neurology': ['stroke', 'nihss', 'neuro', 'glasgow', 'gcs', 'brain'],
        'Hematology': ['bleeding', 'anemia', 'platelet', 'has-bled', 'vte', 'dvt'],
        'Oncology': ['cancer', 'tumor', 'oncol', 'staging', 'ecog'],
        'Endocrinology': ['diabetes', 'diabetic', 'insulin', 'glucose', 'hba1c', 'thyroid'],
        'Gastroenterology': ['gi ', 'gastro', 'pancrea', 'rockall', 'bristol'],
        'Pediatrics': ['pediatric', 'child', 'infant', 'peld', 'apgar'],
        'Psychiatry': ['psych', 'depression', 'phq', 'gad', 'mmse', 'cage'],
        'Infectious Disease': ['infection', 'antibiotic', 'mascc', 'covid'],
        'Laboratory': ['lab', 'sodium', 'calcium', 'anion', 'osmol', 'ldl', 'corrected']
    }

    for calc in calculators:
        if calc.get('category') and calc['category'] != 'General':
            continue

        name_lower = calc.get('name', '').lower()
        slug_lower = calc.get('slug', '').lower()
        combined = f"{name_lower} {slug_lower}"

        for category, keywords in category_keywords.items():
            if any(keyword in combined for keyword in keywords):
                calc['category'] = category
                break

        if not calc.get('category'):
            calc['category'] = 'General'

    return calculators


if __name__ == "__main__":
    asyncio.run(scrape_mdcalc_progressive())