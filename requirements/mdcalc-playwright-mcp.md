# MDCalc Playwright MCP Server - Design Specification

## Overview
This MCP server provides programmatic access to MDCalc.com through Playwright browser automation. The server provides **atomic, mechanical tools** with NO clinical intelligence - all mapping and interpretation is handled by the Claude agent.

## Design Principle: Dumb Tools, Smart Agent

The MCP tools are purely mechanical executors:
- **get_calculator_details**: Returns exactly what's on the page, no interpretation
- **execute_calculator**: Fills in exactly what Claude provides, no mapping
- **search_calculators**: Simple text search, no clinical understanding

All intelligence resides in Claude:
- Clinical interpretation of symptoms
- Value mapping and conversions
- Risk factor counting
- Missing data handling
- Unit conversions
- Threshold determinations
- Clinical judgment calls

## Recording-First Development Approach

### Phase 0: Create Recordings
Before building automation, use Playwright's recording feature:

```python
# tools/recording-generator/record_interaction.py
from playwright.sync_api import sync_playwright

def record_mdcalc_interaction():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(record_har_path="mdcalc.har",
                                     record_video_dir="recordings/")
        
        # Start recording
        page = context.new_page()
        page.goto("https://www.mdcalc.com")
        
        # Manually interact with site while recording
        page.pause()  # This opens Playwright Inspector
        
        # Save the recorded actions
        context.close()
```

### Use Recordings for Selectors
Parse recordings to extract reliable selectors:
```python
# Parse recording to find element selectors
with open('recordings/mdcalc-search.json', 'r') as f:
    recording = json.load(f)
    selectors = extract_selectors(recording)
```

## Core Components

### 1. mdcalc_mcp.py (Main Server - Simple Tool Provider)

```python
class MDCalcMCP:
    """
    Simple MCP server - provides mechanical tools only.
    NO intelligence, NO mapping, NO clinical logic.
    """
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.selectors = self.load_selectors_from_recordings()
        
    # Tool definitions - ATOMIC operations only
    tools = [
        {
            "name": "search_calculators",
            "description": "Search MDCalc for text matching query",
            "parameters": {
                "query": "Search term (passed through as-is)",
                "limit": "Max results to return (default 10)"
            }
        },
        {
            "name": "get_calculator_details", 
            "description": "Get raw input fields from calculator page",
            "parameters": {
                "calculator_id": "MDCalc calculator ID or URL slug"
            }
        },
        {
            "name": "execute_calculator",
            "description": "Fill form with provided values and click calculate",
            "parameters": {
                "calculator_id": "Calculator to execute",
                "inputs": "Dictionary of values (exactly as Claude mapped them)"
            }
        }
        # Note: No batch_execute - Claude handles parallel calls
        # Note: No mapping logic - Claude handles all interpretation
    ]
```

### 2. mdcalc_client.py (Playwright Automation - Mechanical Only)

