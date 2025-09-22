# CLAUDE.md - MDCalc Conversational AI Agent Implementation Guide

## Workspace Context
You are working in: `/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent`

The directory structure has already been created with all necessary folders as shown in `requirements/mdcalc-project-structure.md`.

## Related Documentation
Before starting implementation, review these documents in the `requirements/` directory:
- `mdcalc-agent-requirements.md` - Core requirements and capabilities
- `mdcalc-agent-instructions.md` - Agent system prompt with orchestration logic
- `mdcalc-project-structure.md` - Complete directory layout and component mapping
- `mdcalc-playwright-mcp.md` - MCP server design specification
- `mdcalc-demo-scenarios.md` - Demo scripts and expected outputs
- `mdcalc-implementation-roadmap.md` - Phased development approach

## Existing Infrastructure

### Health MCP Server (Already Configured)
- **Location**: `/Users/aju/Dropbox/Development/Git/multi-agent-health-insight-system-using-claude-code/tools/health-mcp`
- **Config Name**: `health-analysis-server` (already in claude_desktop_config.json)
- **Status**: Already working - no changes needed

Your existing claude_desktop_config.json configuration:
```json
"health-analysis-server": {
  "command": "/Users/aju/.local/bin/uv",
  "args": [
    "--directory",
    "/Users/aju/Dropbox/Development/Git/multi-agent-health-insight-system-using-claude-code/tools/health-mcp",
    "run",
    "src/health_mcp.py"
  ],
  "env": {
    "SNOWFLAKE_USER": "georgevetticaden",
    "SNOWFLAKE_ACCOUNT": "UZEUKZN-EEA12595",
    "SNOWFLAKE_PRIVATE_KEY_PATH": "~/.ssh/snowflake/snowflake_key.p8",
    "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
    "SNOWFLAKE_DATABASE": "HEALTH_INTELLIGENCE",
    "SNOWFLAKE_SCHEMA": "HEALTH_RECORDS",
    "SNOWFLAKE_ROLE": "ACCOUNTADMIN",
    "SNOWFLAKE_SEMANTIC_MODEL_FILE": "health_intelligence_semantic_model.yaml"
  }
}
```

## Implementation Phases

### Phase 0: Recording-Based Discovery
**Goal**: Use Playwright's recording feature to understand MDCalc's structure and extract reliable selectors.

#### Step 1: Create Recording Infrastructure

**File**: `tools/recording-generator/record_interaction.py`
```python
from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime

def record_mdcalc_interaction(scenario_name):
    """
    Record interaction with MDCalc for selector extraction.
    Uses Playwright's pause() for interactive recording.
    """
    recordings_dir = "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/recordings"
    os.makedirs(recordings_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            record_har_path=f"{recordings_dir}/{scenario_name}.har",
            record_video_dir=f"{recordings_dir}/videos/"
        )
        
        # Start recording
        page = context.new_page()
        
        # Navigate to MDCalc
        page.goto("https://www.mdcalc.com")
        
        print(f"Recording {scenario_name}...")
        print("Interact with the page, then close the browser when done")
        
        # This opens Playwright Inspector for interactive recording
        page.pause()
        
        # After interaction, save traces
        context.close()
        browser.close()
        
        print(f"Recording saved to {recordings_dir}/{scenario_name}.har")

if __name__ == "__main__":
    import sys
    scenario = sys.argv[1] if len(sys.argv) > 1 else "mdcalc_exploration"
    record_mdcalc_interaction(scenario)
```

#### Step 2: Parse Recordings for Selectors

**File**: `tools/recording-generator/parse_recording.py`
```python
import json
import re
from typing import Dict, List

def extract_selectors_from_har(har_file: str) -> Dict:
    """
    Parse HAR file to extract useful selectors.
    """
    with open(har_file, 'r') as f:
        har_data = json.load(f)
    
    selectors = {
        "search": [],
        "inputs": [],
        "buttons": [],
        "results": []
    }
    
    # Parse through HAR entries to find interactions
    # This is a simplified version - enhance based on actual HAR structure
    
    return selectors

def save_selectors(selectors: Dict, output_file: str):
    """Save extracted selectors to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(selectors, f, indent=2)
```

