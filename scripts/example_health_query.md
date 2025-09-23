# Example Health Data Queries

Once the health-analysis-server is running in Claude Desktop, you can query health data with natural language:

## Example Queries:

### Get Latest Vitals
"What are my latest vital signs including blood pressure, heart rate, and temperature?"

### Get Lab Results
"Show me my most recent lab results including CBC, metabolic panel, and lipids"

### Get Medications
"List all my current medications with dosages"

### Get Specific Values for Calculators
"Get the data needed for HEART score: age, cardiac risk factors, troponin levels"

### Temporal Queries
"Show my blood pressure trend over the last 30 days"
"What was my creatinine level 3 months ago?"

## Integration with MDCalc

The agent will automatically:
1. Query health data when you describe a patient scenario
2. Map the data to calculator inputs
3. Execute the calculations
4. Synthesize results

Example conversation:
"I need to assess my cardiac risk"
→ Agent queries your age, BP, cholesterol, diabetes status
→ Runs HEART score, TIMI, Framingham
→ Provides unified risk assessment