```python
class MDCalcClient:
    """
    Playwright client for MDCalc automation.
    MECHANICAL ONLY - no intelligence, just form filling.
    """
    
    async def get_calculator_details(self, calculator_id: str) -> Dict:
        """
        Returns RAW calculator requirements - no interpretation.
        Claude will do all the mapping.
        
        Example return:
        {
            "title": "HEART Score for Major Cardiac Events",
            "inputs": [
                {
                    "name": "age",
                    "type": "number",
                    "label": "Age",
                    "min": 0,
                    "max": 120
                },
                {
                    "name": "history",
                    "type": "select",
                    "label": "History",
                    "options": [
                        {"value": "slightly_suspicious", "text": "Slightly suspicious"},
                        {"value": "moderately_suspicious", "text": "Moderately suspicious"},
                        {"value": "highly_suspicious", "text": "Highly suspicious"}
                    ]
                },
                {
                    "name": "ecg",
                    "type": "select", 
                    "label": "ECG",
                    "options": [
                        {"value": "normal", "text": "Normal"},
                        {"value": "st_depression", "text": "Non-specific repolarization"},
                        {"value": "significant_st_deviation", "text": "Significant ST deviation"}
                    ]
                },
                {
                    "name": "risk_factors",
                    "type": "number",
                    "label": "Number of Risk Factors",
                    "min": 0,
                    "max": 5
                },
                {
                    "name": "troponin",
                    "type": "select",
                    "label": "Initial Troponin",
                    "options": [
                        {"value": "normal", "text": "≤ normal limit"},
                        {"value": "1_3x", "text": "1-3x normal limit"},
                        {"value": "gt_3x", "text": ">3x normal limit"}
                    ]
                }
            ]
        }
        """
        page = await self.context.new_page()
        
        # Navigate to calculator
        url = f"{self.base_url}/calc/{calculator_id}"
        await page.goto(url, wait_until='networkidle')
        
        # Extract RAW structure - no interpretation
        details = await page.evaluate('''
            () => {
                const title = document.querySelector('h1')?.textContent?.trim();
                const description = document.querySelector('.calc-description')?.textContent?.trim();
                
                const inputs = [];
                // Get all form inputs exactly as they appear
                document.querySelectorAll('input, select, [role="radio"]').forEach(element => {
                    if (element.name || element.id) {
                        const label = element.closest('label')?.textContent || 
                                    document.querySelector(`label[for="${element.id}"]`)?.textContent;
                        
                        const input = {
                            name: element.name || element.id,
                            label: label?.trim(),
                            type: element.type || element.tagName.toLowerCase()
                        };
                        
                        // For selects, get all options exactly as shown
                        if (element.tagName === 'SELECT') {
                            input.options = Array.from(element.options).map(opt => ({
                                value: opt.value,
                                text: opt.textContent.trim()
                            }));
                        }
                        
                        // Get any data attributes that might have thresholds
                        if (element.dataset.min) input.min = element.dataset.min;
                        if (element.dataset.max) input.max = element.dataset.max;
                        
                        inputs.push(input);
                    }
                });
                
                return { title, description, inputs };
            }
        ''')
        
        await page.close()
        return details
        
    async def execute_calculator(self, calculator_id: str, inputs: Dict) -> Dict:
        """
        Execute calculator with Claude's pre-mapped values.
        NO MAPPING HERE - Claude has already done all the intelligent work.
        
        Claude provides:
        {
            "age": 68,  # Claude determined exact value
            "history": "moderately_suspicious",  # Claude interpreted symptoms
            "ecg": "normal",  # Claude mapped from health records
            "risk_factors": 3,  # Claude counted them
            "troponin": "normal"  # Claude interpreted lab value
        }
        
        We just mechanically fill the form.
        """
        page = await self.context.new_page()
        
        # Navigate to calculator
        url = f"{self.base_url}/calc/{calculator_id}"
        await page.goto(url, wait_until='networkidle')
        
        # Mechanically fill in Claude's values
        for field_name, value in inputs.items():
            # Try multiple selector strategies
            selectors = [
                f'input[name="{field_name}"]',
                f'select[name="{field_name}"]',
                f'#{field_name}',
                f'[data-field="{field_name}"]'
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    
                    # Just fill in what Claude gave us
                    if await element.get_attribute('type') == 'radio':
                        await page.click(f'{selector}[value="{value}"]')
                    elif await element.get_attribute('type') == 'checkbox':
                        if value:
                            await element.check()
                    else:
                        await element.fill(str(value))
                    break
                except:
                    continue
                    
        # Click calculate button
        calculate_button = await page.wait_for_selector(
            self.selectors.get("calculate_button", "button:has-text('Calculate')")
        )
        await calculate_button.click()
        
        # Wait for and extract results
        await page.wait_for_selector('.result, .score', timeout=5000)
        
        # Return RAW results - Claude will interpret them
        results = await page.evaluate('''
            () => {
                const score = document.querySelector('.score, .primary-result')?.textContent?.trim();
                const risk = document.querySelector('.risk-level, .interpretation')?.textContent?.trim();
                const details = document.querySelector('.result-details')?.textContent?.trim();
                const recommendations = Array.from(
                    document.querySelectorAll('.recommendation li')
                ).map(li => li.textContent?.trim());
                
                return {
                    score,  // Raw score value
                    risk_category: risk,  // Raw risk text
                    interpretation: details,  // Raw interpretation
                    recommendations  // Raw recommendations
                };
            }
        ''')
        
        await page.close()
        return results
```

