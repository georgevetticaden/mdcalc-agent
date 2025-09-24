#!/bin/bash

# Launch Chrome browser for MDCalc Clinical Companion demo
# This opens Chrome with remote debugging enabled on port 9222
# The browser window is sized and positioned for demo recording

echo "🚀 Launching Chrome browser for MDCalc Clinical Companion demo..."

# Kill any existing Chrome instances using port 9222
lsof -ti:9222 | xargs kill -9 2>/dev/null

# Set browser window size and position for demo
# Adjust these values based on your screen resolution
WINDOW_WIDTH=1200
WINDOW_HEIGHT=900
WINDOW_X=720  # Position on right side of screen
WINDOW_Y=50

# Chrome executable path (macOS)
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Use a persistent profile directory for session storage
PROFILE_DIR="$HOME/Library/Application Support/MDCalc-Demo-Chrome"

# Create profile directory if it doesn't exist
mkdir -p "$PROFILE_DIR"

echo "📁 Using Chrome profile at: $PROFILE_DIR"
echo "   (Session data will be preserved between runs)"
echo ""

# Launch Chrome with remote debugging and persistent profile
"$CHROME_PATH" \
    --remote-debugging-port=9222 \
    --window-size=$WINDOW_WIDTH,$WINDOW_HEIGHT \
    --window-position=$WINDOW_X,$WINDOW_Y \
    --disable-background-timer-throttling \
    --disable-renderer-backgrounding \
    --disable-backgrounding-occluded-windows \
    --no-first-run \
    --no-default-browser-check \
    --disable-popup-blocking \
    --disable-translate \
    --disable-extensions \
    --disable-features=TranslateUI \
    --disable-ipc-flooding-protection \
    --user-data-dir="$PROFILE_DIR" \
    https://www.mdcalc.com &

# Give Chrome time to start
sleep 3

echo "✅ Chrome browser launched successfully!"
echo "📍 Browser positioned at: ${WINDOW_X},${WINDOW_Y}"
echo "📐 Browser size: ${WINDOW_WIDTH}x${WINDOW_HEIGHT}"
echo "🔌 Remote debugging port: 9222"
echo ""
echo "📝 Next steps:"
echo "1. Position Claude Desktop on the left side of screen"
echo "2. The browser is already positioned on the right"
echo "3. Run your demo - new tabs will open in this browser"
echo ""
echo "To stop the browser, press Ctrl+C or close the window"

# Wait to keep script running
wait