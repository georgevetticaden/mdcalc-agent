# MDCalc Conversational AI Agent - Project Structure

## Directory Structure
```
mdcalc-agent/
├── README.md                           # Project overview and setup instructions
├── CLAUDE.md                          # Comprehensive guide for Claude Code
├── .env.example                       # Environment variables template
├── .gitignore
├── package.json                       # Node.js dependencies
├── requirements.txt                   # Python dependencies
│
├── agent/                             # Claude Desktop Agent Configuration
│   ├── instructions/
│   │   ├── system-prompt.md          # Main agent instructions with orchestration logic
│   │   ├── calculator-knowledge.md   # MDCalc calculator reference
│   │   └── clinical-protocols.md     # Clinical decision guidelines
│   │
│   ├── knowledge/                    # Agent knowledge base
│   │   ├── calculator-catalog.json   # Scraped MDCalc calculator metadata
│   │   ├── calculator-mappings.json  # NLP to calculator mappings
│   │   └── clinical-pathways.json    # Complex decision trees
│   │
│   └── examples/                     # Demo scenarios
│       ├── chest-pain-scenario.md
│       ├── afib-scenario.md
│       └── icu-assessment.md
│
├── recordings/                        # Playwright recordings for element discovery
│   ├── mdcalc-search.json           # Recording of search functionality
│   ├── heart-score-execution.json   # Recording of HEART score calculator
│   ├── cha2ds2-vasc-execution.json  # Recording of CHA2DS2-VASc calculator
│   └── README.md                     # Instructions for creating recordings
│
├── mcp-servers/                       # MCP Server Infrastructure
│   └── mdcalc-automation-mcp/       # Simplified MDCalc automation (no orchestration)
│       ├── src/
│       │   ├── mdcalc_mcp.py       # Main MCP server
│       │   ├── mdcalc_client.py    # Playwright automation client
│       │   ├── calculator_discovery.py # Calculator search and discovery
│       │   ├── calculator_executor.py  # Execute calculators with inputs
│       │   └── result_parser.py    # Parse calculation results
│       ├── package.json
│       └── README.md
│
├── tools/                            # Supporting tools and utilities
│   ├── calculator-scraper/          # Scrape MDCalc catalog
│   │   ├── scraper.py
│   │   └── calculator_metadata.py
│   │
│   ├── recording-generator/         # Generate Playwright recordings
│   │   ├── record_interaction.py
│   │   └── parse_recording.py
│   │
│   ├── test-data-generator/         # Generate test scenarios
│   │   ├── generate_test_data.py
│   │   └── test_scenarios.json
│   │
│   └── demo-dashboard/              # React dashboard for demos (optional)
│       ├── src/
│       │   ├── App.jsx
│       │   ├── CalculatorResults.jsx
│       │   └── HealthMetrics.jsx
│       └── package.json
│
├── evaluation/                       # Testing and evaluation framework
│   ├── test-cases/
│   │   ├── calculator-accuracy/    # Validate calculation accuracy
│   │   ├── data-extraction/        # Test health data queries
│   │   └── orchestration/          # Multi-calc scenarios
│   │
│   └── benchmarks/
│       ├── performance_metrics.py
│       └── clinical_accuracy.py
│
├── docs/                            # Documentation
│   ├── architecture.md             # System architecture
│   ├── mcp-integration.md         # MCP server details
│   ├── clinical-validation.md     # Clinical accuracy validation
│   └── demo-guide.md              # Demo presentation guide
│
└── scripts/                        # Automation scripts
    ├── setup.sh                    # Environment setup
    ├── start-mcp-servers.sh       # Launch all MCP servers
    ├── run-demo.sh                # Demo execution script
    └── validate-health-data.sh    # Verify Snowflake connection

```

## Component Mapping to Existing Work

### Existing Infrastructure We'll Reference

1. **Health Data MCP Server** (external reference)
   - Location: `/Users/aju/Dropbox/Development/Git/multi-agent-health-insight-system-using-claude-code/tools/health-mcp`
   - No need to copy - will reference directly in claude_desktop_config.json
   - Already configured with Snowflake credentials

### Components We Can Adapt

1. **Playwright Automation Pattern** (from iOS2Android migration)
   - Use recording-first approach for element discovery
   - Adapt authentication flow handling patterns
   - Modify page navigation for MDCalc structure
   - Keep credential security pattern (though MDCalc is public)

2. **MCP Server Structure** (from mobile-mcp fork)
   - Use same server initialization pattern
   - Adapt natural language command processing
   - Maintain tool registration approach

### New Components to Build

1. **MDCalc Automation MCP** (Simplified - no orchestration)
   - Calculator discovery (search by condition, specialty)
   - Input field identification and population
   - Result extraction and parsing
   - Single calculator execution only (Claude handles parallel)

2. **Recording-Based Discovery**
   - Create recordings of MDCalc interactions
   - Parse recordings to identify selectors
   - Build robust element identification

3. **Calculator Knowledge Base**
   - Scraper for MDCalc catalog
   - Relationship mappings between calculators
   - Clinical context rules (embedded in agent instructions)

## Development Phases

### Phase 0: Recording & Discovery
- Set up recording infrastructure
- Record key MDCalc interactions
- Parse recordings for element selectors
- Document page structure patterns

### Phase 1: Foundation
- Set up project structure
- Configure health-data-mcp reference
- Create basic mdcalc-automation-mcp
- Test single calculator execution

### Phase 2: Core Automation
- Implement calculator discovery
- Build input population logic
- Create result extraction
- Test with 5 common calculators

### Phase 3: Agent Enhancement
- Enhance agent instructions with orchestration logic
- Define clinical pathways in instructions
- Test parallel execution via Claude
- Implement synthesis patterns

### Phase 4: Demo Polish
- Build demo scenarios
- Create visualization (optional)
- Practice presentation flow
- Final testing and validation

## Key Files for Claude Code

### Priority 1 - Core Infrastructure
1. `CLAUDE.md` - Comprehensive context and guide
2. `recordings/*.json` - Element selectors from recordings
3. `mdcalc_client.py` - Playwright automation
4. `mdcalc_mcp.py` - MCP server

### Priority 2 - Agent Configuration
1. `agent/instructions/system-prompt.md` - Orchestration logic
2. `agent/knowledge/clinical-pathways.json` - Calculator relationships
3. `calculator_discovery.py` - Smart selection

### Priority 3 - Demo Enhancement
1. `demo-guide.md` - Presentation script
2. Test scenarios and validation
3. Optional dashboard for visualization