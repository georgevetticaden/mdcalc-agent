#!/usr/bin/env python3
"""
MDCalc Automation Client - Browser automation with screenshot support

This client provides low-level browser automation for MDCalc calculators using Playwright.
The key innovation is using screenshots for Claude's visual understanding rather than
maintaining complex selectors for 825 different calculators.

Core Capabilities:
    - Navigate to any MDCalc calculator by ID or slug
    - Capture optimized screenshots (23KB JPEG) of calculator interfaces
    - Search within catalog of 825 calculators
    - Execute calculators by clicking buttons and filling inputs
    - Extract results after calculation

Design Philosophy:
    - Screenshots over selectors: Claude SEES the calculator
    - Universal support: One approach works for all calculators
    - Mechanical execution: No clinical logic, just browser automation
    - Catalog-driven: Complete offline catalog for fast searching

This client is intentionally "dumb" - all intelligence lives in Claude.
"""

import asyncio
from playwright.async_api import async_playwright
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MDCalcClient:
    """
    MDCalc automation client using Playwright for browser control.

    This client implements a screenshot-based approach for universal calculator support.
    Instead of maintaining 825 different selector configurations, we:
    1. Navigate to calculators
    2. Take screenshots for Claude's visual understanding
    3. Execute calculators based on Claude's intelligent mapping

    Key Design Principles:
    - NO hardcoded selectors for specific calculators
    - Screenshots enable Claude to SEE and understand any calculator
    - Client is purely mechanical - Claude handles all intelligence
    - Supports all 825 MDCalc calculators automatically

    Methods:
        get_all_calculators(): Load catalog of 825 calculators
        search_calculators(): Search by condition/name
        get_calculator_details(): Get screenshot for visual understanding
        execute_calculator(): Execute with mapped values
    """

    def __init__(self):
        self.base_url = "https://www.mdcalc.com"
        self.playwright = None
        self.browser = None
        self.context = None

    def load_auth_state(self):
        """Load authentication state if available."""
        auth_path = Path(__file__).parent.parent.parent.parent / "recordings" / "auth" / "mdcalc_auth_state.json"

        if auth_path.exists():
            logger.info(f"Loading auth state from: {auth_path}")
            return str(auth_path)

        logger.info("No auth state found, proceeding without authentication")
        return None

    async def initialize(self, headless=True, use_auth=True):
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )

        context_params = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36'
        }

        if use_auth:
            auth_state_path = self.load_auth_state()
            if auth_state_path:
                context_params['storage_state'] = auth_state_path

        self.context = await self.browser.new_context(**context_params)
        logger.info("Browser initialized successfully")

    async def get_all_calculators(self) -> List[Dict]:
        """
        Load the complete MDCalc calculator catalog from JSON file.

        Returns:
            List[Dict]: List of 825 calculators, each containing:
                - id (str): Calculator ID (e.g., "1752")
                - name (str): Calculator name (e.g., "HEART Score")
                - category (str): Medical specialty (e.g., "Cardiology")
                - slug (str): URL slug (e.g., "heart-score")
                - url (str): Full MDCalc URL

        Raises:
            FileNotFoundError: If catalog file doesn't exist
            RuntimeError: If catalog file can't be parsed
        """
        # Load from scraped catalog file
        catalog_path = Path(__file__).parent / "calculator-catalog" / "mdcalc_catalog.json"

        if not catalog_path.exists():
            raise FileNotFoundError(
                f"Calculator catalog not found at {catalog_path}. "
                f"Please run: python tools/calculator-scraper/scrape_mdcalc.py"
            )

        try:
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
                logger.info(f"Loaded {catalog['total_count']} calculators from catalog")
                return catalog['calculators']
        except Exception as e:
            raise RuntimeError(f"Failed to load calculator catalog: {e}")

    async def search_calculators(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for calculators by condition, symptom, or name.

        Searches first in the local catalog (825 calculators) for speed,
        then falls back to web search if needed.

        Args:
            query (str): Search term (e.g., "chest pain", "HEART", "pneumonia")
            limit (int): Maximum results to return (default: 10)

        Returns:
            List[Dict]: Matching calculators, each containing:
                - id (str): Calculator ID
                - title (str): Calculator name
                - category (str): Medical specialty
                - slug (str): URL slug
                - url (str): Full MDCalc URL
                - description (str): Brief description (if available)
        """
        # First try searching in our catalog (faster and more reliable)
        try:
            all_calculators = await self.get_all_calculators()
            query_lower = query.lower()

            # Search in name, category, and slug
            matching_calcs = []
            for calc in all_calculators:
                name = calc.get('name', '').lower()
                category = calc.get('category', '').lower()
                slug = calc.get('slug', '').lower()

                # Check if query matches any field
                if (query_lower in name or
                    query_lower in category or
                    query_lower in slug):
                    matching_calcs.append({
                        'id': calc.get('id'),
                        'title': calc.get('name'),
                        'category': calc.get('category'),
                        'slug': calc.get('slug'),
                        'url': calc.get('url', f"{self.base_url}/calc/{calc.get('id')}/{calc.get('slug')}")
                    })

                    if len(matching_calcs) >= limit:
                        break

            if matching_calcs:
                logger.info(f"Found {len(matching_calcs)} calculators for '{query}' from catalog")
                return matching_calcs[:limit]

        except Exception as e:
            logger.warning(f"Catalog search failed: {e}, falling back to web search")

        # Fallback to web search if catalog search fails or returns no results
        page = await self.context.new_page()

        try:
            # First go to MDCalc homepage
            logger.info(f"Navigating to MDCalc...")
            await page.goto(self.base_url, wait_until='networkidle')
            await page.wait_for_timeout(2000)

            # Find and use the search box
            search_input = await page.wait_for_selector('input[type="search"], input[placeholder*="Search"]', timeout=5000)

            logger.info(f"Searching for: {query}")
            await search_input.fill(query)
            await search_input.press('Enter')

            # Wait for navigation and results to load
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)

            # Look for actual search result containers
            # Based on debug output, results are in calculatorRow_row-container__HM_dC elements
            calculators = await page.evaluate(f'''
                () => {{
                    const limit = {limit};

                    // Look for search result rows - these have the specific class
                    const resultRows = document.querySelectorAll('.calculatorRow_row-container__HM_dC');

                    if (resultRows.length === 0) {{
                        // Fallback to links within main content if no specific rows found
                        const mainLinks = document.querySelectorAll('main a[href*="/calc/"]');
                        // Filter out navigation and non-result links
                        const filteredLinks = Array.from(mainLinks).filter(link => {{
                            const text = link.textContent.trim();
                            // Must have substantial text to be a real result
                            return text.length > 20 && !text.includes('Popular') && !text.includes('Recent');
                        }});

                        return filteredLinks.slice(0, limit).map(link => {{
                            const href = link.href;
                            const idMatch = href.match(/calc\\/(\\d+)/);
                            const slugMatch = href.match(/calc\\/\\d+\\/([^/]+)/);

                            return {{
                                title: link.textContent.trim(),
                                url: href,
                                id: idMatch ? idMatch[1] : null,
                                slug: slugMatch ? slugMatch[1] : null
                            }};
                        }});
                    }}

                    // Process the result rows
                    return Array.from(resultRows).slice(0, limit).map(row => {{
                        const link = row.querySelector('a[href*="/calc/"]');
                        if (!link) return null;

                        const href = link.href;
                        const idMatch = href.match(/calc\\/(\\d+)/);
                        const slugMatch = href.match(/calc\\/\\d+\\/([^/]+)/);

                        // Get title from the specific title div
                        const titleElement = row.querySelector('.calculatorRow_row-title__8tXMs') || link;
                        const descElement = row.querySelector('.calculatorRow_row-bottom__eA_gR');

                        return {{
                            title: titleElement.textContent.trim(),
                            description: descElement ? descElement.textContent.trim() : '',
                            url: href,
                            id: idMatch ? idMatch[1] : null,
                            slug: slugMatch ? slugMatch[1] : null
                        }};
                    }}).filter(item => item && item.url);
                }}
            ''')

            logger.info(f"Found {len(calculators)} calculators for '{query}'")
            return calculators

        finally:
            await page.close()

    async def get_calculator_details(self, calculator_id: str) -> Dict:
        """
        Get calculator details including a screenshot for visual understanding.

        This is the KEY method for Claude's visual understanding approach.
        Instead of parsing DOM elements, we take a screenshot that Claude
        can SEE and understand using vision capabilities.

        Args:
            calculator_id (str): Calculator ID (e.g., "1752") or slug (e.g., "heart-score")

        Returns:
            Dict containing:
                - title (str): Calculator name
                - url (str): Calculator URL
                - screenshot_base64 (str): JPEG screenshot encoded as base64 (~23KB)
                - fields (List): Detected fields (may be empty for React apps)
                - fields_detected (int): Number of fields found

        Note:
            The screenshot is the primary output. Field detection may return 0
            for React-based calculators, which is expected. Claude uses vision
            to understand the calculator structure from the screenshot.
        """
        page = await self.context.new_page()

        try:
            # Handle both numeric IDs and slugs
            if calculator_id.isdigit():
                url = f"{self.base_url}/calc/{calculator_id}"
            else:
                # Assume it's a slug and try to use it directly
                url = f"{self.base_url}/calc/{calculator_id}"

            logger.info(f"Getting details for calculator: {calculator_id}")
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)  # Wait longer for React to render

            # Extract calculator structure
            details = await page.evaluate('''
                () => {
                    const title = document.querySelector('h1')?.textContent?.trim();

                    // Find ALL field groups - both button-based and input-based
                    const fieldGroups = [];

                    // 1. Find button-based fields (divs with calc_option elements)
                    const allContainers = document.querySelectorAll('div');
                    allContainers.forEach(container => {
                        const options = container.querySelectorAll('div[class*="calc_option"]');

                        if (options.length > 1) {  // Must have at least 2 options to be a field
                            // Look for a label - usually a div with text right before the options
                            let label = null;
                            const firstOption = options[0];
                            let sibling = firstOption.parentElement?.previousElementSibling;

                            // Check previous siblings for a label
                            while (sibling && !label) {
                                if (sibling.textContent && sibling.children.length === 0) {
                                    const text = sibling.textContent.trim();
                                    if (text && text.length < 100) {  // Reasonable label length
                                        label = text;
                                        break;
                                    }
                                }
                                sibling = sibling.previousElementSibling;
                            }

                            // Also check if there's a label as a direct child of the parent
                            if (!label) {
                                const parentChildren = Array.from(container.children);
                                for (let child of parentChildren) {
                                    if (child.textContent && !child.classList.contains('calc_option')
                                        && child.children.length === 0) {
                                        const text = child.textContent.trim();
                                        if (text && text.length < 100) {
                                            label = text;
                                            break;
                                        }
                                    }
                                }
                            }

                            if (label && !fieldGroups.some(fg => fg.label === label)) {
                                fieldGroups.push({
                                    label: label,
                                    name: label.toLowerCase().replace(/[^a-z0-9]/g, '_'),
                                    options: Array.from(options).map(opt => ({
                                        text: opt.textContent.trim(),
                                        value: opt.textContent.trim().toLowerCase().replace(/[^a-z0-9]/g, '_'),
                                        selected: opt.className.includes('selected')
                                    }))
                                });
                            }
                        }
                    });

                    // 2. Find numeric/text input fields
                    const inputFields = document.querySelectorAll('input[type="number"], input[type="text"]:not([type="search"])');
                    inputFields.forEach(input => {
                        // Get the label for this input
                        let label = null;

                        // Try to find associated label
                        if (input.id) {
                            const labelElement = document.querySelector(`label[for="${input.id}"]`);
                            if (labelElement) {
                                label = labelElement.textContent.trim();
                            }
                        }

                        // If no label found, look for nearby text
                        if (!label) {
                            const parent = input.closest('div');
                            if (parent) {
                                // Look for text before the input
                                const walker = document.createTreeWalker(
                                    parent,
                                    NodeFilter.SHOW_TEXT,
                                    null,
                                    false
                                );
                                let node;
                                while (node = walker.nextNode()) {
                                    const text = node.textContent.trim();
                                    if (text && text.length > 1 && text.length < 50) {
                                        label = text;
                                        break;
                                    }
                                }
                            }
                        }

                        if (label) {
                            const fieldName = input.name || input.id || label.toLowerCase().replace(/[^a-z0-9]/g, '_');

                            // Check if we already have this field
                            if (!fieldGroups.some(fg => fg.name === fieldName)) {
                                fieldGroups.push({
                                    label: label,
                                    name: fieldName,
                                    type: input.type,
                                    value: input.value,
                                    placeholder: input.placeholder,
                                    options: []  // No options for input fields
                                });
                            }
                        }
                    });

                    return {
                        title,
                        fields: fieldGroups,
                        url: window.location.href
                    };
                }
            ''')

            # Take a screenshot of the calculator form
            screenshot_bytes = None
            try:
                # Try to find just the calculator form area (not the whole page)
                # Look for the actual form container
                calc_selectors = [
                    'div[class*="calc_container"]',  # MDCalc's main calc container
                    'div[class*="calculator-form"]',
                    'form',
                    '.calc-main',
                    'main'
                ]

                calc_container = None
                for selector in calc_selectors:
                    calc_container = await page.query_selector(selector)
                    if calc_container:
                        break

                if calc_container:
                    # Take screenshot of just the calculator form
                    screenshot_bytes = await calc_container.screenshot(
                        type='jpeg',
                        quality=30  # Lower quality for smaller size
                    )
                else:
                    # Fallback: crop to just the center portion of viewport
                    # This avoids headers, footers, ads
                    screenshot_bytes = await page.screenshot(
                        type='jpeg',
                        quality=30,  # Lower quality
                        clip={'x': 200, 'y': 200, 'width': 800, 'height': 600}  # Crop to center
                    )

                # Convert to base64
                if screenshot_bytes:
                    details['screenshot_base64'] = base64.b64encode(screenshot_bytes).decode('utf-8')
                    logger.info(f"Screenshot captured: {len(screenshot_bytes)} bytes")

            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")

            logger.info(f"Found {len(details.get('fields', []))} fields for {details.get('title', 'Unknown')}")
            return details

        finally:
            await page.close()

    async def execute_calculator(self, calculator_id: str, inputs: Dict) -> Dict:
        """
        Execute calculator with provided input values.

        This is a MECHANICAL function - it only clicks/fills what you specify.
        YOU must first call get_calculator_details to SEE the calculator,
        then map patient data to the EXACT button text or input values shown.

        Args:
            calculator_id (str): Calculator ID or slug
            inputs (Dict): Mapped field values where:
                - Keys: Field names (e.g., "age", "history", "troponin")
                - Values: EXACT button text or numeric values
                  Examples:
                    - "age": "≥65" (button text)
                    - "history": "Moderately suspicious" (button text)
                    - "troponin": "≤1x normal limit" (button text)
                    - "ldl": "120" (numeric input)

        Returns:
            Dict containing:
                - success (bool): Whether calculation succeeded
                - score (str): Calculated score (e.g., "5 points")
                - risk (str): Risk category/percentage
                - interpretation (str): Clinical interpretation

        Important:
            Values must match EXACTLY what appears in the calculator.
            Use get_calculator_details first to see available options.
        """
        page = await self.context.new_page()

        try:
            # Navigate to calculator
            if calculator_id.isdigit():
                url = f"{self.base_url}/calc/{calculator_id}"
            else:
                # Assume it's a slug and try to use it directly
                url = f"{self.base_url}/calc/{calculator_id}"

            logger.info(f"Executing calculator: {calculator_id}")
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(2000)  # Wait for React to render

            # Map common input values to button text
            value_mappings = {
                # History
                'slightly_suspicious': 'Slightly suspicious',
                'moderately_suspicious': 'Moderately suspicious',
                'highly_suspicious': 'Highly suspicious',

                # Age
                '45': '<45',
                'less_than_45': '<45',
                '<45': '<45',
                '45-64': '45-64',
                '45_64': '45-64',
                '65': '≥65',
                '>=65': '≥65',
                'greater_than_65': '≥65',

                # Risk factors
                '0': 'No known risk factors',
                'no': 'No known risk factors',
                'none': 'No known risk factors',
                '1': '1-2 risk factors',
                '2': '1-2 risk factors',
                '1-2': '1-2 risk factors',
                '3': '≥3 risk factors or history of atherosclerotic disease',
                '>=3': '≥3 risk factors or history of atherosclerotic disease'
            }

            # Special handling for ECG and Troponin based on field name
            ecg_mappings = {
                'normal': 'Normal',
                'non_specific': 'Non-specific repolarization disturbance',
                'significant': 'Significant ST deviation',
                'abnormal': 'Non-specific repolarization disturbance'
            }

            troponin_mappings = {
                'normal': '≤1x normal limit',
                'elevated_1x': '1-2x normal limit',
                '1x': '1-2x normal limit',
                'elevated_2x': '>2x normal limit',
                '2x': '>2x normal limit',
                '>2x': '>2x normal limit'
            }

            # Fill inputs and click buttons based on input values
            for field_name, value in inputs.items():
                logger.info(f"Trying to set {field_name} to '{value}'")

                # First try to fill numeric/text inputs
                filled = False

                # Try various selectors for input fields
                input_selectors = [
                    f'input[name="{field_name}"]',
                    f'input[id="{field_name}"]',
                    f'input[placeholder*="{field_name}"]'
                ]

                for selector in input_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, str(value))
                            filled = True
                            logger.info(f"  ✅ Filled input field: {field_name} = {value}")
                            break
                    except:
                        pass

                # If not an input field, try button clicking
                if not filled:
                    # Normalize the field name
                    field_name_normalized = field_name.lower().replace('_', ' ')

                    # Get the mapped button text based on field type
                    if 'ecg' in field_name.lower() or 'ekg' in field_name.lower():
                        button_text = ecg_mappings.get(str(value).lower(), str(value))
                    elif 'troponin' in field_name.lower():
                        button_text = troponin_mappings.get(str(value).lower(), str(value))
                    else:
                        button_text = value_mappings.get(str(value).lower(), str(value))

                    logger.info(f"  Trying to click button for: '{button_text}'")

                    # Try multiple strategies to click the button
                    clicked = False

                    # Strategy 1: Direct button text
                    try:
                        button_selector = f"button:has-text('{button_text}')"
                        if await page.locator(button_selector).count() > 0:
                            await page.click(button_selector)
                            clicked = True
                            logger.info(f"  ✅ Clicked button: {button_text}")
                    except:
                        pass

                    # Strategy 2: Div with calc_option class
                    if not clicked:
                        try:
                            option_selector = f"div[class*='calc_option']:has-text('{button_text}')"
                            if await page.locator(option_selector).count() > 0:
                                await page.click(option_selector)
                                clicked = True
                                logger.info(f"  ✅ Clicked option: {button_text}")
                        except:
                            pass

                    # Strategy 3: Any clickable element with the text
                    if not clicked:
                        try:
                            any_selector = f"*:has-text('{button_text}'):not(body):not(html)"
                            elements = await page.locator(any_selector).all()
                            for element in elements:
                                try:
                                    await element.click()
                                    clicked = True
                                    logger.info(f"  ✅ Clicked element with text: {button_text}")
                                    break
                                except:
                                    continue
                        except:
                            pass

                    if not clicked:
                        logger.warning(f"  ⚠️ Could not click option for {field_name}: {button_text}")

                # Wait for React to update
                await page.wait_for_timeout(500)

            # Wait for results to update
            await page.wait_for_timeout(1000)

            # Extract results
            results = await page.evaluate('''
                () => {
                    // Look for score text
                    const scoreElements = Array.from(document.querySelectorAll('*')).filter(
                        el => /\\d+ points?/.test(el.textContent) && el.children.length === 0
                    );
                    const score = scoreElements.length > 0 ? scoreElements[0].textContent.trim() : null;

                    // Look for risk text
                    const riskElements = Array.from(document.querySelectorAll('*')).filter(
                        el => /Risk.*%/.test(el.textContent) && el.textContent.length < 200
                    );
                    const risk = riskElements.length > 0 ? riskElements[0].textContent.trim() : null;

                    // Look for interpretation
                    const interpretElements = Array.from(document.querySelectorAll('*')).filter(
                        el => /(Low|Moderate|High) Score/.test(el.textContent)
                    );
                    const interpretation = interpretElements.length > 0 ? interpretElements[0].textContent.trim() : null;

                    return {
                        score: score,
                        risk: risk,
                        interpretation: interpretation,
                        success: !!(score || risk)
                    };
                }
            ''')

            if results['success']:
                logger.info(f"✅ Calculation successful: {results.get('score', 'N/A')}")
            else:
                logger.warning("⚠️ Could not extract results (may be auto-calculated)")

            return results

        finally:
            await page.close()

    async def cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser cleanup complete")


# Quick test
if __name__ == "__main__":
    async def quick_test():
        client = MDCalcClient()
        await client.initialize(headless=False)

        # Test search
        results = await client.search_calculators("heart")
        print(f"Search found {len(results)} calculators")
        if results:
            print(f"First: {results[0]['title']}")

        # Test details
        details = await client.get_calculator_details("1752")
        print(f"\nCalculator: {details.get('title', 'Unknown')}")
        print(f"Fields: {len(details.get('fields', []))}")

        # Test execution
        inputs = {
            'history': 'slightly_suspicious',
            'age': '45-64',
            'ecg': 'normal',
            'risk_factors': '1-2',
            'troponin': 'normal'
        }

        result = await client.execute_calculator("1752", inputs)
        print(f"\nResult: {result}")

        await client.cleanup()

    asyncio.run(quick_test())