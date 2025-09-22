# Tools Directory

Supporting tools and utilities for the MDCalc agent system.

## Components:

### calculator-scraper/
- `scraper.py` - Scrape MDCalc catalog and metadata
- `calculator_metadata.py` - Process and store calculator information

### recording-generator/
- `record_interaction.py` - Create Playwright recordings of MDCalc interactions
- `parse_recording.py` - Extract selectors from recordings

### test-data-generator/
- `generate_test_data.py` - Generate test scenarios with patient data
- `test_scenarios.json` - Pre-defined test cases

### demo-dashboard/ (Optional)
- React dashboard for visualizing demo results
- Shows real-time calculator execution
- Displays synthesized assessments

## Usage:
These tools support development and testing but are not required for runtime operation.