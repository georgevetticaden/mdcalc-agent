# Agent Configuration

This directory contains Claude Desktop Agent configuration and knowledge base.

## Structure:

### instructions/
- `system-prompt.md` - Main agent instructions with orchestration logic
- `calculator-knowledge.md` - MDCalc calculator reference information
- `clinical-protocols.md` - Clinical decision guidelines

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