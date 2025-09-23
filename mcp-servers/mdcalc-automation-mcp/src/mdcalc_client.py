#!/usr/bin/env python3
"""
MDCalc Automation Client V2
Updated to handle MDCalc's React-based button interface
"""

import asyncio
from playwright.async_api import async_playwright
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MDCalcClient:
    """
    Playwright client for MDCalc automation.
    Handles React-based button interface.
    """

    def __init__(self):
        self.base_url = "https://www.mdcalc.com"
        self.playwright = None
        self.browser = None
        self.context = None
        self.config = self.load_config()
        self.selectors = self.config['selectors']

    def load_config(self):
        """Load configuration from mdcalc_config.json."""
        config_path = Path(__file__).parent / "mdcalc_config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            return json.load(f)

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

    async def search_calculators(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for calculators by condition or name."""
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
        """Get calculator structure and current values."""
        page = await self.context.new_page()

        try:
            # Handle both numeric IDs and slugs
            if calculator_id.isdigit():
                url = f"{self.base_url}/calc/{calculator_id}"
            else:
                known_ids = self.config.get('calculator_ids', {})
                calc_id = known_ids.get(calculator_id.replace('-', '_'), calculator_id)
                url = f"{self.base_url}/calc/{calc_id}"

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

            logger.info(f"Found {len(details.get('fields', []))} fields for {details.get('title', 'Unknown')}")
            return details

        finally:
            await page.close()

    async def execute_calculator(self, calculator_id: str, inputs: Dict) -> Dict:
        """Execute calculator by clicking appropriate buttons."""
        page = await self.context.new_page()

        try:
            # Navigate to calculator
            if calculator_id.isdigit():
                url = f"{self.base_url}/calc/{calculator_id}"
            else:
                known_ids = self.config.get('calculator_ids', {})
                calc_id = known_ids.get(calculator_id.replace('-', '_'), calculator_id)
                url = f"{self.base_url}/calc/{calc_id}"

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