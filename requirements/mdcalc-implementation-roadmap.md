# MDCalc Clinical Companion - Implementation Roadmap

## Executive Summary
A phased implementation plan to build and demonstrate the MDCalc Clinical Companion, leveraging existing infrastructure and proven patterns from previous successful projects. No fixed timeline - progress through phases based on completion and validation.

## Phase 0: Recording & Discovery
**Goal**: Use Playwright recordings to understand MDCalc's structure

### Deliverables
- Recording infrastructure setup
- Recorded interactions for key calculators
- Extracted selectors and patterns
- Element identification strategy

### Tasks
1. Set up recording tools
2. Record MDCalc interactions:
   - Homepage navigation
   - Search functionality
   - HEART Score execution
   - CHA2DS2-VASc execution
   - Result extraction
3. Parse recordings for selectors
4. Document page patterns

### Success Criteria
- [ ] 5+ calculator recordings created
- [ ] Selectors extracted and validated
- [ ] Page structure documented
- [ ] Recording playback working

## Phase 1: Foundation & Infrastructure
**Goal**: Establish core development environment and basic automation

### Deliverables
- Development environment ready
- Health MCP integration verified
- Basic MDCalc automation working
- Single calculator execution

### Tasks
```bash
# Environment setup
cd /Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent

# Install dependencies
pip install playwright asyncio snowflake-connector-python beautifulsoup4
npm install @modelcontextprotocol/server-nodejs

# Verify health MCP connection
python scripts/validate-health-data.sh
```

### Key Components
- `mdcalc_client.py` - Basic Playwright client
- `mdcalc_mcp.py` - MCP server skeleton
- Test connection to health-analysis-server
- Verify Snowflake data access

### Success Criteria
- [ ] Environment configured
- [ ] Health data queries working
- [ ] Basic MDCalc navigation functional
- [ ] One calculator executing successfully

## Phase 2: Core Automation Development
**Goal**: Build robust calculator interaction capabilities

### Deliverables
- Search functionality complete
- Calculator detail extraction
- Input population working
- Result parsing accurate

### Priority Calculators
1. HEART Score (most used)
2. CHA2DS2-VASc (AFib essential)
3. SOFA (ICU critical)
4. PERC Rule (ED common)
5. Creatinine Clearance (medication dosing)

### Key Functions
```python
# Core capabilities to implement
- search_calculators(query, limit)
- get_calculator_details(calculator_id)
- populate_inputs(page, values)
- extract_results(page)
```

### Success Criteria
- [ ] 5 calculators fully automated
- [ ] Input mapping working
- [ ] Result extraction accurate
- [ ] MCP tools accessible in Claude

## Phase 3: Agent Enhancement & Orchestration
**Goal**: Enable Claude to orchestrate complex assessments

### Deliverables
- Enhanced agent instructions
- Clinical pathway definitions
- Parallel execution via Claude
- Synthesis patterns working

### Agent Capabilities
- Clinical pathway knowledge embedded
- Parallel tool call patterns
- Result synthesis algorithms
- Confidence scoring logic

### Clinical Pathways to Define
```python
PATHWAYS = {
    'chest_pain': ['heart-score', 'timi-risk', 'grace', 'perc'],
    'afib': ['cha2ds2-vasc', 'has-bled', 'atria'],
    'sepsis': ['sofa', 'apache-ii', 'news'],
    'aki': ['kdigo', 'rifle', 'akin']
}
```

### Success Criteria
- [ ] Agent makes parallel tool calls
- [ ] Synthesis produces unified assessments
- [ ] Confidence scores calibrated
- [ ] Clinical pathways working

## Phase 4: Demo Preparation & Polish
**Goal**: Create compelling demonstration for stakeholders

### Deliverables
- 4 polished demo scenarios
- Expected outputs documented
- Fallback plans ready
- Presentation materials complete

### Demo Scenarios
1. Emergency chest pain (3 min)
2. AFib anticoagulation (3 min)
3. ICU deterioration (2.5 min)
4. Medication safety (1.5 min)

### Polish Tasks
- Response formatting
- Error handling
- Performance optimization
- Demo recording as backup

### Success Criteria
- [ ] All demos execute flawlessly
- [ ] Response time < 10 seconds
- [ ] Synthesis quality high
- [ ] Backup plans tested

## Technical Implementation Details

### MCP Server Configuration
Add to claude_desktop_config.json:
```json
"mdcalc-automation": {
  "command": "python",
  "args": [
    "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
  ],
  "env": {
    "PYTHONPATH": "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent"
  }
}
```

