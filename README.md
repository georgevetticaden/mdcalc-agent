# MDCalc Clinical Companion

An intelligent clinical decision support system that enables natural language interaction with MDCalc's 825+ medical calculators through Claude Desktop and visual understanding.

## Overview

This system transforms MDCalc from a **pull-based** system (physicians manually search and fill calculators) to an **intelligent push-based** system where Claude:
- Suggests relevant calculators based on clinical context
- Automatically maps patient data to calculator inputs
- Executes multiple calculators in parallel
- Synthesizes results into actionable clinical insights

## Key Features

- 🏥 **Natural Language Interface**: Describe clinical scenarios conversationally
- 👁️ **Visual Calculator Understanding**: Screenshots enable universal calculator support
- 🔄 **Smart Data Gathering**: Intelligently asks for missing critical information
- 🧠 **Intelligent Orchestration**: Claude handles all clinical interpretation
- 📊 **Optimized Catalog**: ~31K tokens (63% smaller) for all 825 calculators
- 🔍 **Semantic Search**: MDCalc's sophisticated search, not keyword matching
- ⚡ **Complete Coverage**: All 825 MDCalc calculators supported
- 💬 **Physician-Friendly Input**: Accept flexible response formats (Y/N, natural language)

## Architecture

### Screenshot-Based Universal Calculator Support

The system uses a revolutionary screenshot-based approach that enables support for ALL 825+ MDCalc calculators without any calculator-specific code:

1. **Visual Understanding**: Claude receives a screenshot of each calculator (JPEG, ~23KB)
2. **Field Recognition**: Claude SEEs all input fields, buttons, and options visually
3. **Intelligent Mapping**: Claude maps patient data to the exact button text shown
4. **Mechanical Execution**: The tool simply clicks buttons with matching text

**Key Innovation**: The screenshot is the bridge between MDCalc's complex UI and Claude's intelligence. Even when Playwright can't detect React fields programmatically, Claude can SEE them in the screenshot and tell the tool exactly what to click.

### Intelligent Data Gathering

When critical clinical data is missing, the system intelligently gathers it through physician-friendly interactions:

```
User: "68yo male with chest pain, HTN, diabetes..."

Claude: "To complete risk assessment, I need:
         1. Pain radiates to arm/jaw?
         2. Worse with breathing?
         3. Diaphoresis?

         Quick entry: 'N,N,Y' or describe"

User: "no radiation, not pleuritic, sweating++"

Claude: [Executes calculators with complete data]
```

**Benefits**:
- **No failed calculations** - Always has required data before executing
- **Time-efficient** - Batch all questions in one interaction
- **Flexible input** - Accept Y/N, comma-separated, or natural language
- **Clinical intelligence** - Only asks what changes management

### Workflow Architecture

```
User: "Calculate cardiac risk for my chest pain patient"
                    ↓
         Claude Desktop Agent
                    ↓
    ┌──────────────────────────────┐
    │  1. Search relevant calcs    │
    │  2. Get screenshots (seq.)   │
    │  3. Identify missing data    │
    └──────────────────────────────┘
                    ↓
         "Need: radiation? pleuritic?
          Quick reply: Y/N"
                    ↓
          User: "N,N"
                    ↓
    ┌──────────────────────────────┐
    │  4. Map data to buttons      │
    │  5. Execute calculators      │
    │  6. Extract results          │
    └──────────────────────────────┘
                    ↓
          Claude Synthesizes
                    ↓
        "HEART Score: 5 (12% risk)
         TIMI: 2 points (8% risk)
         Recommend: Admission..."
```

### Design Principle: "Smart Agent, Dumb Tools"

- **Claude (Agent)**: ALL intelligence, interpretation, clinical reasoning, data gathering
- **MCP Tools**: Purely mechanical - screenshot, click, extract
- **No hardcoded logic**: Works with any calculator through vision
- **No assumptions**: Always asks for missing critical data

## Project Structure

```
mdcalc-agent/
├── mcp-servers/
│   └── mdcalc-automation-mcp/    # MCP server implementation
│       ├── src/
│       │   ├── mdcalc_client.py  # Playwright automation
│       │   ├── mdcalc_mcp.py     # MCP protocol server
│       │   └── calculator-catalog/
│       │       └── mdcalc_catalog.json  # 825 calculators
│       └── tests/                # Test suite
├── tools/
│   └── calculator-scraper/       # Catalog maintenance tools
├── docs/                          # Architecture documentation
└── requirements/                  # Project specifications
```

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### 2. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mdcalc-automation": {
      "command": "/path/to/mdcalc-agent/venv/bin/python",
      "args": [
        "/path/to/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/mdcalc-agent",
        "MDCALC_HEADLESS": "true"
      }
    }
  }
}
```

**Environment Variables**:
- `MDCALC_HEADLESS`: Set to `"false"` to see browser during demos
- `PYTHONPATH`: Path to mdcalc-agent root

### 3. Test the System

```bash
cd mcp-servers/mdcalc-automation-mcp/tests