### 3. What the MCP Tools DO NOT Do

```python
# ❌ WRONG - Tools should NOT have this logic:

class MDCalcClient:
    # DON'T DO THIS - No mapping logic in tools!
    FIELD_MAPPINGS = {
        'age': ['patient_age', 'age_years'],  # ❌ NO
        'systolic_bp': ['sbp', 'systolic'],   # ❌ NO
    }
    
    # DON'T DO THIS - No clinical interpretation!
    def interpret_troponin(self, value):  # ❌ NO
        if value < 0.04:
            return "normal"
        elif value < 0.12:
            return "1_3x"
        else:
            return "gt_3x"
    
    # DON'T DO THIS - No risk factor counting!
    def count_risk_factors(self, patient_data):  # ❌ NO
        count = 0
        if patient_data.get('hypertension'):
            count += 1
        # etc...
        return count
```

### 4. Correct Division of Labor

```python
# ✅ CORRECT - Clear separation:

# MCP Tool (mechanical):
async def get_calculator_details("heart-score"):
    # Returns: ["age", "history", "ecg", "risk_factors", "troponin"]
    # With their types and options
    
# Claude Agent (intelligent):
# 1. Queries health data: "Get patient cardiac history and risk factors"
# 2. Maps intelligently:
#    - Age 68 → age: 68
#    - "Chest pressure for 2 hours" → history: "moderately_suspicious"
#    - HTN + DM + smoking → risk_factors: 3
#    - Troponin 0.02 → troponin: "normal"

# MCP Tool (mechanical):
async def execute_calculator("heart-score", claude_mapped_values):
    # Just fills form with Claude's values
    # Returns raw result
```

## Security & Performance

### No PHI Processing in Tools
- Tools never interpret or log patient data
- They only fill forms with what Claude provides
- No clinical decision logic

### Caching Strategy
```python
class CalculatorCache:
    """
    Cache calculator STRUCTURE only, not patient data.
    """
    def cache_calculator_details(self, calc_id, details):
        # Cache the form structure (fields, options)
        # NOT any patient values or calculations
```

### Error Handling
```python
async def execute_with_retry(func, max_attempts=3):
    """Simple retry for network issues only."""
    # No clinical error handling
    # No data interpretation on errors
    # Just mechanical retry logic
```

## Testing the Mechanical Nature

```python
# Test that tools are truly mechanical:

async def test_tool_has_no_intelligence():
    """
    Verify tools don't interpret data.
    """
    client = MDCalcClient()
    
    # Tool should return raw structure
    details = await client.get_calculator_details("cha2ds2-vasc")
    assert "options" in details["inputs"][0]  # Raw options
    assert "value" in details["inputs"][0]["options"][0]  # Raw values
    
    # Tool should NOT interpret
    # If we pass wrong value types, it should just try to fill them
    result = await client.execute_calculator("cha2ds2-vasc", {
        "age": "sixty-eight"  # Wrong format - tool doesn't fix it
    })
    # Tool mechanically tries to fill, may fail, that's OK
    # Claude should have provided correct format
```

## Summary

The MCP tools are intentionally "dumb" mechanical executors that:
- Extract raw form structures from web pages
- Fill forms with exactly what Claude provides
- Return raw results without interpretation
- Have NO clinical knowledge or mapping logic

Claude provides ALL intelligence:
- Interprets clinical meaning
- Maps health data to calculator inputs
- Makes clinical judgments
- Handles missing data
- Converts units and thresholds
- Counts risk factors
- Synthesizes results

This separation ensures:
1. Tools remain simple and maintainable
2. Clinical logic stays in one place (Claude)
3. System can handle any calculator without tool updates
4. Clear accountability for clinical decisions

### 2. mdcalc_client.py (Playwright Automation)
Adapted from `icloud_client.py` pattern:

