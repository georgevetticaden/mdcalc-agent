# MDCalc Automation MCP Server

Model Context Protocol (MCP) server that provides Claude with access to all 825 MDCalc medical calculators through visual understanding and browser automation.

## Overview

This MCP server enables Claude to:
- Search and discover medical calculators from a catalog of 825 tools
- Understand calculator requirements through screenshots (visual AI)
- Execute calculators with intelligently mapped patient data
- Extract and interpret results

## Architecture

### Screenshot-Based Universal Calculator Support

Instead of hardcoding selectors for 825 different calculators, this server uses a revolutionary approach:

```
Traditional Approach (Fragile):
- Hardcode selectors for each calculator ❌
- Break when UI changes ❌
- Maintain 825 different configurations ❌

Our Approach (Universal):
- Take screenshot of calculator ✅
- Claude SEES the fields visually ✅
- Claude maps data based on what it sees ✅
- Works for ALL calculators automatically ✅
```

### How It Works

1. **User Request**: "Calculate HEART score for chest pain patient"
2. **Claude calls `mdcalc_get_calculator("1752")`**:
   - Server navigates to calculator
   - Takes screenshot (23KB JPEG)
   - Returns screenshot + metadata
3. **Claude SEES the calculator**:
   - Visually identifies fields: History, Age, ECG, Risk Factors, Troponin
   - Understands options for each field
4. **Claude maps patient data**:
   - Age 68 → sees "≥65" button → maps to that option
   - 3 risk factors → sees "≥3 risk factors" → maps to that option
5. **Claude calls `mdcalc_execute()` with mapped values**
6. **Server clicks buttons and returns results**

## Installation

### Prerequisites

- Python 3.7+
- Playwright
- Chrome/Chromium browser

### Setup

```bash
# Install Python dependencies
pip install playwright asyncio beautifulsoup4

# Install browser
playwright install chromium

# Verify catalog exists
ls src/calculator-catalog/mdcalc_catalog.json
# Should show: 825 calculators
```

## MCP Tools

### 1. `mdcalc_list_all`

Get complete catalog of all 825 calculators organized by specialty.

**Parameters**: None

**Returns**:
```json
{
  "total_count": 825,
  "categories": ["Cardiology", "Pulmonology", ...],
  "calculators_by_category": {
    "Cardiology": [
      {"id": "1752", "name": "HEART Score", "condition": "chest pain"},
      ...
    ]
  }
}
```

### 2. `mdcalc_search`

Search for calculators by condition, symptom, or name.

**Parameters**:
- `query` (string): Search term
- `limit` (integer, optional): Max results (default: 10)

**Returns**:
```json
{
  "count": 5,
  "calculators": [
    {
      "id": "1752",
      "title": "HEART Score",
      "url": "https://www.mdcalc.com/calc/1752/...",
      "description": "Predicts 6-week risk..."
    }
  ]
}
```

### 3. `mdcalc_get_calculator`

Get calculator details with screenshot for visual understanding.

**Parameters**:
- `calculator_id` (string): Calculator ID or slug

**Returns**:
- Image content (JPEG screenshot, ~23KB)
- Text metadata:
```json
{
  "title": "HEART Score",
  "url": "https://www.mdcalc.com/calc/1752/...",
  "fields_detected": 0,  // May be 0 due to React rendering
  "screenshot_included": true
}
```

**Note**: The screenshot is the key - Claude uses vision to understand the calculator structure.

### 4. `mdcalc_execute`

Execute calculator with mapped values.

**Parameters**:
- `calculator_id` (string): Calculator ID
- `inputs` (object): Field values mapped by Claude

**Example Input**:
```json
{
  "calculator_id": "1752",
  "inputs": {
    "history": "Moderately suspicious",
    "age": "≥65",
    "ecg": "Normal",
    "risk_factors": "≥3 risk factors",
    "troponin": "≤1x normal limit"
  }
}
```

**Returns**:
```json
{
  "success": true,
  "score": 5,
  "score_text": "5 points",
  "risk_category": "Moderate",
  "risk_percentage": "12%"
}
```

## Calculator Catalog

The server includes a pre-scraped catalog of all 825 MDCalc calculators:

### Categories (16 total)
- **Cardiology**: 245 calculators
- **Pulmonology**: 67 calculators
- **Emergency Medicine**: 43 calculators
- **Hepatology**: 36 calculators
- **Pediatrics**: 34 calculators
- **Neurology**: 30 calculators
- **Nephrology**: 22 calculators
- **Oncology**: 22 calculators
- And more...

### Updating the Catalog

```bash
# Re-scrape MDCalc for latest calculators
python ../../tools/calculator-scraper/scrape_mdcalc.py

# Verify completeness
python ../../tools/calculator-scraper/verify_catalog.py
```

## Testing

### Test Suite Overview

The test suite verifies all aspects of the MDCalc automation system. Tests should be run in the following order:

| Test File | Purpose | What It Validates |
|-----------|---------|-------------------|
| `test_screenshot.py` | Basic screenshot capability | - Browser automation works<br>- Screenshot capture and encoding<br>- File size optimization (~23KB) |
| `test_calculator_execution.py` | **Main integration test** | - Button clicking (divs styled as buttons)<br>- Numeric input fields<br>- Context-aware selection<br>- Result extraction<br>- Pre-selected value handling |
| `test_mcp_server.py` | MCP protocol compliance | - Server initialization<br>- Tool registration<br>- Request/response format<br>- Claude Desktop compatibility |
| `test_known_calculators.py` | Specific calculator validation | - HEART Score<br>- LDL Calculator<br>- CHA2DS2-VASc Score |
| `test_any_calculator.py` | Universal calculator testing | - Test any calculator by ID<br>- Auto-generate test inputs<br>- Useful for debugging new calculators |

