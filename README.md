# MDCalc Conversational AI Agent

A Claude-powered medical calculator automation system that enables natural language interaction with MDCalc's 825+ medical calculators through visual understanding and intelligent data mapping.

## Overview

This system transforms MDCalc from a **pull-based** system (physicians manually search and fill calculators) to an **intelligent push-based** system where Claude:
- Suggests relevant calculators based on clinical context
- Automatically maps patient data to calculator inputs
- Executes multiple calculators in parallel
- Synthesizes results into actionable clinical insights

## Key Features

- 🏥 **Natural Language Interface**: Describe clinical scenarios conversationally
- 👁️ **Visual Calculator Understanding**: Screenshots enable universal calculator support
- 🔄 **Parallel Execution**: Run multiple calculators simultaneously
- 🧠 **Intelligent Orchestration**: Claude handles all clinical interpretation
- 📊 **Health Data Integration**: Pulls from Snowflake/EHR systems automatically
- ⚡ **Complete Coverage**: All 825 MDCalc calculators supported

## Architecture

### Screenshot-Based Universal Calculator Support

```
User: "Calculate cardiac risk for my chest pain patient"
                    ↓
         Claude Desktop Agent
                    ↓
    ┌──────────────────────────────┐
    │     Parallel MCP Tools       │
    ├──────────────┬───────────────┤
    ↓              ↓
Health Data    MDCalc Automation
    │              │
    │         1. Get Screenshot
    │         2. Claude SEES fields
    │         3. Maps patient data
    │         4. Executes calculator
    └──────────────┴───────────────┘
                    ↓
          Claude Synthesizes Results
                    ↓
        "HEART Score: 5 (12% risk)
         Consider admission..."
```

### Design Principle: "Smart Agent, Dumb Tools"

- **Claude (Agent)**: ALL intelligence, interpretation, clinical reasoning
- **MCP Tools**: Purely mechanical - screenshot, click, extract
- **No hardcoded logic**: Works with any calculator through vision

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
      "command": "python",
      "args": [
        "/path/to/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
      ]
    }
  }
}
```

### 3. Test the System

```bash
# Test MCP server and tools
python mcp-servers/mdcalc-automation-mcp/tests/test_mcp_server.py

# Test calculator execution
python mcp-servers/mdcalc-automation-mcp/tests/test_known_calculators.py
```

## MCP Tools Available

The MDCalc MCP server provides 4 tools to Claude:

1. **mdcalc_list_all**: Get all 825 calculators organized by specialty
2. **mdcalc_search**: Search calculators by condition or name
3. **mdcalc_get_calculator**: Get calculator with screenshot for visual understanding
4. **mdcalc_execute**: Execute calculator with mapped values

See [mcp-servers/mdcalc-automation-mcp/README.md](mcp-servers/mdcalc-automation-mcp/README.md) for detailed API documentation.

## Example Usage

```
User: "I have a 68-year-old patient with chest pain, hypertension, and diabetes.
       Latest troponin is 0.02. What's their cardiac risk?"

Claude's Process:
1. Calls mdcalc_search("chest pain") → finds HEART Score, TIMI, GRACE
2. Calls mdcalc_get_calculator("1752") → gets HEART Score with screenshot
3. SEES the calculator fields visually
4. Maps patient data:
   - Age 68 → "≥65" button
   - HTN + DM → "≥3 risk factors" button
   - Troponin 0.02 → "≤1x normal" button
5. Calls mdcalc_execute with mapped values
6. Returns: "HEART Score is 5 (12% risk). Consider admission and cardiology consultation."
```

## Implementation Status

✅ **Complete**:
- 825 calculators catalogued across 16 specialties
- Screenshot-based universal calculator support
- MCP server with 4 production-ready tools
- Intelligent category assignment
- Comprehensive test suite

🚧 **In Progress**:
- Claude Desktop integration
- Multi-calculator synthesis examples
- Clinical pathway templates

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