```python
class MDCalcClient:
    def __init__(self):
        self.base_url = "https://www.mdcalc.com"
        self.playwright = None
        self.browser = None
        self.context = None
        
    async def initialize(self, headless=True):
        """Initialize Playwright with optimized settings"""
        # Reuse browser initialization from iOS2Android
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
    async def search_calculators(self, query, specialty=None):
        """Search MDCalc using site search or navigation"""
        page = await self.context.new_page()
        
        # Navigate to search or specialty page
        if specialty:
            url = f"{self.base_url}/browse/{specialty}"
        else:
            url = f"{self.base_url}/search?q={query}"
            
        await page.goto(url)
        
        # Extract calculator cards
        calculators = await page.eval_on_selector_all(
            '.calculator-card',  # Adjust selector based on actual HTML
            '''elements => elements.map(el => ({
                title: el.querySelector('.title')?.textContent,
                url: el.querySelector('a')?.href,
                description: el.querySelector('.description')?.textContent,
                specialty: el.querySelector('.specialty-tag')?.textContent
            }))'''
        )
        
        return calculators
        
    async def get_calculator_page(self, calculator_id):
        """Navigate to specific calculator"""
        # Handle both ID and slug formats
        if calculator_id.isdigit():
            url = f"{self.base_url}/calc/{calculator_id}"
        else:
            url = f"{self.base_url}/calc/{calculator_id}"
            
        page = await self.context.new_page()
        await page.goto(url)
        
        # Wait for calculator to load
        await page.wait_for_selector('.calculator-inputs', timeout=10000)
        
        return page
```

### 3. calculator_discovery.py (Search & Catalog)
```python
class CalculatorDiscovery:
    def __init__(self, client):
        self.client = client
        self.catalog_cache = None
        
    async def search_by_condition(self, condition):
        """Find calculators relevant to a medical condition"""
        # Use pre-built mappings when available
        if condition.lower() in CONDITION_MAPPINGS:
            return CONDITION_MAPPINGS[condition.lower()]
            
        # Otherwise search dynamically
        return await self.client.search_calculators(condition)
        
    async def get_calculator_relationships(self, calculator_id):
        """Find related calculators often used together"""
        # E.g., HEART Score → TIMI, GRACE, PERC
        relationships = {
            'heart-score': ['timi-risk-score', 'grace-acs', 'perc-rule'],
            'cha2ds2-vasc': ['has-bled', 'hemorr2hages'],
            'sofa': ['apache-ii', 'news', 'qsofa']
        }
        return relationships.get(calculator_id, [])
```

### 4. calculator_executor.py (Input & Execution)
```python
class CalculatorExecutor:
    def __init__(self, client):
        self.client = client
        
    async def identify_inputs(self, page):
        """Extract all input fields from calculator"""
        inputs = await page.eval_on_selector_all(
            'input, select, [role="radio"], [role="checkbox"]',
            '''elements => elements.map(el => ({
                name: el.name || el.id,
                type: el.type || el.tagName.toLowerCase(),
                label: el.closest('label')?.textContent || 
                       document.querySelector(`label[for="${el.id}"]`)?.textContent,
                required: el.required,
                options: el.tagName === 'SELECT' ? 
                    Array.from(el.options).map(o => ({
                        value: o.value,
                        text: o.textContent
                    })) : null
            }))'''
        )
        return inputs
        
    async def populate_inputs(self, page, values):
        """Fill calculator inputs with provided values"""
        for field_name, value in values.items():
            # Try multiple selector strategies
            selectors = [
                f'input[name="{field_name}"]',
                f'input[id="{field_name}"]', 
                f'select[name="{field_name}"]',
                f'label:has-text("{field_name}") input'
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    
                    # Handle different input types
                    if await element.get_attribute('type') == 'radio':
                        await page.click(f'{selector}[value="{value}"]')
                    elif await element.get_attribute('type') == 'checkbox':
                        if value:
                            await element.check()
                    else:
                        await element.fill(str(value))
                    break
                except:
                    continue
                    
    async def execute_calculation(self, page):
        """Trigger calculation and wait for results"""
        # Find and click calculate button
        calculate_selectors = [
            'button:has-text("Calculate")',
            'input[type="submit"]',
            'button.calculate-btn'
        ]
        
        for selector in calculate_selectors:
            try:
                await page.click(selector)
                break
            except:
                continue
                
        # Wait for results to appear
        await page.wait_for_selector('.result-container', timeout=5000)
```

