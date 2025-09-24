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
    Uses visual understanding instead of maintaining 825 different selector configurations.

    Key Design Principles:
    - Smart Agent, Dumb Tools: Client is mechanical, Claude provides intelligence
    - Visual Understanding: Screenshots enable field mapping without hardcoding
    - Exact Matching: Field names must match exactly as shown in UI (no normalization)
    - Optimized Catalog: Compact format reduces tokens from 82K to 31K

    Methods:
        get_all_calculators(): Load optimized catalog (ID, name, category only)
        search_calculators(): Use MDCalc's semantic web search
        get_calculator_details(): Get screenshot for visual understanding
        execute_calculator(): Execute with exact field names from screenshot
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
        """
        Initialize Playwright browser instance.

        Args:
            headless (bool): Run browser in headless mode (default: True).
                            Set to False to see browser during demos.
                            Controlled by MDCALC_HEADLESS env var in MCP config.
            use_auth (bool): Load authentication state if available.

        Demo Mode:
            When headless=False and Chrome is running with --remote-debugging-port=9222,
            connects to the existing browser instead of launching a new one.
            This allows using a pre-positioned browser window for demos.
        """
        self.playwright = await async_playwright().start()

        # Check if we should connect to existing browser (demo mode)
        use_existing_browser = False
        if not headless:
            # Try to connect to existing Chrome instance on port 9222
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 9222))
                sock.close()
                use_existing_browser = (result == 0)
                if use_existing_browser:
                    logger.info("Demo mode: Connecting to existing Chrome browser on port 9222")
            except:
                pass

        if use_existing_browser:
            # Connect to existing browser instance
            try:
                self.browser = await self.playwright.chromium.connect_over_cdp(
                    endpoint_url="http://localhost:9222",
                    timeout=5000
                )
                logger.info("Successfully connected to existing Chrome browser")
            except Exception as e:
                logger.warning(f"Failed to connect to existing browser: {e}")
                logger.info("Falling back to launching new browser")
                # Fallback to launching new browser
                self.browser = await self.playwright.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
        else:
            # Launch new browser (normal mode)
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )

        # For demo mode with existing browser, try to reuse existing context
        if use_existing_browser:
            # Get existing contexts
            contexts = self.browser.contexts
            if contexts:
                # Reuse first available context
                self.context = contexts[0]
                logger.info(f"Demo mode: Reusing existing browser context with {len(self.context.pages)} open tabs")
            else:
                # Create new context in existing browser
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36'
                )
                logger.info("Demo mode: Created new context in existing browser")
        else:
            # Normal mode - create new context
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
        Load the complete MDCalc calculator catalog optimized for LLM processing.

        Returns a compact format to minimize token usage while preserving
        all essential information for calculator selection.

        Returns:
            List[Dict]: List of 825 calculators, each containing:
                - id (str): Calculator ID (e.g., "1752")
                - name (str): Calculator name (e.g., "HEART Score")
                - category (str): Medical category (e.g., "Cardiology")

        Note:
            URLs are omitted but can be constructed as:
            https://www.mdcalc.com/calc/{id}
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

                # Return optimized format - just id, name, and category
                optimized = []
                for calc in catalog['calculators']:
                    # Truncate very long names to save tokens
                    name = calc.get('name', '')
                    if len(name) > 100:
                        name = name[:97] + '...'

                    optimized.append({
                        'id': calc.get('id'),
                        'name': name,
                        'category': calc.get('category', 'General')
                    })

                return optimized
        except Exception as e:
            raise RuntimeError(f"Failed to load calculator catalog: {e}")

    async def search_calculators(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for calculators using MDCalc's web search.

        Uses MDCalc's sophisticated search algorithm that understands
        clinical relationships and semantic matches.

        Args:
            query (str): Search term (e.g., "chest pain", "HEART", "pneumonia")
            limit (int): Maximum results to return (default: 10)

        Returns:
            List[Dict]: Matching calculators, each containing:
                - id (str): Calculator ID
                - title (str): Calculator name
                - slug (str): URL slug
                - url (str): Full MDCalc URL
                - description (str): Brief description (if available)
        """
        # Use MDCalc's web search directly for better semantic matching
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

                    // Check if we're actually on a search results page
                    // MDCalc shows "No tool found for..." when there are no results
                    // Look for the specific div with class containing "search-results-message"
                    const noToolFound = document.querySelector('.search_search-results-message__nK_GX, [class*="search-results-message"]');
                    if (noToolFound && noToolFound.textContent.includes('No tool')) {{
                        console.log("No search results - MDCalc shows:", noToolFound.textContent);
                        return [];
                    }}

                    // Look for search result rows - these have the specific class
                    const resultRows = document.querySelectorAll('.calculatorRow_row-container__HM_dC');

                    if (resultRows.length === 0) {{
                        // No results found - return empty array
                        return [];
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
                logger.info(f"Starting screenshot capture for calculator: {calculator_id}")

                # STRATEGY: Dynamically adjust zoom to fit calculator in viewport
                # First, find the calculator container and measure it
                # Also check if there's a Results section that might overlay
                measurements = await page.evaluate('''
                    () => {
                        const container = document.querySelector('.side-by-side-container, .calc__body');
                        const calcHeight = container ? container.scrollHeight : 0;

                        // Find the last input field to ensure it's visible
                        const allInputs = container ? container.querySelectorAll('input, select, textarea, [class*="calc_option"]') : [];
                        let lastFieldBottom = 0;
                        if (allInputs.length > 0) {
                            const lastField = allInputs[allInputs.length - 1];
                            const rect = lastField.getBoundingClientRect();
                            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                            lastFieldBottom = rect.bottom + scrollTop;
                        }

                        // Check if there's a results section
                        const resultsSection = document.querySelector('[class*="result"], [class*="Result"]');
                        const hasResults = resultsSection !== null;

                        return {
                            calcHeight: calcHeight,
                            lastFieldBottom: lastFieldBottom,
                            viewportHeight: window.innerHeight,
                            hasResults: hasResults
                        };
                    }
                ''')

                calc_height = measurements['calcHeight']
                viewport_height = measurements['viewportHeight']
                last_field_bottom = measurements['lastFieldBottom']
                has_results = measurements['hasResults']

                logger.info(f"Calculator height: {calc_height}px, Last field bottom: {last_field_bottom}px, Viewport: {viewport_height}px, Has results: {has_results}")

                # Calculate optimal zoom level
                # Use the last field position if available, otherwise use container height
                optimal_zoom = 100
                target_height = last_field_bottom if last_field_bottom > 0 else calc_height

                if target_height > viewport_height:
                    # Since we're hiding the Results overlay, we can use more of the viewport
                    # Use 90% of viewport to fit the calculator with just a small margin
                    margin_factor = 90
                    optimal_zoom = int((viewport_height / target_height) * margin_factor)
                    optimal_zoom = max(50, min(optimal_zoom, 100))  # Clamp between 50-100%
                    logger.info(f"Calculated zoom: {optimal_zoom}% (using {margin_factor}% margin)")

                original_zoom = await page.evaluate('() => document.body.style.zoom || "100%"')
                logger.info(f"Original zoom: {original_zoom}, Setting optimal zoom: {optimal_zoom}%")

                # Apply the calculated zoom
                await page.evaluate(f'() => {{ document.body.style.zoom = "{optimal_zoom}%"; }}')
                logger.info(f"Set zoom to {optimal_zoom}% to fit calculator")

                # CRITICAL: Hide the sticky Results overlay during screenshot
                # MDCalc uses a sticky Results section that covers bottom fields
                await page.evaluate('''
                    () => {
                        // Find and temporarily hide the Results section
                        const results = document.querySelectorAll('[class*="result"], [class*="Result"], [class*="score"], .calc__result');
                        results.forEach(el => {
                            el.setAttribute('data-original-display', el.style.display);
                            el.style.display = 'none';
                        });

                        // Also hide any sticky/fixed positioned elements that might overlay
                        const allElements = document.querySelectorAll('*');
                        allElements.forEach(el => {
                            const style = window.getComputedStyle(el);
                            if (style.position === 'sticky' || style.position === 'fixed') {
                                // Check if it's part of the calculator results (not header/nav)
                                const text = el.textContent || '';
                                if (text.includes('Result') || text.includes('Score') || text.includes('point')) {
                                    el.setAttribute('data-original-display', el.style.display);
                                    el.style.display = 'none';
                                }
                            }
                        });
                    }
                ''')
                logger.info("Temporarily hid Results overlay for screenshot")

                # Wait for layout to adjust
                await page.wait_for_timeout(500)

                # Find the FIRST form field of ANY type in the calculator
                # This includes: text inputs, radio buttons, checkboxes, selects, etc.
                first_calc_field = await page.query_selector('''
                    .side-by-side-container input,
                    .side-by-side-container select,
                    .side-by-side-container textarea,
                    .side-by-side-container button[role="radio"],
                    .calc__body input,
                    .calc__body select,
                    .calc__body textarea
                '''.replace('\n', ' ').strip())

                # Alternative: Find the first calc_input-wrapper which contains any field
                if not first_calc_field:
                    first_calc_field = await page.query_selector('.calc_input-wrapper__LavoA')

                if first_calc_field:
                    logger.info("Found first calculator field, scrolling to top of viewport")
                    await first_calc_field.evaluate('(el) => el.scrollIntoView({block: "start", behavior: "instant"})')
                    # With zoom out, we might not need as much scroll adjustment
                    await page.evaluate('window.scrollBy(0, -100)')
                else:
                    # Fallback: just scroll to top
                    await page.evaluate('window.scrollTo(0, 0)')

                await page.wait_for_timeout(500)

                # Log current viewport and page dimensions after zoom
                dimensions = await page.evaluate('''
                    () => {
                        return {
                            viewport: {
                                width: window.innerWidth,
                                height: window.innerHeight
                            },
                            zoom: document.body.style.zoom,
                            scrollPosition: {
                                x: window.pageXOffset || document.documentElement.scrollLeft,
                                y: window.pageYOffset || document.documentElement.scrollTop
                            }
                        }
                    }
                ''')
                logger.info(f"Page dimensions after zoom and scroll: {dimensions}")

                # Take screenshot with zoomed out view
                logger.info("Taking viewport screenshot with zoomed out view")
                screenshot_bytes = await page.screenshot(
                    type='jpeg',
                    quality=20,  # Low quality to reduce size
                    full_page=False  # Just the viewport
                )
                logger.info(f"Viewport screenshot captured: {len(screenshot_bytes) if screenshot_bytes else 0} bytes")

                # Restore the Results section visibility
                await page.evaluate('''
                    () => {
                        // Restore all hidden elements
                        const hidden = document.querySelectorAll('[data-original-display]');
                        hidden.forEach(el => {
                            el.style.display = el.getAttribute('data-original-display') || '';
                            el.removeAttribute('data-original-display');
                        });
                    }
                ''')
                logger.info("Restored Results overlay visibility")

                # Restore original zoom
                await page.evaluate(f'() => {{ document.body.style.zoom = "{original_zoom}"; }}')
                logger.info(f"Restored zoom to: {original_zoom}")

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

            # DEBUG: Let's see what clickable elements are actually on the page
            if logger.level <= logging.DEBUG:
                all_clickables = await page.evaluate('''() => {
                    // Try multiple possible selectors
                    const buttons = Array.from(document.querySelectorAll('button')).map(b => ({text: b.textContent.trim(), tag: 'button'}));
                    const divOptions = Array.from(document.querySelectorAll('div[class*="option"]')).map(d => ({text: d.textContent.trim(), tag: 'div.option', class: d.className}));
                    const allDivs = Array.from(document.querySelectorAll('div')).filter(d => {
                        const text = d.textContent.trim();
                        return (text === 'Moderately suspicious' || text === '45-64' || text === 'Normal' ||
                                text === '1-2 risk factors' || text.includes('normal limit'));
                    }).map(d => ({text: d.textContent.trim(), tag: 'div', class: d.className}));

                    return {
                        buttons: buttons.slice(0, 10),
                        divOptions: divOptions.slice(0, 10),
                        targetDivs: allDivs.slice(0, 10)
                    };
                }''')
                logger.debug(f"  Buttons: {all_clickables.get('buttons', [])}")
                logger.debug(f"  Div options: {all_clickables.get('divOptions', [])}")
                logger.debug(f"  Target divs: {all_clickables.get('targetDivs', [])}")

            # Fill inputs and click buttons based on input values
            for field_name, value in inputs.items():
                logger.info(f"Trying to set {field_name} to '{value}'")

                # For MDCalc calculators, most fields are buttons not inputs
                # Only try input fields if the value looks numeric
                filled = False

                # Check if value looks like a number (for numeric inputs like cholesterol values)
                try:
                    float(value)
                    is_numeric = True
                except (ValueError, TypeError):
                    is_numeric = False

                # Only try input fields for numeric values
                if is_numeric:
                    # Try to find input field by label text or placeholder
                    # For fields like "Total Cholesterol", "HDL Cholesterol"
                    try:
                        # Strategy 1: Find input by label text
                        label_element = await page.query_selector(f'text="{field_name}"')
                        if label_element:
                            # Find the input associated with this label
                            input_element = await page.evaluate('''(label) => {
                                // Check if label has a 'for' attribute
                                const forAttr = label.getAttribute('for');
                                if (forAttr) {
                                    const input = document.getElementById(forAttr);
                                    if (input) return input.id;
                                }
                                // Check if input is within the same container
                                const container = label.closest('div');
                                if (container) {
                                    const input = container.querySelector('input');
                                    if (input) {
                                        // Give it a temporary ID so we can select it
                                        const tempId = 'temp_' + Math.random().toString(36).substring(7);
                                        input.id = tempId;
                                        return tempId;
                                    }
                                }
                                return null;
                            }''', label_element)

                            if input_element:
                                await page.fill(f'#{input_element}', str(value))
                                filled = True
                                logger.info(f"  ✅ Filled input field: {field_name} = {value}")
                    except:
                        pass

                    # Strategy 2: Try various selectors
                    if not filled:
                        input_selectors = [
                            f'input[placeholder*="{field_name}"]',
                            f'input[aria-label*="{field_name}"]',
                            # Try with normalized field name
                            f'input[name="{field_name.lower().replace(" ", "_")}"]',
                            f'input[name="{field_name.lower().replace(" ", "")}"]',
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

                # If not filled (or not numeric), try button clicking
                if not filled:
                    # NO NORMALIZATION - use exact field names as passed
                    # The value should already be the exact button text
                    button_text = str(value)

                    logger.info(f"  Trying to click button '{button_text}' for field '{field_name}'")

                    # Try multiple strategies to click the button
                    clicked = False

                    # Strategy 1: Direct button text
                    try:
                        button_selector = f"button:has-text('{button_text}')"
                        count = await page.locator(button_selector).count()
                        logger.debug(f"  Strategy 1: Found {count} buttons with text '{button_text}'")
                        if count > 0:
                            await page.click(button_selector)
                            clicked = True
                            logger.info(f"  ✅ Clicked button: {button_text}")
                    except Exception as e:
                        logger.debug(f"  Strategy 1 failed: {e}")

                    # Strategy 2: Any clickable div with exact text (MDCalc uses divs for buttons)
                    if not clicked:
                        try:
                            # MDCalc uses divs as buttons, not actual button elements
                            # Use text= for exact match, find the innermost element
                            option_selector = f"div:text-is('{button_text}')"  # Exact text match
                            elements = page.locator(option_selector)
                            count = await elements.count()
                            logger.debug(f"  Strategy 2: Found {count} divs with exact text '{button_text}'")

                            # If there's only one element, click it (no ambiguity)
                            if count == 1:
                                element = elements.first
                                # Check if already selected - check computed styles more carefully
                                element_state = await element.evaluate('''el => {
                                    const style = window.getComputedStyle(el);
                                    const bgColor = style.backgroundColor;

                                    // MDCalc uses teal/green for selected state
                                    // rgb(26, 188, 156) is the teal color
                                    // Check if background is teal/green (selected state)
                                    const isTeal = bgColor === 'rgb(26, 188, 156)' ||
                                                  bgColor === 'rgba(26, 188, 156, 1)';

                                    // Also check parent element for selection state
                                    let parentHasTeal = false;
                                    if (el.parentElement) {
                                        const parentBg = window.getComputedStyle(el.parentElement).backgroundColor;
                                        parentHasTeal = parentBg === 'rgb(26, 188, 156)' ||
                                                       parentBg === 'rgba(26, 188, 156, 1)';
                                    }

                                    return isTeal || parentHasTeal;
                                }''')

                                if element_state:
                                    clicked = True
                                    logger.info(f"  ✅ Option already selected: {button_text}")
                                else:
                                    await element.click()
                                    clicked = True
                                    logger.info(f"  ✅ Clicked option: {button_text}")
                            elif count > 1:
                                # Multiple elements found - skip to Strategy 3 for context-aware clicking
                                logger.debug(f"  Multiple elements found, need context-aware selection")
                        except Exception as e:
                            logger.debug(f"  Strategy 2 failed: {e}")

                    # Strategy 3: Context-aware search - find button near the field label
                    if not clicked:
                        # The field_name should be the exact label seen in the UI
                        logger.info(f"  Looking for {button_text} button near field '{field_name}'")

                        try:
                            # Get all buttons/divs with this text
                            # MDCalc uses divs as clickable options
                            button_locator = page.locator(f"button:text-is('{button_text}'), div:text-is('{button_text}')")
                            all_buttons = await button_locator.element_handles()

                            logger.debug(f"  Strategy 3: Found {len(all_buttons)} elements with text '{button_text}'")

                            for button in all_buttons:
                                # Check if this button is near the field label
                                is_in_field = await button.evaluate('''(el, fieldName) => {
                                    // Walk up the DOM to find if we're in the right field
                                    let parent = el.parentElement;
                                    let maxLevels = 5;  // Only go up 5 levels for speed
                                    while (parent && maxLevels > 0) {
                                        // Check if the parent contains the field name
                                        if (parent.textContent.includes(fieldName)) {
                                            return true;
                                        }
                                        parent = parent.parentElement;
                                        maxLevels--;
                                    }
                                    return false;
                                }''', field_name)

                                if is_in_field:
                                    # Check if already selected using exact RGB values
                                    button_state = await button.evaluate('''el => {
                                        const bgColor = window.getComputedStyle(el).backgroundColor;
                                        const parentBgColor = el.parentElement ?
                                            window.getComputedStyle(el.parentElement).backgroundColor : '';

                                        // MDCalc uses rgb(26, 188, 156) for selected state
                                        const isTeal = bgColor === 'rgb(26, 188, 156)' ||
                                                      bgColor === 'rgba(26, 188, 156, 1)' ||
                                                      parentBgColor === 'rgb(26, 188, 156)' ||
                                                      parentBgColor === 'rgba(26, 188, 156, 1)';

                                        return isTeal;
                                    }''')

                                    if button_state:
                                        clicked = True
                                        logger.info(f"  ✅ {button_text} already selected for field '{field_name}'")
                                    else:
                                        await button.click()
                                        clicked = True
                                        logger.info(f"  ✅ Clicked {button_text} for field '{field_name}'")
                                    break

                        except Exception as e:
                            logger.debug(f"  Strategy 3 failed: {e}")

                    if not clicked:
                        logger.warning(f"  ⚠️ Could not click option for {field_name}: {button_text}")

                # Wait for React to update (reduced for speed)
                await page.wait_for_timeout(100)

            # Wait for results to update (MDCalc takes time to calculate)
            await page.wait_for_timeout(2000)

            # Take a screenshot of the result (for debugging/validation)
            try:
                result_screenshot = await page.screenshot(
                    type='jpeg',
                    quality=85,
                    full_page=False  # Just viewport to capture results
                )
                # Save to screenshots directory if it exists (for tests)
                screenshots_dir = Path(__file__).parent.parent / "tests" / "screenshots"
                if screenshots_dir.exists():
                    result_path = screenshots_dir / f"{calculator_id}_result.jpg"
                    with open(result_path, 'wb') as f:
                        f.write(result_screenshot)
                    logger.info(f"📸 Result screenshot saved to: {result_path}")
            except Exception as e:
                logger.warning(f"Could not capture result screenshot: {e}")

            # Extract results - look for result containers and score displays
            results = await page.evaluate('''
                () => {
                    let score = null;
                    let risk = null;
                    let interpretation = null;

                    // Strategy 1: Look for result containers (calc_result class pattern)
                    // MDCalc consistently uses classes with "calc_result" in them
                    const resultContainers = document.querySelectorAll('[class*="calc_result"], [class*="result_container"], [class*="score_display"]');

                    for (const container of resultContainers) {
                        // Look for heading elements (h1, h2, h3) within the result container
                        // These typically contain the score
                        const headings = container.querySelectorAll('h1, h2, h3');
                        for (const heading of headings) {
                            const text = heading.textContent.trim();
                            // Match patterns like "8 points", "8", etc.
                            const scoreMatch = text.match(/^(\\d+)\\s*(points?|pts?)?/i);
                            if (scoreMatch && !score) {
                                score = scoreMatch[1] + ' points';

                                // Also look for risk/interpretation in the same container
                                const containerText = container.textContent;
                                // Extract risk percentage if present
                                const riskMatch = containerText.match(/(\\d+\\.?\\d*)%.*?(risk|per year)/i);
                                if (riskMatch && !risk) {
                                    risk = riskMatch[0];
                                }
                                break;
                            }
                        }
                        if (score) break; // Found score, stop looking
                    }

                    // Strategy 2: If no result container found, look for prominent score displays
                    if (!score) {
                        // Look for large text elements containing scores
                        const allElements = document.querySelectorAll('div, span, h1, h2, h3, p');
                        for (const el of allElements) {
                            const text = el.textContent.trim();

                            // Skip long text (definitely not a score)
                            if (text.length > 50) continue;

                            // Check if it matches score pattern
                            const scoreMatch = text.match(/^(\\d+)\\s*(points?|pts?)?$/i);
                            if (scoreMatch) {
                                // Verify it's prominently displayed
                                const style = window.getComputedStyle(el);
                                const fontSize = parseFloat(style.fontSize);
                                const isVisible = style.display !== 'none' && style.visibility !== 'hidden';

                                if (isVisible && fontSize >= 24) { // Large font for scores
                                    score = scoreMatch[1] + ' points';
                                    break;
                                }
                            }
                        }
                    }

                    // Look for interpretation (Low/Moderate/High Score)
                    if (!interpretation) {
                        const interpElements = document.querySelectorAll('*');
                        for (const el of interpElements) {
                            const text = el.textContent.trim();
                            if (text.length < 100) {
                                const match = text.match(/(Low|Moderate|High)\\s*(Score|Risk)\\s*\\(?(\\d+-?\\d*\\s*points?)\\)?/i);
                                if (match) {
                                    interpretation = match[0];
                                    break;
                                }
                            }
                        }
                    }

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