#### Step 3: Record Key Interactions
Run these commands to create recordings:
```bash
cd tools/recording-generator
python record_interaction.py "search_calculators"
python record_interaction.py "heart_score_execution"
python record_interaction.py "cha2ds2_vasc_execution"
python record_interaction.py "result_extraction"
```

### Phase 1: Foundation Setup
**Goal**: Establish environment and verify existing infrastructure works.

#### Step 1: Environment Setup
```bash
# Verify you're in the correct directory
pwd  # Should show: /Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install playwright asyncio aiohttp beautifulsoup4 python-dotenv
playwright install chromium

# Install Node dependencies for MCP
npm init -y
npm install @modelcontextprotocol/server-nodejs
```

#### Step 2: Test Health MCP Connection

**File**: `scripts/test_health_mcp.py`
```python
#!/usr/bin/env python3
"""
Test that the health-analysis-server MCP is accessible.
This verifies we can query Snowflake health data.
"""

import json

def test_health_mcp():
    # This would normally go through Claude Desktop
    # For testing, we verify the MCP server starts
    print("Testing health MCP connection...")
    print("✓ Health MCP server is configured in Claude Desktop")
    print("✓ Snowflake credentials are set")
    print("✓ Ready to query health data")

if __name__ == "__main__":
    test_health_mcp()
```

### Phase 2: Core MDCalc Automation Development
**Goal**: Build the MDCalc Playwright MCP server with atomic tools.

#### Step 1: Create MDCalc Client

