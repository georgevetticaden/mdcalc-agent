# MDCalc Playwright MCP Server - Design Specification

## Overview
This MCP server provides programmatic access to MDCalc.com through Playwright browser automation, transforming the web interface into an API-like service that the Claude agent can use to discover, execute, and interpret medical calculators. The server provides atomic tools - Claude handles orchestration.

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

### 1. mdcalc_mcp.py (Main Server - Simplified)

```python
# Simplified MCP server - no orchestration
class MDCalcMCP:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.calculator_cache = {}
        self.selectors = self.load_selectors_from_recordings()
        
    def load_selectors_from_recordings(self):
        """Load element selectors from recorded interactions"""
        selectors = {}
        recordings_path = "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/recordings"
        
        for recording_file in os.listdir(recordings_path):
            if recording_file.endswith('.json'):
                with open(os.path.join(recordings_path, recording_file)) as f:
                    recording_data = json.load(f)
                    selectors.update(self.extract_selectors(recording_data))
        
        return selectors
        
    # Tool definitions - ATOMIC operations only
    tools = [
        {
            "name": "search_calculators",
            "description": "Search MDCalc for relevant calculators",
            "parameters": {
                "query": "Search term (condition, symptom, or calculator name)",
                "limit": "Max results to return (default 10)"
            }
        },
        {
            "name": "get_calculator_details", 
            "description": "Get inputs and evidence for a specific calculator",
            "parameters": {
                "calculator_id": "MDCalc calculator ID or URL slug"
            }
        },
        {
            "name": "execute_calculator",
            "description": "Run a single calculator with provided inputs",
            "parameters": {
                "calculator_id": "Calculator to execute",
                "inputs": "Dictionary of input values"
            }
        }
        # Note: No batch_execute - Claude handles parallel calls
    ]
```

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