### Key Code Patterns

#### Recording-Based Development
```python
# First: Record interactions
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.mdcalc.com")
    page.pause()  # Interactive recording
```

#### Parallel Execution (Claude handles this)
```python
# Claude makes multiple tool calls like:
results = await asyncio.gather(
    execute_calculator("heart-score", inputs1),
    execute_calculator("timi-risk", inputs2),
    execute_calculator("grace", inputs3)
)
```

#### Synthesis in Agent Instructions
```markdown
When you receive multiple calculator results:
1. Extract risk levels from each
2. Identify agreement/conflicts  
3. Weight by evidence quality
4. Generate unified recommendation
5. Calculate confidence score
```

## Success Metrics

### Technical Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Calculator Accuracy | 100% | Compare with manual |
| Response Time (single) | <3 sec | Time tool execution |
| Response Time (multi) | <10 sec | Time full assessment |
| Uptime | 99.9% | Monitor failures |

### Clinical Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Correct Calculator Selection | >95% | Review selections |
| Complete Assessment Coverage | >90% | Check pathways |
| Appropriate Recommendations | 100% | Clinical review |

### Demo Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Scenario Completion | 4/4 | Execute all demos |
| Time per Demo | <3 min | Time recordings |
| Synthesis Quality | High | Review outputs |

## Risk Mitigation

### Technical Risks
- **MDCalc blocks automation**: Use rate limiting, rotating user agents
- **Selector changes**: Use multiple fallback selectors from recordings
- **Performance issues**: Cache common calculators, limit parallel calls

### Demo Risks
- **Live failure**: Pre-record all scenarios
- **Slow response**: Show recording if needed
- **Data issues**: Have test data ready

## Go/No-Go Checkpoints

### After Phase 0
- [ ] Recordings capture all needed interactions
- [ ] Selectors are reliable
- **Decision**: Proceed if selectors work

### After Phase 1
- [ ] Basic automation proven
- [ ] Health data accessible
- **Decision**: Proceed if foundation solid

### After Phase 2
- [ ] Core calculators working
- [ ] MCP integration stable
- **Decision**: Proceed if automation reliable

### After Phase 3
- [ ] Orchestration functioning
- [ ] Synthesis valuable
- **Decision**: Proceed if quality high

## Key File Locations

### Configuration Files
```
/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/
├── CLAUDE.md (this file)
├── requirements/*.md (reference docs)
├── recordings/*.json (selector data)
└── mcp-servers/mdcalc-automation-mcp/src/*.py
```

### External Dependencies
```
Health MCP: /Users/aju/Dropbox/Development/Git/multi-agent-health-insight-system-using-claude-code/tools/health-mcp
```

## Next Immediate Steps

1. **Start Phase 0**: Create recording script
2. **Record interactions**: Capture MDCalc behavior
3. **Extract selectors**: Parse recordings
4. **Begin Phase 1**: Build basic automation

## Remember
- **No fixed timeline** - progress based on completion
- **Recording-first** - understand before automating
- **Claude orchestrates** - MCP tools stay atomic
- **Leverage existing** - health MCP already works
- **Demo focus** - everything builds toward demo

The goal is demonstrating transformative potential, not perfection. Focus on showing how conversational AI revolutionizes medical calculator usage.

**Validation Queries**:
```sql
-- Test essential data availability
SELECT COUNT(*) FROM vitals WHERE date > DATEADD(day, -30, CURRENT_DATE());
SELECT COUNT(*) FROM lab_results WHERE test_name IN ('Creatinine', 'Hemoglobin', 'Platelet Count');
SELECT COUNT(*) FROM medications WHERE status = 'Active';
```

## Week 2: Core Automation Development

### Day 6-7: Playwright MDCalc Client
**Owner**: George (with Claude Code assistance)  
**Deliverables**:
- `mdcalc_client.py` functional
- Search capability working
- Calculator details extraction complete

**Key Functions to Implement**:
- `search_calculators(query, limit)`
- `get_calculator_details(calculator_id)`
- `extract_input_fields(page)`

### Day 8-9: Calculator Execution
**Owner**: George  
**Deliverables**:
- Single calculator execution working
- Input population functioning
- Result extraction validated

**Test Calculators Priority**:
1. HEART Score (most used)
2. CHA2DS2-VASc (AFib essential)
3. SOFA (ICU critical)
4. PERC Rule (ED common)
5. Creatinine Clearance (medication dosing)

### Day 10: MCP Server Integration
**Owner**: George  
**Deliverables**:
- MDCalc MCP server running
- Tools exposed to Claude Desktop
- Basic testing complete