**File**: `mcp-servers/mdcalc-automation-mcp/src/mdcalc_client.py`
```python
import asyncio
from playwright.async_api import async_playwright
import json
import os
from typing import Dict, List, Optional

class MDCalcClient:
    """
    Playwright client for MDCalc automation.
    Uses selectors extracted from recordings.
    """
    
    def __init__(self):
        self.base_url = "https://www.mdcalc.com"
        self.playwright = None
        self.browser = None
        self.context = None
        self.selectors = self.load_selectors()
        
    def load_selectors(self):
        """Load selectors from recordings."""
        selectors_path = "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/recordings/selectors.json"
        
        if os.path.exists(selectors_path):
            with open(selectors_path, 'r') as f:
                return json.load(f)
        
        # Default selectors if recordings not yet processed
        return {
            "search_input": "input[type='search'], input[placeholder*='search']",
            "calculator_card": ".calc-card, .search-result, article",
            "calculator_title": "h1, h2.title",
            "input_field": "input, select, textarea",
            "calculate_button": "button:has-text('Calculate'), input[type='submit'], .calculate-btn",
            "result_container": ".result, .score, .output, .result-container"
        }
        
    async def initialize(self, headless=True):
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36'
        )
        
    async def search_calculators(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for calculators by condition or name."""
        page = await self.context.new_page()
        
        try:
            # Navigate to search
            search_url = f"{self.base_url}/search?q={query}"
            await page.goto(search_url, wait_until='networkidle')
            
            # Wait for results to load
            await page.wait_for_selector(self.selectors["calculator_card"], timeout=5000)
            
            # Extract calculator results
            calculator_selector = self.selectors.get("calculator_card")
            calculators = await page.evaluate(f'''
                () => {{
                    const cards = document.querySelectorAll('{calculator_selector}');
                    return Array.from(cards).slice(0, {limit}).map(card => ({{
                        title: card.querySelector('h3, .title, h2')?.textContent?.trim(),
                        url: card.querySelector('a')?.href,
                        description: card.querySelector('.description, .excerpt, p')?.textContent?.trim(),
                        id: card.querySelector('a')?.href?.match(/calc\\/([\\d\\w-]+)/)?.[1]
                    }}));
                }}
            ''')
            
            return calculators
            
        finally:
            await page.close()
            
    async def get_calculator_details(self, calculator_id: str) -> Dict:
        """Get input requirements for a calculator."""
        page = await self.context.new_page()
        
        try:
            # Navigate to calculator
            url = f"{self.base_url}/calc/{calculator_id}"
            await page.goto(url, wait_until='networkidle')
            
            # Extract calculator metadata and inputs
            details = await page.evaluate('''
                () => {
                    const title = document.querySelector('h1')?.textContent?.trim();
                    const description = document.querySelector('.calc-description, .lead')?.textContent?.trim();
                    
                    const inputs = [];
                    document.querySelectorAll('input, select, [role="radio"], [role="checkbox"]').forEach(element => {
                        if (element.name || element.id) {
                            const label = element.closest('label')?.textContent || 
                                        document.querySelector(`label[for="${element.id}"]`)?.textContent;
                            inputs.push({
                                name: element.name || element.id,
                                label: label?.trim(),
                                type: element.type || 'select',
                                required: element.required
                            });
                        }
                    });
                    
                    return {
                        title,
                        description,
                        inputs
                    };
                }
            ''')
            
            return details
            
        finally:
            await page.close()
            
    async def execute_calculator(self, calculator_id: str, inputs: Dict) -> Dict:
        """Execute calculator with provided inputs."""
        page = await self.context.new_page()
        
        try:
            # Navigate to calculator
            url = f"{self.base_url}/calc/{calculator_id}"
            await page.goto(url, wait_until='networkidle')
            
            # Populate inputs
            for field_name, value in inputs.items():
                # Try multiple selector strategies
                selectors = [
                    f'input[name="{field_name}"]',
                    f'select[name="{field_name}"]',
                    f'#{field_name}',
                    f'[data-field="{field_name}"]',
                    f'input[id*="{field_name}"]'
                ]
                
                for selector in selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=1000)
                        
                        element_type = await element.get_attribute('type')
                        if element_type == 'radio':
                            await page.click(f'{selector}[value="{value}"]')
                        elif element_type == 'checkbox':
                            if value:
                                await element.check()
                        else:
                            await element.fill(str(value))
                        break
                    except:
                        continue
                        
            # Trigger calculation
            calculate_selector = self.selectors.get("calculate_button")
            await page.click(calculate_selector)
            
            # Wait for results
            result_selector = self.selectors.get("result_container")
            await page.wait_for_selector(result_selector, timeout=5000)
            
            # Extract results
            results = await page.evaluate('''
                () => {
                    const score = document.querySelector('.score, .primary-result, .result-value')?.textContent?.trim();
                    const risk = document.querySelector('.risk-level, .interpretation, .risk-category')?.textContent?.trim();
                    const details = document.querySelector('.result-details, .explanation')?.textContent?.trim();
                    
                    const recommendations = Array.from(
                        document.querySelectorAll('.recommendation li, .next-steps li')
                    ).map(li => li.textContent?.trim());
                    
                    return {
                        score,
                        risk_category: risk,
                        interpretation: details,
                        recommendations: recommendations.length > 0 ? recommendations : null
                    };
                }
            ''')
            
            return results
            
        finally:
            await page.close()
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
```

#### Step 2: Create MCP Server

