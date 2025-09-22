# MDCalc Automation MCP Server

MCP server that provides atomic tools for MDCalc calculator automation via Playwright.

## Core Components:
- `mdcalc_mcp.py` - Main MCP server (provides atomic tools only)
- `mdcalc_client.py` - Playwright automation client
- `calculator_discovery.py` - Calculator search and discovery
- `calculator_executor.py` - Execute calculators with inputs
- `result_parser.py` - Parse calculation results

## Atomic Tools Provided:
1. `search_calculators` - Search MDCalc for relevant calculators
2. `get_calculator_details` - Get input requirements for a calculator
3. `execute_calculator` - Run a single calculator with provided inputs

## Note:
This MCP server provides ONLY atomic operations. Claude handles all orchestration, parallel execution, and synthesis of results.