**Integration Checklist**:
- [ ] MCP server starts without errors
- [ ] Tools visible in Claude Desktop
- [ ] Health MCP and MDCalc MCP communicate
- [ ] Error handling for common failures

## Week 3: Advanced Orchestration

### Day 11-12: Clinical Pathways
**Owner**: George  
**Deliverables**:
- Clinical pathway mappings defined
- Calculator relationships documented
- Orchestrator logic implemented

**Key Pathways**:
```python
PATHWAYS = {
    'chest_pain': ['heart-score', 'timi-risk', 'grace', 'perc'],
    'afib': ['cha2ds2-vasc', 'has-bled', 'atria'],
    'sepsis': ['sofa', 'apache-ii', 'news'],
    'aki': ['kdigo', 'rifle', 'akin']
}
```

### Day 13-14: Parallel Execution
**Owner**: George  
**Deliverables**:
- Concurrent calculator execution
- Performance optimization
- Resource management

**Performance Targets**:
- Single calculator: <3 seconds
- 5 parallel calculators: <10 seconds
- Memory usage: <500MB
- CPU usage: <50%

### Day 15: Result Synthesis
**Owner**: George  
**Deliverables**:
- Synthesis algorithm complete
- Confidence scoring implemented
- Conflict resolution logic

**Synthesis Components**:
- Risk level aggregation
- Agreement calculation
- Recommendation generation
- Evidence quality assessment

## Week 4: Demo Preparation & Polish

### Day 16-17: Agent Instructions & Knowledge
**Owner**: George  
**Deliverables**:
- Comprehensive agent instructions
- Calculator knowledge base
- Clinical protocols documented

**Documentation Priorities**:
- System prompt optimization
- Calculator selection logic
- Safety guidelines
- Response formatting

### Day 18-19: Demo Scenarios
**Owner**: George  
**Deliverables**:
- 4 demo scenarios polished
- Edge cases handled
- Backup plans ready

**Demo Testing Checklist**:
- [ ] Chest pain assessment (3 min)
- [ ] AFib anticoagulation (3 min)
- [ ] ICU deterioration (2.5 min)
- [ ] Medication safety (1.5 min)

### Day 20: Final Integration & Testing
**Owner**: George  
**Deliverables**:
- End-to-end testing complete
- Performance validated
- Demo recording created

**Final Validation**:
- 10 complete run-throughs
- Response time measurements
- Accuracy verification
- Failure recovery tested

## Success Metrics & KPIs

### Technical Metrics
| Metric | Target | Current | Status |
|--------|--------|---------|---------|
| Calculator Accuracy | 100% | - | Pending |
| Response Time (single) | <3 sec | - | Pending |
| Response Time (multi) | <10 sec | - | Pending |
| Uptime | 99.9% | - | Pending |
| Error Rate | <1% | - | Pending |

### Clinical Metrics
| Metric | Target | Current | Status |
|--------|--------|---------|---------|
| Correct Calculator Selection | >95% | - | Pending |
| Complete Assessment Coverage | >90% | - | Pending |
| Appropriate Recommendations | 100% | - | Pending |
| Confidence Calibration | ±10% | - | Pending |

### Business Metrics
| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Time Savings | 5-10 min/case | Demo timing |
| Calculator Utilization | 4x increase | Count in demo |
| User Satisfaction | >4.5/5 | Post-demo survey |
| Implementation Feasibility | High | Technical review |

## Risk Mitigation

### Technical Risks

**Risk**: MDCalc blocks automation  
**Mitigation**: 
- Implement rate limiting
- Use rotating user agents
- Have manual fallback ready
- Contact MDCalc for API discussion

**Risk**: Playwright instability  
**Mitigation**:
- Implement retry logic
- Use multiple selector strategies
- Have timeout handling
- Create fallback paths

**Risk**: Data mapping failures  
**Mitigation**:
- Build comprehensive field mappings
- Handle missing data gracefully
- Provide manual input option
- Clear error messaging

### Demo Risks

**Risk**: Live demo failure  
**Mitigation**:
- Pre-record all scenarios
- Have static slides ready
- Practice offline explanation
- Test 1 hour before demo

**Risk**: Performance issues  
**Mitigation**:
- Pre-cache common calculators
- Limit parallel execution
- Have faster machine ready
- Show recording if needed

## Resource Requirements

### Technical Resources
- **Development Machine**: 16GB RAM, 8-core CPU
- **Snowflake Account**: Existing health data warehouse
- **Claude Desktop**: Latest version with MCP support
- **MDCalc Access**: Public website access