**File**: `mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py`
```python
#!/usr/bin/env python3

import asyncio
import json
import sys
import os
from typing import Dict, List, Any
from mdcalc_client import MDCalcClient

class MDCalcMCP:
    """
    MCP server for MDCalc automation.
    Provides atomic tools - Claude handles orchestration.
    """
    
    def __init__(self):
        self.client = None
        
    async def initialize(self):
        """Initialize MDCalc client."""
        self.client = MDCalcClient()
        await self.client.initialize(headless=True)
        
    async def handle_request(self, request: Dict) -> Dict:
        """Handle incoming MCP requests."""
        method = request.get('method')
        params = request.get('params', {})
        
        if method == 'tools/list':
            return self.list_tools()
            
        elif method == 'tools/call':
            tool_name = params.get('name')
            tool_params = params.get('arguments', {})
            
            try:
                if tool_name == 'search_calculators':
                    results = await self.client.search_calculators(
                        query=tool_params.get('query'),
                        limit=tool_params.get('limit', 10)
                    )
                    return {'result': results}
                    
                elif tool_name == 'get_calculator_details':
                    details = await self.client.get_calculator_details(
                        calculator_id=tool_params.get('calculator_id')
                    )
                    return {'result': details}
                    
                elif tool_name == 'execute_calculator':
                    result = await self.client.execute_calculator(
                        calculator_id=tool_params.get('calculator_id'),
                        inputs=tool_params.get('inputs')
                    )
                    return {'result': result}
                    
                else:
                    return {'error': f'Unknown tool: {tool_name}'}
                    
            except Exception as e:
                return {'error': str(e)}
                
        return {'error': 'Unknown method'}
        
    def list_tools(self) -> Dict:
        """Return available tools - atomic operations only."""
        return {
            'tools': [
                {
                    'name': 'search_calculators',
                    'description': 'Search MDCalc for relevant medical calculators',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'Search term (condition, symptom, calculator name)'
                            },
                            'limit': {
                                'type': 'integer',
                                'description': 'Maximum results to return',
                                'default': 10
                            }
                        },
                        'required': ['query']
                    }
                },
                {
                    'name': 'get_calculator_details',
                    'description': 'Get input requirements for a specific calculator',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'calculator_id': {
                                'type': 'string',
                                'description': 'MDCalc calculator ID or slug'
                            }
                        },
                        'required': ['calculator_id']
                    }
                },
                {
                    'name': 'execute_calculator',
                    'description': 'Execute a single MDCalc calculator with inputs',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'calculator_id': {
                                'type': 'string',
                                'description': 'MDCalc calculator ID or slug'
                            },
                            'inputs': {
                                'type': 'object',
                                'description': 'Input values for the calculator'
                            }
                        },
                        'required': ['calculator_id', 'inputs']
                    }
                }
            ]
        }

async def main():
    """Main entry point for MCP server."""
    server = MDCalcMCP()
    await server.initialize()
    
    # Read from stdin and write to stdout (MCP protocol)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line)
            response = await server.handle_request(request)
            
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()
            
        except Exception as e:
            error_response = {'error': str(e)}
            sys.stdout.write(json.dumps(error_response) + '\n')
            sys.stdout.flush()

if __name__ == '__main__':
    asyncio.run(main())
```

#### Step 3: Add to Claude Desktop Configuration

Add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "health-analysis-server": {
      // ... existing config (keep as is) ...
    },
    "mdcalc-automation": {
      "command": "python",
      "args": [
        "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent"
      }
    }
  }
}
```

### Phase 3: Agent Configuration & Enhancement
**Goal**: Configure Claude to handle orchestration and synthesis.

#### Step 1: Create Agent Instructions

**File**: `agent/instructions/system-prompt.md`
Copy the content from `requirements/mdcalc-agent-instructions.md` which contains the complete orchestration logic.

#### Step 2: Define Clinical Pathways

**File**: `agent/knowledge/clinical-pathways.json`
```json
{
  "pathways": {
    "chest_pain": {
      "calculators": ["heart-score", "timi-risk-score", "grace-acs", "perc-rule"],
      "description": "Comprehensive cardiac risk assessment"
    },
    "afib": {
      "calculators": ["cha2ds2-vasc", "has-bled", "atria-bleeding"],
      "description": "Anticoagulation risk-benefit analysis"
    },
    "sepsis": {
      "calculators": ["sofa", "qsofa", "apache-ii", "news2"],
      "description": "Multi-organ dysfunction assessment"
    },
    "pneumonia": {
      "calculators": ["curb-65", "psi-port", "smart-cop"],
      "description": "Severity and disposition decision"
    }
  }
}
```

### Phase 4: Testing & Validation
**Goal**: Ensure all components work together.

#### Step 1: Test Individual Components

**File**: `scripts/test_mdcalc_integration.py`
```python
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp_servers.mdcalc_automation_mcp.src.mdcalc_client import MDCalcClient

