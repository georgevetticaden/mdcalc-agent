#!/bin/bash

# Setup script for MDCalc Clinical Companion Demo
# This script prepares everything needed for recording a demo

echo "🎬 MDCalc Clinical Companion - Demo Setup"
echo "=========================================="
echo ""

# Step 1: Launch the demo browser
echo "Step 1: Launching demo browser..."
./launch_demo_browser.sh &
BROWSER_PID=$!

# Wait for browser to start
sleep 5

echo "✅ Browser launched (PID: $BROWSER_PID)"
echo ""

# Step 2: Instructions for Claude Desktop
echo "Step 2: Configure Claude Desktop"
echo "---------------------------------"
echo "1. Open Claude Desktop"
echo "2. Position it on the LEFT side of your screen"
echo "3. Update the config to use demo mode:"
echo ""
echo "   In ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "   Set MDCALC_HEADLESS to \"false\""
echo ""
echo "   Or copy the demo config:"
echo "   cp claude_desktop_demo_config.json ~/Library/Application\\ Support/Claude/claude_desktop_config.json"
echo ""
echo "4. Restart Claude Desktop"
echo ""

# Step 3: Demo instructions
echo "Step 3: Recording the Demo"
echo "--------------------------"
echo "✅ Browser is positioned on the RIGHT (1200x900)"
echo "✅ Remote debugging enabled on port 9222"
echo "✅ New calculators will open in new tabs"
echo ""
echo "Demo talking points:"
echo "1. Natural language clinical scenario"
echo "2. Show parallel calculator execution"
echo "3. Demonstrate result synthesis"
echo "4. Highlight visual understanding (screenshots)"
echo ""

# Step 4: Test connection
echo "Step 4: Testing browser connection..."
echo "--------------------------------------"

# Test if port 9222 is accessible
if nc -z localhost 9222 2>/dev/null; then
    echo "✅ Chrome remote debugging port is accessible"

    # Test playwright connection
    python3 -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.connect_over_cdp('http://localhost:9222')
        contexts = browser.contexts
        print('✅ Playwright can connect to browser')
        print(f'   Active contexts: {len(contexts)}')
        await browser.close()
    except Exception as e:
        print(f'❌ Playwright connection failed: {e}')
    finally:
        await playwright.stop()

asyncio.run(test())
" 2>/dev/null
else
    echo "❌ Chrome remote debugging port not accessible"
    echo "   Please check if browser launched correctly"
fi

echo ""
echo "🎥 Demo setup complete!"
echo "========================"
echo ""
echo "To stop the demo:"
echo "1. Close the Chrome browser window"
echo "2. Or press Ctrl+C in this terminal"
echo ""
echo "Waiting... Press Ctrl+C to stop"

# Keep script running
wait $BROWSER_PID