# Test catalog optimization (no browser)
python test_catalog_improvements.py

# Test calculator execution (browser required)
python test_calculator_execution.py

# Test MCP protocol
python test_mcp_server.py
```

## MCP Tools Available

The MDCalc MCP server provides 4 tools to Claude:

1. **mdcalc_list_all**: Get optimized catalog (~31K tokens) with ID, name, category
2. **mdcalc_search**: Use MDCalc's semantic web search for relevant calculators
3. **mdcalc_get_calculator**: Get screenshot for visual understanding (required before execute)
4. **mdcalc_execute**: Execute with exact field names from screenshot (no normalization)

See [mcp-servers/mdcalc-automation-mcp/README.md](mcp-servers/mdcalc-automation-mcp/README.md) for detailed API documentation.

## Example Usage

### Basic Interaction
```
User: "I have a 68-year-old patient with chest pain, hypertension, and diabetes.
       Latest troponin is 0.02. What's their cardiac risk?"

Claude: "I'll assess cardiac risk. First, I need a few clinical details:
         1. Pain radiates to arm/jaw?
         2. Worse with breathing?
         3. Reproducible by palpation?
         4. Known CAD >50%?

         Quick reply: Y/N for each"

User: "N,N,N,N"

Claude's Process:
1. Calls mdcalc_search("chest pain") → finds HEART Score, TIMI, EDACS
2. Calls mdcalc_get_calculator for each (sequentially)
3. SEES the calculator fields visually in screenshots
4. Maps patient data to exact button text:
   - Age 68 → "≥65" button
   - HTN + DM → "≥3 risk factors" button
   - Troponin 0.02 → "≤1x normal" button
5. Calls mdcalc_execute with complete data
6. Synthesizes: "HEART Score: 5 (12% risk), TIMI: 2 (8% risk)
                  Moderate risk - recommend admission and cardiology consult."
```

### Flexible Response Formats
The system accepts various input formats for physician convenience:
- **Comma-separated**: "Y,N,N,Y,N"
- **Natural language**: "no radiation, not pleuritic"
- **Batch negative**: "all no" or "none of the above"
- **Partial**: "only #3 is yes, rest no"

## Key Improvements (Latest)

### 1. Search Enhancement
- Removed rudimentary local catalog search
- Now uses MDCalc's sophisticated web search
- Better semantic matching ("chest pain" finds HEART, TIMI automatically)

### 2. Catalog Optimization
- Reduced from ~82K to ~31K tokens (63% reduction)
- Removed redundant fields (URL, slug, description)
- Kept essential: ID, name, category

### 3. Exact Field Matching
- No field name normalization
- Must match UI exactly ("History" not "history")
- Spaces not underscores ("Risk factors" not "risk_factors")
- Only pass fields that need changing from defaults

### 4. Intelligent Data Gathering (NEW)
- Automatically identifies missing critical data
- Batches all questions into single interaction
- Accepts flexible response formats
- Only asks what changes clinical management

### 5. Headless Mode Control
- Set `MDCALC_HEADLESS="false"` for demos
- Default `"true"` for production

## Implementation Status

✅ **Complete**:
- 825 calculators catalogued across 16 specialties
- Screenshot-based universal calculator support
- Optimized catalog format (63% smaller)
- Semantic search integration
- MCP server with 4 production-ready tools
- Exact field matching system
- Comprehensive test suite
- Claude Desktop configuration

## Development

### Update Calculator Catalog

```bash
# Scrape latest calculators from MDCalc
python tools/calculator-scraper/scrape_mdcalc.py

# Verify extraction completeness
python tools/calculator-scraper/verify_catalog.py
```

### Run Tests

```bash
# All tests
python mcp-servers/mdcalc-automation-mcp/tests/test_mcp_server.py
python mcp-servers/mdcalc-automation-mcp/tests/test_known_calculators.py
python mcp-servers/mdcalc-automation-mcp/tests/test_screenshot.py
```

## License

MIT

## Contributing

Contributions welcome! Please ensure all tests pass before submitting PRs.

## Support

For implementation details, see [CLAUDE.md](CLAUDE.md)