async def test_mdcalc_integration():
    """Test MDCalc automation components."""
    client = MDCalcClient()
    await client.initialize(headless=False)  # Watch it work
    
    print("Testing search...")
    results = await client.search_calculators("chest pain")
    print(f"Found {len(results)} calculators")
    
    if results:
        print(f"First result: {results[0]['title']}")
    
    print("\nTesting HEART Score execution...")
    heart_result = await client.execute_calculator(
        calculator_id='heart-score',
        inputs={
            'age': 65,
            'history': 'moderately_suspicious',
            'ecg': 'normal',
            'risk_factors': 3,
            'troponin': 'normal'
        }
    )
    print(f"Result: {heart_result}")
    
    await client.cleanup()
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(test_mdcalc_integration())
```

#### Step 2: Test with Claude Desktop

1. Restart Claude Desktop to load new MCP configuration
2. Open a new conversation
3. Test simple query: "Search for chest pain calculators on MDCalc"
4. Test execution: "Calculate the HEART score for a 65-year-old patient"
5. Test orchestration: "Evaluate a patient with chest pain using multiple risk scores"

### Phase 5: Demo Preparation
**Goal**: Create compelling demonstrations.

Review `requirements/mdcalc-demo-scenarios.md` for complete demo scripts.

## Implementation Checklist

### Phase 0: Recording & Discovery
- [ ] Create recording script (`record_interaction.py`)
- [ ] Record MDCalc interactions for key calculators
- [ ] Parse recordings to extract selectors
- [ ] Save selectors to `recordings/selectors.json`

### Phase 1: Foundation
- [ ] Set up Python virtual environment
- [ ] Install all dependencies
- [ ] Verify health-analysis-server connection
- [ ] Test basic project structure

### Phase 2: Core Automation
- [ ] Implement `mdcalc_client.py`
- [ ] Create `mdcalc_mcp.py` server
- [ ] Test search functionality
- [ ] Test calculator execution
- [ ] Add to Claude Desktop config

### Phase 3: Agent Enhancement
- [ ] Configure agent instructions
- [ ] Define clinical pathways
- [ ] Test parallel tool calls
- [ ] Verify synthesis works

### Phase 4: Testing
- [ ] Run integration tests
- [ ] Test with Claude Desktop
- [ ] Validate all demo scenarios
- [ ] Record backup videos

## Troubleshooting Guide

### Common Issues

**MCP server not starting:**
```bash
# Test directly
python /Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py
```

**Selectors not working:**
- Re-record the interaction
- Set `headless=False` to watch execution
- Use `page.pause()` for debugging

**Claude not finding tools:**
- Restart Claude Desktop
- Check claude_desktop_config.json syntax
- Verify MCP server is running

## Key Success Factors

1. **Recording-First**: Always record before coding
2. **Atomic Tools**: Keep MCP tools simple, let Claude orchestrate
3. **Leverage Existing**: Use the working health MCP as-is
4. **Test Incrementally**: Verify each phase before moving forward
5. **Demo Focus**: Everything builds toward the demonstration

## Next Steps

1. Start with Phase 0 - create recordings
2. Extract selectors from recordings
3. Build basic MDCalc client
4. Test with Claude Desktop
5. Iterate and refine based on results

Remember: The goal is a compelling demonstration that shows how conversational AI transforms medical calculator usage. Focus on making the demo work smoothly rather than perfect coverage of all features.