### Time Investment
- **Week 1**: 30 hours (environment + foundation)
- **Week 2**: 40 hours (core development)
- **Week 3**: 35 hours (orchestration + testing)
- **Week 4**: 25 hours (demo prep + practice)
- **Total**: 130 hours

### Cost Estimates
- **Development Time**: 130 hours × $200/hr = $26,000
- **Infrastructure**: $0 (using existing)
- **Tools/Licenses**: $0 (open source)
- **Total Investment**: $26,000

### ROI Projection
- **Time Saved**: 7 min/case average
- **Cases/Day**: 100 (across MDCalc users)
- **Daily Savings**: 700 minutes = 11.7 hours
- **Annual Value**: 11.7 × 250 × $200 = $585,000
- **ROI**: 22x in Year 1

## Go/No-Go Decision Points

### End of Week 1 Checkpoint
**Decision Criteria**:
- [ ] MDCalc automation proven feasible
- [ ] Health data integration working
- [ ] No blocking technical issues

**Go Decision**: Proceed to Week 2
**No-Go**: Pivot to API negotiation with MDCalc

### End of Week 2 Checkpoint
**Decision Criteria**:
- [ ] 5+ calculators executing successfully
- [ ] Performance meets targets
- [ ] MCP integration stable

**Go Decision**: Proceed to Week 3
**No-Go**: Focus on perfecting fewer calculators

### End of Week 3 Checkpoint
**Decision Criteria**:
- [ ] Orchestration working
- [ ] Synthesis producing value
- [ ] Demo scenarios functional

**Go Decision**: Proceed to demo prep
**No-Go**: Simplify demo scope

## Post-Demo Next Steps

### Immediate (Days 1-7 post-demo)
1. Incorporate Joe & Matt's feedback
2. Address technical questions
3. Provide implementation proposal
4. Share demo recording

### Short-term (Weeks 2-4 post-demo)
1. Build POC with 20 calculators
2. Recruit 5 beta physicians
3. Create evaluation framework
4. Document API requirements

### Medium-term (Months 2-3)
1. Expand to 100 calculators
2. Integrate with one EHR
3. Build analytics dashboard
4. Conduct clinical validation

### Long-term (Months 4-6)
1. Full calculator catalog
2. Production deployment
3. Multi-site rollout
4. Continuous improvement

## Communication Plan

### Weekly Updates to MDCalc
- Monday: Week plan and priorities
- Wednesday: Progress update
- Friday: Demo of week's work

### Stakeholder Communications
- **Joe (CEO)**: Business value focus
- **Matt (CTO)**: Technical architecture
- **Clinicians**: Safety and workflow
- **Engineers**: Integration points

## Definition of Success

### Minimum Viable Success
- 3 working demo scenarios
- Clear value proposition demonstrated
- Technical feasibility proven
- Path to production defined

### Target Success
- All 4 demos flawless
- 10+ calculators integrated
- Performance exceeds targets
- Strong stakeholder buy-in

### Exceptional Success
- Live patient data demo
- 20+ calculators working
- EHR integration prototype
- Immediate funding approval

## Appendix: Key Code Snippets

### Critical Function: Parallel Calculator Execution
```python
async def execute_parallel_calculators(calculator_configs):
    """Execute multiple calculators simultaneously"""
    tasks = []
    for config in calculator_configs:
        task = asyncio.create_task(
            execute_single_calculator(
                calculator_id=config['id'],
                inputs=config['inputs']
            )
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return process_results(results)
```

### Critical Function: Clinical Synthesis
```python
def synthesize_clinical_assessment(results):
    """Synthesize multiple calculator results"""
    risk_scores = extract_risk_levels(results)
    agreement = calculate_agreement(risk_scores)
    confidence = determine_confidence(agreement, data_quality)
    
    return {
        'overall_risk': aggregate_risk(risk_scores),
        'confidence': confidence,
        'recommendations': generate_recommendations(risk_scores),
        'evidence_quality': assess_evidence(results)
    }
```

## Final Notes

This implementation leverages:
1. **Proven patterns** from iOS2Android Playwright automation
2. **Existing infrastructure** from multi-agent health system
3. **Rapid development** via Claude Code and 3-Amigo pattern
4. **Clinical expertise** from healthcare background

The key to success is not perfection but demonstration of transformative potential. Focus on the "wow" moments that show how conversational AI can revolutionize medical calculator usage.

**Remember**: We're not replacing MDCalc—we're making it 10x more powerful.