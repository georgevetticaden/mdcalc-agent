# MDCalc Automation MCP Server

## Universal Medical Calculator Support Through Visual Intelligence

A Model Context Protocol (MCP) server that enables Claude to interact with all 825+ MDCalc medical calculators through revolutionary screenshot-based visual understanding.

## 🎯 The Innovation

This server solves a fundamental challenge in healthcare automation: **How do you integrate with 825+ different medical calculators without writing custom code for each one?**

### Traditional Approach ❌
- Write custom integration for each calculator
- Maintain 825+ different configurations
- Break when calculator UI updates
- Months of development per calculator
- Constant maintenance burden

### Our Approach ✅
- One universal solution for all calculators
- Claude "sees" calculators like clinicians do
- Zero maintenance when calculators update
- Works immediately with new calculators
- 100% coverage from day one

## 🔬 How It Works

### Visual Understanding Pipeline

```mermaid
graph LR
    A[Calculator Request] --> B[Navigate to MDCalc]
    B --> C[Capture Screenshot]
    C --> D[Claude Analyzes Visually]
    D --> E[Map Patient Data]
    E --> F[Execute Calculator]
    F --> G[Extract Results]
```

### Real Example: HEART Score Calculation

1. **Request**: Calculate HEART score for 68-year-old with chest pain
2. **Screenshot**: System captures calculator interface (23KB JPEG)
3. **Visual Analysis**: Claude identifies fields:
   - History (dropdown with options)
   - Age (buttons: <45, 45-64, ≥65)
   - ECG (radio buttons)
   - Risk factors (toggle buttons)
   - Troponin (selection buttons)
4. **Intelligent Mapping**:
   - Age 68 → Claude sees "≥65" button → Maps to that option
   - 3 risk factors → Sees "≥3 risk factors" → Maps to that option
5. **Execution**: Clicks mapped buttons
6. **Results**: Returns score and risk assessment

## 🛠 MCP Tools

### Complete Calculator Catalog
**`mdcalc_list_all`**
- Returns all 825 calculators
- Optimized to ~31K tokens (63% reduction)
- Organized by medical specialty
- Instant access without API calls

### Intelligent Search
**`mdcalc_search`**
- Semantic search understanding
- "chest pain" → finds HEART, TIMI, GRACE
- "afib" → finds CHA2DS2-VASc, HAS-BLED
- Uses MDCalc's AI-powered search

### Visual Calculator Understanding
**`mdcalc_get_calculator`**
- Captures calculator screenshot
- Optimized JPEG (~23KB)
- Enables Claude's visual analysis
- No DOM parsing needed

### Automated Execution
**`mdcalc_execute`**
- Executes calculator with mapped values
- Handles buttons, dropdowns, inputs
- Returns structured results
- Automatic result extraction

## 📊 Coverage & Capabilities

### Medical Specialties Covered (825+ Calculators)

| Specialty | Calculators | Examples |
|-----------|------------|----------|
| **Cardiology** | 245 | HEART Score, TIMI, CHA2DS2-VASc |
| **Critical Care** | 89 | SOFA, APACHE II, qSOFA |
| **Emergency Medicine** | 143 | PERC, Wells, NEXUS |
| **Pulmonology** | 67 | CURB-65, PSI/PORT |
| **Nephrology** | 42 | MDRD GFR, CKD-EPI |
| **Hepatology** | 36 | MELD, Child-Pugh |
| **Neurology** | 30 | NIHSS, ABCD2 |
| **Plus 9 more specialties** | 173+ | Full coverage |

### Key Features

- **Zero Configuration**: Works with any calculator immediately
- **Visual Intelligence**: Understands calculators through screenshots
- **Dynamic Adaptation**: Handles UI changes automatically
- **Optimized Performance**: ~23KB screenshots, fast execution
- **Clinical Accuracy**: Preserves exact calculator logic

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/georgevetticaden/mdcalc-clinical-companion.git
cd mdcalc-agent/mcp-servers/mdcalc-automation-mcp

# Install dependencies
pip install playwright asyncio
playwright install chromium

