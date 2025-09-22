# MDCalc Conversational AI Agent

A conversational AI agent that transforms MDCalc's 900+ medical calculators into an intelligent clinical decision support system using Claude Desktop, MCP servers, and Playwright automation.

## Overview

This system demonstrates how conversational AI can transform MDCalc from a **pull-based** system (physicians search for calculators) to a **push-based** intelligent system (AI suggests relevant calculators based on patient context).

## Key Features

- 🏥 **Natural Language Interface**: Describe clinical scenarios conversationally
- 🔄 **Parallel Execution**: Run multiple calculators simultaneously
- 🧠 **Intelligent Orchestration**: Claude synthesizes results into unified assessments
- 📊 **Health Data Integration**: Automatically pulls data from Snowflake/Apple Health
- ⚡ **Rapid Assessment**: Complete multi-calculator analysis in <10 seconds

## Architecture

```
User Query → Claude Desktop Agent (Orchestration)
                    ↓
         ┌──────────────────────────────┐
         │     Parallel Tool Calls      │
         ├──────────────┬───────────────┤
         ↓              ↓
   Health Data MCP   MDCalc Automation MCP
         │              │
   Snowflake DB    MDCalc.com
         └──────────────┴───────────────┘
                    ↓
          Claude Synthesizes Results
                    ↓
           Unified Clinical Response
```

## Directory Structure

```
mdcalc-agent/
├── agent/              # Claude agent configuration
├── recordings/         # Playwright recordings for selectors
├── mcp-servers/        # MCP server implementations
├── tools/              # Supporting utilities
├── evaluation/         # Testing framework
├── docs/              # Documentation
└── scripts/           # Automation scripts
```

## Quick Start

1. **Environment Setup**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   npm install
   ```

2. **Configure MCP Servers**
   Add to your Claude Desktop config

3. **Run Demo**
   ```bash
   ./scripts/run-demo.sh
   ```

## Implementation Phases

- **Phase 0**: Recording-based discovery
- **Phase 1**: Foundation setup
- **Phase 2**: Core automation
- **Phase 3**: Agent orchestration
- **Phase 4**: Demo preparation

## Related Documentation

See `requirements/` directory for detailed specifications:
- Core requirements
- Agent instructions
- MCP design
- Demo scenarios
- Implementation roadmap

## Status

🚧 **In Development** - Building recording infrastructure and core automation

## Contact

For questions or contributions, refer to CLAUDE.md for implementation details.