### 5. result_parser.py (Extract Results)
```python
class ResultParser:
    async def extract_results(self, page):
        """Extract calculation results from page"""
        results = {}
        
        # Primary score/result
        score_element = await page.query_selector('.primary-result, .score')
        if score_element:
            results['score'] = await score_element.text_content()
            
        # Risk category
        risk_element = await page.query_selector('.risk-category, .interpretation')
        if risk_element:
            results['risk_category'] = await risk_element.text_content()
            
        # Detailed interpretation
        interpretation = await page.query_selector('.detailed-interpretation')
        if interpretation:
            results['interpretation'] = await interpretation.text_content()
            
        # Recommendations
        recommendations = await page.eval_on_selector_all(
            '.recommendation-item, .next-steps li',
            'elements => elements.map(el => el.textContent)'
        )
        if recommendations:
            results['recommendations'] = recommendations
            
        # Evidence/References
        evidence = await page.eval_on_selector_all(
            '.evidence-item, .reference',
            'elements => elements.map(el => ({
                text: el.textContent,
                link: el.querySelector("a")?.href
            }))'
        )
        results['evidence'] = evidence
        
        return results
```

## Security & Performance

### Credential Management
Following the iOS2Android pattern:
- No credentials needed for MDCalc (public site)
- Rate limiting to avoid being blocked
- User agent rotation if needed

### Caching Strategy
```python
class CalculatorCache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl
        
    def get(self, key):
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['value']
        return None
        
    def set(self, key, value):
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
```

### Parallel Execution
```python
async def batch_execute_calculators(calculators, max_parallel=3):
    """Execute multiple calculators in parallel tabs"""
    semaphore = asyncio.Semaphore(max_parallel)
    
    async def execute_with_limit(calc_config):
        async with semaphore:
            page = await context.new_page()
            try:
                # Execute calculator
                await navigate_to_calculator(page, calc_config['id'])
                await populate_inputs(page, calc_config['inputs'])
                await execute_calculation(page)
                return await extract_results(page)
            finally:
                await page.close()
                
    tasks = [execute_with_limit(calc) for calc in calculators]
    return await asyncio.gather(*tasks)
```

## Error Handling

### Common Scenarios
1. **Calculator not found**: Return clear error with suggestions
2. **Invalid inputs**: Validate before submission, return specific errors
3. **Page structure changes**: Fallback selectors, graceful degradation
4. **Timeout**: Retry with exponential backoff
5. **Rate limiting**: Implement delays between requests

### Recovery Strategies
```python
async def with_retry(func, max_attempts=3):
    """Retry mechanism with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
```

## Integration with Health Data MCP

### Data Flow
1. Agent receives clinical query
2. Health MCP queries patient data from Snowflake
3. MDCalc MCP identifies relevant calculators
4. Health data mapped to calculator inputs
5. MDCalc MCP executes calculations
6. Results synthesized and returned

### Input Mapping
```python
# Map health data fields to MDCalc inputs
FIELD_MAPPINGS = {
    'age': ['patient_age', 'age_years'],
    'systolic_bp': ['sbp', 'systolic'],
    'heart_rate': ['hr', 'pulse'],
    'creatinine': ['cr', 'creatinine_level'],
    'hemoglobin': ['hgb', 'hb'],
    'platelet_count': ['plt', 'platelets']
}
```

## Testing Strategy

### Unit Tests
- Input identification accuracy
- Result extraction correctness
- Error handling robustness

### Integration Tests
- End-to-end calculator execution
- Parallel execution performance
- Cache effectiveness

### Validation Tests
- Compare automated results with manual calculations
- Verify all 900+ calculators accessible
- Stress test with rapid executions

## Performance Targets
- Single calculator execution: < 3 seconds
- Parallel execution (5 calculators): < 10 seconds
- Cache hit rate: > 80% for common calculators
- Error rate: < 1%
- Availability: 99.9% (handling site changes gracefully)