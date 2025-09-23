# Screenshot-Based Universal Calculator Architecture

## How It Works

### 1. User Request
```
User: "Calculate HEART score for my 68-year-old patient with chest pain"
```

### 2. Claude Gets Calculator Details (with Screenshot)

**Tool Call**: `get_calculator_details("1752")`

**Tool Returns**:
```json
{
  "title": "HEART Score",
  "url": "https://mdcalc.com/calc/1752/...",
  "screenshot_base64": "iVBORw0KGgoAAAANS...",  // 50KB JPEG
  "fields": []  // Empty is OK - Claude will see them visually
}
```

### 3. Claude's Visual Understanding

Claude SEES this in the screenshot:
```
┌─────────────────────────────────────┐
│ HEART Score Calculator              │
│                                     │
│ History                             │
│ ○ Slightly suspicious               │
│ ○ Moderately suspicious             │
│ ○ Highly suspicious                 │
│                                     │
│ Age                                 │
│ ○ <45                               │
│ ○ 45-64                             │
│ ○ ≥65                               │
│                                     │
│ ECG                                 │
│ ○ Normal                            │
│ ○ Non-specific repolarization      │
│ ○ Significant ST deviation         │
│                                     │
│ Risk factors                        │
│ ○ No known risk factors            │
│ ○ 1-2 risk factors                 │
│ ○ ≥3 risk factors                  │
│                                     │
│ Troponin                            │
│ ○ ≤1x normal limit                  │
│ ○ 1-2x normal limit                 │
│ ○ >2x normal limit                  │
└─────────────────────────────────────┘
```

### 4. Claude Queries Health Data

**Tool Call**: `query_health_data(patient_id)`

**Returns**:
```json
{
  "age": 68,
  "diagnoses": ["Hypertension", "Diabetes", "Hyperlipidemia"],
  "labs": {"troponin": 0.02},
  "symptoms": "chest pain, moderately concerning"
}
```

### 5. Claude's Intelligent Mapping

Claude performs ALL the intelligence:

| Health Data | Claude's Analysis | Maps To |
|-------------|------------------|---------|
| Age: 68 | 68 is ≥65 | "≥65" |
| Symptoms: "moderately concerning" | Moderate suspicion | "Moderately suspicious" |
| EKG: Normal sinus | No ST changes | "Normal" |
| HTN, DM, HLD | 3 risk factors | "≥3 risk factors" |
| Troponin: 0.02 | Within normal | "≤1x normal limit" |

### 6. Claude Executes with Exact Text

**Tool Call**:
```python
execute_calculator("1752", {
  "history": "Moderately suspicious",  # Exact button text
  "age": "≥65",                       # Exact button text
  "ecg": "Normal",                     # Exact button text
  "risk_factors": "≥3 risk factors",  # Exact button text (truncated)
  "troponin": "≤1x normal limit"      # Exact button text
})
```

### 7. Tool Mechanically Clicks Buttons

The execute function:
1. Finds buttons containing the exact text Claude provided
2. Clicks them
3. Submits the form
4. Returns the result

## Key Benefits

1. **Works for ALL 900+ calculators** - No special cases needed
2. **Handles any UI pattern** - React, Vue, vanilla JS, etc.
3. **Claude does the intelligence** - Tool is purely mechanical
4. **Future-proof** - UI changes don't break the system
5. **Simple tool code** - Just click buttons with matching text

## The Magic

**The screenshot is the bridge**:
- Tool can't detect React fields (returns 0 fields) ❌
- But Claude can SEE them in the screenshot ✅
- Claude tells tool EXACTLY what text to click ✅
- Tool just matches text and clicks ✅

## Implementation Status

✅ Screenshot capture working (but needs size optimization)
✅ Base64 encoding working
✅ Execute function can click buttons by text
⏳ Need to optimize screenshot size (currently 300KB, target 50KB)
⏳ Need to wrap in MCP server
⏳ Need to configure Claude Desktop

## Next Steps

1. Run test with optimized screenshot size
2. Create MCP server wrapper
3. Configure Claude Desktop
4. Test end-to-end with Claude doing the mapping