### Recommended Test Order

```bash
# 1. Basic screenshot test (quick smoke test)
python tests/test_screenshot.py

# 2. Main integration test (comprehensive)
python tests/test_calculator_execution.py
# Enter 'n' when prompted to watch the browser

# 3. MCP server protocol test
python tests/test_mcp_server.py

# 4. (Optional) Test specific calculators
python tests/test_known_calculators.py

# 5. (Optional) Test any specific calculator
python tests/test_any_calculator.py
# Follow prompts to enter calculator ID
```

### Test Details

#### 1. `test_screenshot.py` - Screenshot Capability
- **Purpose**: Verify basic browser automation and screenshot capture
- **Duration**: ~10 seconds
- **Key Validation**:
  - Browser launches successfully
  - Screenshots are captured
  - Images are properly encoded as base64
  - File sizes are optimized

#### 2. `test_calculator_execution.py` - Main Integration Test ⭐
- **Purpose**: Comprehensive testing of all calculator types
- **Duration**: ~30 seconds
- **Tests**:
  1. **Catalog Search**: Search for calculators by keyword
  2. **HEART Score**: Button-based calculator with pre-selected values
  3. **LDL Calculator**: Numeric input fields
  4. **CHA2DS2-VASc**: Mixed inputs with context-aware selection
- **Key Lessons Applied**:
  - Uses exact field names from UI (e.g., "History" not "history")
  - Omits pre-selected fields to avoid toggling them off
  - Handles spaces in field names (e.g., "Risk factors")
  - Extracts results from `calc_result` containers

#### 3. `test_mcp_server.py` - MCP Protocol Test
- **Purpose**: Verify MCP server works with Claude Desktop
- **Duration**: ~20 seconds
- **Validates**:
  - JSON-RPC protocol compliance
  - All 4 MCP tools work correctly
  - Screenshot transmission as base64
  - Error handling

#### 4. `test_known_calculators.py` - Known Calculators
- **Purpose**: Test specific high-value calculators
- **Duration**: ~20 seconds
- **Note**: Uses same input patterns as `test_calculator_execution.py`

#### 5. `test_any_calculator.py` - Universal Tester
- **Purpose**: Debug and test any calculator interactively
- **Usage**:
  ```bash
  python tests/test_any_calculator.py
  # Enter calculator ID when prompted (e.g., 1752, 70, 801)
  # Optionally provide custom inputs or use auto-generated ones
  ```

### Important Testing Notes

1. **Field Names Must Be Exact**: Always use exact field names as they appear in the UI
   - ✅ `'History'` (capital H)
   - ❌ `'history'` (lowercase)

2. **Pre-selected Values**: Don't include fields that are already selected by default
   - For HEART Score: Omit "EKG" and "Initial troponin" if already selected

3. **Screenshots Location**: All test screenshots are saved to:
   ```
   tests/screenshots/
   ├── heart_score_test.jpg      # Initial state
   ├── 1752_result.jpg           # After execution
   ├── ldl_calc_test.jpg         # Initial state
   ├── 70_result.jpg             # After execution
   └── ...
   ```

4. **Running Tests Visibly**: Enter `n` when prompted to see the browser during tests

### Troubleshooting Tests

| Issue | Solution |
|-------|----------|
| Button not clicking | Check exact text in screenshot, ensure no extra spaces |
| Pre-selected value toggled off | Don't include that field in inputs |
| Result extraction fails | Check `calc_result` container structure in browser |
| Field not found | Use exact field name with proper capitalization |

## Configuration

### Add to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mdcalc-automation": {
      "command": "python",
      "args": [
        "/full/path/to/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/full/path/to/mdcalc-agent"
      }
    }
  }
}
```

## How Claude Uses This Server

### Example: Chest Pain Assessment

```
User: "68-year-old with chest pain, diabetes, hypertension"

Claude's Process:
1. mdcalc_search("chest pain")
   → Finds HEART Score, TIMI, GRACE

2. mdcalc_get_calculator("1752")
   → Gets HEART Score screenshot
   → SEES fields visually

3. Maps data intelligently:
   - Sees "Age" field with options → Maps 68 to "≥65"
   - Sees "Risk factors" → Counts HTN+DM → Maps to "≥3"

4. mdcalc_execute("1752", mapped_values)
   → Returns score: 5, risk: 12%

5. Synthesizes: "Moderate risk, consider admission"
```

## Troubleshooting

### Screenshot Too Large
- Current: ~23KB (optimized)
- If larger: Adjust quality in `mdcalc_client.py`

### Calculator Not Found
- Check calculator ID in catalog
- Use search to find correct ID

### Fields Not Detected
- This is OK! Claude uses the screenshot
- Field detection returning 0 is expected for React apps

### Execution Failed
- Ensure button text matches exactly
- Check screenshot to verify UI hasn't changed

## Design Philosophy

**"Smart Agent, Dumb Tools"**

This server is intentionally "dumb" - it only:
- Takes screenshots
- Clicks buttons
- Extracts text

All intelligence lives in Claude:
- Visual understanding
- Clinical interpretation
- Data mapping
- Result synthesis

This separation ensures:
- Universal calculator support
- No maintenance of calculator-specific code
- Robust against UI changes
- Leverages Claude's vision capabilities

## License

MIT

## Support

For issues or questions, see the main [README.md](../../README.md) or [CLAUDE.md](../../CLAUDE.md)