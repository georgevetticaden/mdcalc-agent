#!/bin/bash
# Record all priority MDCalc calculators

echo "📹 MDCalc Recording Session"
echo "=========================="
echo ""
echo "This will record interactions with 5 priority calculators."
echo "You'll need to interact with each one manually."
echo ""

# Activate virtual environment
source venv/bin/activate

# Record each calculator
echo "1️⃣ Recording Search functionality..."
python tools/recording-generator/record_interaction.py search

echo "2️⃣ Recording HEART Score..."
python tools/recording-generator/record_interaction.py heart_score

echo "3️⃣ Recording CHA2DS2-VASc..."
python tools/recording-generator/record_interaction.py cha2ds2_vasc

echo "4️⃣ Recording SOFA Score..."
python tools/recording-generator/record_interaction.py sofa

echo "5️⃣ Recording Navigation patterns..."
python tools/recording-generator/record_interaction.py navigation

# Parse all recordings
echo ""
echo "🔍 Parsing recordings to extract selectors..."
python tools/recording-generator/parse_recording.py

# Validate
echo ""
echo "✅ Validating recordings..."
python tools/recording-generator/parse_recording.py --validate

echo ""
echo "✅ Recording session complete!"
echo "Check recordings/ directory for results"