# Verify catalog
ls src/calculator-catalog/mdcalc_catalog.json
# Should show: mdcalc_catalog.json (825 calculators)
```

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mdcalc-automation": {
      "command": "python",
      "args": [
        "/path/to/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
      ],
      "env": {
        "MDCALC_HEADLESS": "true"
      }
    }
  }
}
```

### Demo Mode

Set `MDCALC_HEADLESS="false"` to watch the browser automation during demonstrations.

## 🧪 Testing Suite

### Comprehensive Test Coverage

```bash
# Visual validation for multiple calculators
cd tests
python test_screenshot.py --headless

# Tests HEART Score, CHA2DS2-VASc, SOFA, APACHE II, and more
# Validates screenshot capture, zoom adjustment, and field visibility
```

### Test Any Calculator

```bash
python tests/test_any_calculator.py
# Enter calculator ID when prompted (e.g., 1752 for HEART Score)
# System will auto-generate test inputs or accept custom values
```

## 💡 Technical Highlights

### Smart Zoom Technology
- Automatically adjusts viewport for long calculators
- Ensures all fields are captured
- Handles sticky overlays intelligently
- Maintains readability while fitting content

### Overlay Management
- Detects and temporarily hides sticky result sections
- Prevents fields from being obscured
- Restores original state after screenshot
- Works with complex React-based UIs

### Optimized Token Usage
- Catalog compressed from 82K to 31K tokens (63% reduction)
- Screenshot compression to ~23KB
- Efficient data structures
- Minimal bandwidth requirements

## 🏗 Architecture

### Design Philosophy: "Smart Agent, Dumb Tools"

The server intentionally provides simple, mechanical operations:
- Navigate to calculators
- Capture screenshots
- Click specified elements
- Extract visible text

All intelligence resides in Claude:
- Visual understanding of interfaces
- Clinical data interpretation
- Smart field mapping
- Result synthesis
- Medical decision support

This separation ensures:
- **Reliability**: Simple tools are robust
- **Flexibility**: Claude adapts to any calculator
- **Maintainability**: No complex logic to debug
- **Scalability**: One approach for unlimited calculators

## 📈 Performance Metrics

- **Coverage**: 100% of 825+ calculators
- **Screenshot Size**: ~23KB average
- **Execution Time**: 2-3 seconds per calculator
- **Token Efficiency**: 63% reduction in catalog size
- **Maintenance**: Zero after initial setup
- **New Calculator Support**: Immediate

## 🔗 Integration Examples

### Clinical Workflow Integration

```python
# Example: Comprehensive cardiac risk assessment
results = {
    "HEART Score": await execute_calculator("1752", patient_data),
    "TIMI Risk": await execute_calculator("1099", patient_data),
    "GRACE ACS": await execute_calculator("1100", patient_data)
}

# Claude synthesizes multiple scores into recommendations
recommendation = synthesize_cardiac_risk(results)
```

### EHR Integration Pattern

```python
# Pull patient data from EHR
patient = ehr.get_patient(patient_id)

# Map to calculator inputs
inputs = map_patient_to_calculator(patient, calculator_id)

# Execute and return to EHR
result = await execute_calculator(calculator_id, inputs)
ehr.add_clinical_note(patient_id, result)
```

## 📚 Documentation

- [Main Project README](../../README.md) - Project overview and vision
- [Implementation Guide](../../CLAUDE.md) - Technical details
- [Agent Instructions](../../agent/instructions/mdcalc-clinical-companion-agent-instructions-v2.md) - Orchestration logic

## 🤝 Contributing

We welcome contributions! Key areas:
- Additional test coverage
- Performance optimizations
- Enhanced result extraction
- Multi-language support

## 📄 License

MIT

## 🙏 Acknowledgments

Built with:
- [MDCalc](https://www.mdcalc.com/) - The essential clinical tool
- [Playwright](https://playwright.dev/) - Browser automation
- [Model Context Protocol](https://modelcontextprotocol.io) - Tool integration
- [Anthropic Claude](https://www.anthropic.com) - Multimodal AI

---

*"By enabling Claude to see and understand medical calculators visually, we've created a universal solution that works with any calculator interface — past, present, or future."*