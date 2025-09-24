# Agent Configuration

This directory contains Claude Desktop Agent configuration and knowledge base.

## Structure:

### instructions/
- `mdcalc-clinical-companion-agent-instructions.md` - Main agent instructions with orchestration logic
- `mdcalc-clinical-companion-agent-description.md` - Brief agent description for Claude Desktop
- `mdcalc-execution-guide.md` - Quick reference for MDCalc execution

### knowledge/
- `calculator-catalog.json` - MDCalc calculator metadata
- `calculator-mappings.json` - Natural language to calculator mappings
- `clinical-pathways.json` - Complex decision trees for conditions

### examples/
- `chest-pain-scenario.md` - Emergency chest pain assessment demo
- `afib-scenario.md` - AFib anticoagulation decision demo
- `icu-assessment.md` - ICU multi-organ assessment demo

## Key Concept:
The agent handles ALL orchestration logic. It makes parallel tool calls to the MDCalc MCP server and synthesizes results using its clinical reasoning capabilities.