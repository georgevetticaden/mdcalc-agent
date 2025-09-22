# MDCalc Conversational AI Agent - Requirements Document

## Executive Summary
Build a conversational AI agent that demonstrates how Claude can transform MDCalc's 900+ medical calculators into an intelligent, natural language clinical decision support system. The agent will access the user's Apple Health data through existing Snowflake infrastructure and use Playwright automation to interact with MDCalc's web interface, enabling physicians to ask natural language questions and receive comprehensive clinical assessments.

## Core Value Proposition
Transform MDCalc from a **pull-based** system (physician searches for calculators) to a **push-based** intelligent system (AI suggests relevant calculators based on patient context) while maintaining clinical accuracy and physician trust.

## Key Capabilities

### 1. Natural Language Understanding
- **Input**: "Evaluate this 58-year-old diabetic patient with chest pain and shortness of breath"
- **Process**: 
  - Extract clinical parameters (age, conditions, symptoms)
  - Query user's health data from Snowflake
  - Identify relevant calculators from MDCalc's catalog
  - Orchestrate multiple calculations through parallel tool calls

### 2. Intelligent Calculator Selection
- Analyze patient context to identify relevant calculators
- Understand relationships between calculators (e.g., HEART Score + TIMI + PERC for chest pain)
- Prioritize based on clinical urgency and guideline recommendations
- Handle complex decision trees where one calculator's output determines which others to run

### 3. Automated Data Population
- Query Snowflake health database for required inputs
- Map health data fields to calculator inputs
- Handle unit conversions and data normalization
- Flag missing data and request from user when necessary

### 4. Agent-Based Orchestration
- **Claude Agent handles all orchestration natively**:
  - Makes parallel tool calls to execute multiple calculators
  - Synthesizes results using LLM reasoning capabilities
  - Identifies conflicts or contradictions between outputs
  - Presents unified risk assessment with confidence scores
- **No separate orchestration MCP needed** - Claude's native capabilities handle synthesis

### 5. Clinical Context Awareness
- Consider department context (Emergency, ICU, Outpatient)
- Factor in available resources and time constraints
- Adapt recommendations based on local protocols
- Provide evidence-based rationale for each recommendation

## Technical Architecture

### Simplified Agent Architecture
```
User Query → Claude Desktop Agent (Orchestration & Reasoning)
                        ↓
         ┌──────────────────────────────┐
         │     Parallel Tool Calls      │
         ├──────────────┬───────────────┤
         ↓              ↓               
   Health Data MCP   MDCalc Playwright MCP
         │              │               
   Snowflake DB    MDCalc.com          
         │              │               
         └──────────────┴───────────────┘
                        ↓
            Claude synthesizes all results
                        ↓
              Unified Clinical Response
```

### Key Architecture Decisions
- **Orchestration by Claude**: The agent uses its native reasoning to coordinate tools
- **Atomic MCP Tools**: Each MCP server provides simple, single-purpose tools
- **Parallel Execution**: Claude makes multiple simultaneous tool calls
- **Synthesis in Context**: Result interpretation happens in Claude's context window

### Performance Requirements
- Response time: < 3 seconds for single calculator
- Multi-calculator orchestration: < 10 seconds for complex cases
- Accuracy: 100% match with manual calculator execution
- Availability: Offline fallback for cached calculators

### Safety Requirements
- Never make autonomous clinical decisions
- Always show confidence scores and limitations
- Maintain audit trail of all calculations
- Flag when calculator prerequisites aren't met
- Require physician confirmation for critical decisions

## User Stories

### Story 1: Emergency Chest Pain Assessment
**As an** emergency physician  
**I want to** quickly assess a chest pain patient  
**So that** I can make rapid triage decisions  

**Acceptance Criteria:**
- Identifies and runs HEART, TIMI, PERC scores simultaneously
- Pulls relevant vitals, labs, and history from health data
- Provides risk stratification in under 10 seconds
- Highlights which pathway (rule out, admit, discharge) is indicated

### Story 2: Medication Dosing Verification
**As a** hospitalist  
**I want to** verify anticoagulation dosing for AFib  
**So that** I can prevent adverse events  

**Acceptance Criteria:**
- Calculates CHA2DS2-VASc and HAS-BLED scores
- Checks creatinine clearance for dosing adjustment
- Flags drug interactions from medication list
- Provides specific dosing recommendations with evidence

### Story 3: Complex Multi-System Assessment
**As an** ICU physician  
**I want to** assess multiple organ systems simultaneously  
**So that** I can prioritize interventions  

**Acceptance Criteria:**
- Runs SOFA, APACHE II, and relevant organ-specific scores
- Tracks trends over time from historical data
- Identifies deteriorating systems requiring immediate attention
- Provides prognostic information for family discussions

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Set up development environment
- Integrate existing health MCP server
- Create basic MDCalc Playwright automation
- Implement calculator discovery mechanism

### Phase 2: Core Features (Week 2)
- Build natural language to calculator mapping
- Implement automated data extraction and population
- Create single calculator execution flow
- Add basic result interpretation

### Phase 3: Advanced Orchestration (Week 3)
- Implement multi-calculator parallel execution
- Add conflict resolution and synthesis
- Build confidence scoring system
- Create clinical context awareness

### Phase 4: Demo Preparation (Week 4)
- Polish conversational interface
- Create compelling demo scenarios
- Add visualization and reporting
- Conduct thorough testing

## Success Metrics
- **Technical**: 95% accuracy in calculator selection, < 5 second average response
- **Clinical**: Identifies all relevant calculators for given scenario
- **User Experience**: Natural conversation flow without technical jargon
- **Business**: Clear path to 10x physician engagement

## Risk Mitigation
- **Calculator accuracy**: Extensive validation against manual calculations
- **Data quality**: Graceful handling of missing or inconsistent data
- **Performance**: Caching and parallel execution strategies
- **Trust building**: Complete transparency in calculation process

## Demo Scenarios for Joe and Matt

### Scenario 1: "The Overwhelmed Emergency Physician"
Show how a busy ER doctor can say "65-year-old with AFib and chest pain" and get comprehensive risk assessment across cardiac, stroke, and bleeding domains in seconds.

### Scenario 2: "The Complex ICU Case"
Demonstrate orchestrating 8+ calculators for multi-organ failure, showing how the agent prioritizes and synthesizes overwhelming amounts of data into actionable insights.

### Scenario 3: "The Medication Safety Check"
Illustrate how the agent can prevent medication errors by automatically running relevant drug dosing calculators based on patient's renal function and drug interactions.

## Next Steps
1. Review and approve requirements
2. Set up development environment with Claude Desktop
3. Configure MCP servers for health data and web automation
4. Begin Phase 1 implementation
5. Weekly demos to track progress