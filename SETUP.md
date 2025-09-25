# MDCalc Clinical Companion - Setup Guide

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/gvetticaden/mdcalc-agent.git
cd mdcalc-agent
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure Claude Desktop

Add the MDCalc MCP server to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mdcalc-automation": {
      "command": "python",
      "args": [
        "/absolute/path/to/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/mdcalc-agent"
      }
    }
  }
}
```

Replace `/absolute/path/to/mdcalc-agent` with your actual repository path.

### 4. Test the Setup

```bash
# Test the MCP server directly
python mcp-servers/mdcalc-automation-mcp/tests/test_mcp_server.py

# Test calculator functionality
python tests/test_known_calculators.py --no-headless
```

### 5. Start Using with Claude

1. Restart Claude Desktop after updating the configuration
2. Look for "mdcalc-automation" in Claude's available tools
3. Try: "Search for heart score calculator"

## 📋 Configuration Options

### Environment Variables

- `MDCALC_HEADLESS`: Set to `false` to see browser during execution
- `MDCALC_DEMO_MODE`: Set to `true` for demonstration mode
- `PYTHONPATH`: Must point to the repository root

### Testing Individual Calculators

```bash
# Test specific calculator
python tests/test_known_calculators.py --calc heart

# Available test calculators:
# - heart: HEART Score
# - ldl: LDL Calculator
# - cha2ds2: CHA2DS2-VASc Score
# - sofa: SOFA Score
# - apache: APACHE II Score
# - creatinine: Creatinine Clearance
```

## 🐛 Troubleshooting

### MCP Server Not Appearing in Claude

1. Check configuration file syntax (must be valid JSON)
2. Verify paths are absolute, not relative
3. Restart Claude Desktop completely
4. Check logs: `~/Library/Logs/Claude/` (macOS)

### Browser Automation Issues

```bash
# Install missing dependencies
playwright install-deps

# Test browser launch
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); print('Success!'); b.close(); p.stop()"
```

### Python Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📚 Next Steps

- Review [Agent Instructions](agent/instructions/mdcalc-clinical-companion-agent-instructions-v3.md)
- Try [Demo Scenarios](requirements/mdcalc-demo-scenarios.md)
- Read [Architecture Overview](docs/architecture.md)
- Browse [Calculator Catalog](mcp-servers/mdcalc-automation-mcp/src/mdcalc_catalog.json)

## 💬 Need Help?

- [Open an Issue](https://github.com/gvetticaden/mdcalc-agent/issues)
- Check existing issues for solutions
- Join the discussion in GitHub Discussions