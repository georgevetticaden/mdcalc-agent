# MDCalc Execution Quick Reference Guide

## Golden Rules for MDCalc Automation

### Rule 1: Screenshot First, Always
```
ALWAYS: mdcalc_get_calculator() → Examine screenshot → mdcalc_execute()
NEVER: Skip the screenshot and guess field names
```

### Rule 2: Use EXACT Field Names
| ❌ WRONG | ✅ CORRECT | Why |
|----------|-----------|-----|
| `'history'` | `'History'` | Capital H as shown |
| `'risk_factors'` | `'Risk factors'` | Space, not underscore |
| `'ecg'` | `'EKG'` | Exact text from UI |
| `'troponin'` | `'Initial troponin'` | Full field name |
| `'hdl'` | `'HDL Cholesterol'` | Complete name with capitals |

### Rule 3: Only Change What Needs Changing
- **Green/Teal background = Already selected**
- **DO NOT pass fields already at desired value**
- **Clicking a selected value DESELECTS it**

## Common Calculator Patterns

### HEART Score (ID: 1752)
**Default selections:**
- EKG: "Normal" (green)
- Initial troponin: "≤normal limit" (green)

**Typical execution:**
```json
{
  "History": "Moderately suspicious",
  "Age": "45-64",
  "Risk factors": "1-2 risk factors"
  // Don't include EKG or Initial troponin if keeping defaults
}
```

### CHA2DS2-VASc (ID: 801)
**Default selections:**
- Sex: "Male" (green)
- All history fields: "No" (green)

**Typical execution:**
```json
{
  "Age": "65-74",
  "Sex": "Female",  // Only if changing from Male
  "CHF history": "Yes",  // Only if Yes
  "Hypertension history": "Yes",  // Only if Yes
  // Don't include fields staying at "No"
}
```

### LDL Calculator (ID: 70)
**No defaults - all numeric inputs:**
```json
{
  "Total Cholesterol": "200",
  "HDL Cholesterol": "50",
  "Triglycerides": "150"
}
```

## Visual Cues in Screenshots

### How to Identify Selected Options
- **Green/Teal background** (#1abc9c or rgb(26, 188, 156)) = Selected
- **White/Gray background** = Not selected
- **Number in corner** (e.g., "+1", "+2") = Point value

### Field Types
1. **Button Groups**: Click one option (e.g., Age ranges)
2. **Yes/No Toggles**: Binary choices
3. **Numeric Inputs**: Text fields for values
4. **Multi-select**: Rare, check instructions

## Debugging Checklist

If execution fails:
1. ✓ Did you get the screenshot first?
2. ✓ Are field names EXACTLY as shown (capitals, spaces)?
3. ✓ Are you trying to set a field to its current value?
4. ✓ Is the button text exactly right (e.g., "≥65" not ">65")?
5. ✓ For numeric fields, are you passing strings not numbers?

## Quick Test Commands

Test if field names are correct:
```python
# Get screenshot and examine
details = mdcalc_get_calculator("1752")
# Look at the screenshot - what are the EXACT field names?
# What's already selected (green)?
```

## Remember: You're the Smart Agent

The MCP tool is dumb - it just clicks what you tell it. YOU must:
- SEE the calculator through screenshots
- UNDERSTAND what's already selected
- MAP patient data to exact button text
- DECIDE what needs to change

**When in doubt, get the screenshot and look!**