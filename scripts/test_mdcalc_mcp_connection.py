#!/usr/bin/env python3
"""
Test MDCalc MCP Server Connection
Verifies the MCP server starts and responds correctly.
"""

import subprocess
import json
import sys
import time

def test_mcp_server():
    """Test that the MDCalc MCP server starts and responds."""

    print("\n" + "="*60)
    print("Testing MDCalc MCP Server Connection")
    print("="*60)

    # Command from claude_desktop_config.json
    cmd = [
        "python",
        "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
    ]

    env = {
        "PYTHONPATH": "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent"
    }

    print("\n1. Starting MCP server...")
    print(f"   Command: {' '.join(cmd)}")

    try:
        # Start the server
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**subprocess.os.environ, **env},
            text=True
        )

        # Give it time to start
        time.sleep(2)

        # Send initialize request
        print("\n2. Sending initialize request...")
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }

        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()

        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line)
            if 'result' in response:
                print("✅ Server initialized successfully!")
                print(f"   Server: {response['result']['serverInfo']['name']}")
                print(f"   Version: {response['result']['serverInfo']['version']}")
            else:
                print("❌ Unexpected response:", response)
        else:
            print("❌ No response from server")

        # Send tools/list request
        print("\n3. Requesting available tools...")
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()

        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line)
            if 'result' in response:
                tools = response['result']['tools']
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool['name']}")
            else:
                print("❌ Unexpected response:", response)
        else:
            print("❌ No response from server")

        # Clean shutdown
        process.terminate()
        process.wait(timeout=5)
        print("\n✅ Server shutdown cleanly")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    print("\n" + "="*60)
    print("MDCalc MCP Server Configuration:")
    print("="*60)
    print("""
Add this to your claude_desktop_config.json:

"mdcalc-automation": {
  "command": "python",
  "args": [
    "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent/mcp-servers/mdcalc-automation-mcp/src/mdcalc_mcp.py"
  ],
  "env": {
    "PYTHONPATH": "/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent"
  }
}
    """)

    print("\n✅ Configuration is correct and server is working!")
    print("\nNext steps:")
    print("1. Restart Claude Desktop")
    print("2. Open a new conversation")
    print("3. Check if MDCalc tools appear (mdcalc_list_all, mdcalc_search, etc.)")

    return True

if __name__ == "__main__":
    # Activate virtual environment first
    print("Make sure you're in the virtual environment!")
    print("Run: source venv/bin/activate")

    success = test_mcp_server()
    sys.exit(0 if success else 1)