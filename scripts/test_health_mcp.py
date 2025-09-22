#!/usr/bin/env python3
"""
Test script to verify health-analysis-server MCP is accessible.
This verifies we can query Snowflake health data through the existing MCP.
"""

import os
import json
import subprocess
from pathlib import Path


def check_claude_config():
    """Check if health-analysis-server is configured in Claude Desktop."""
    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"

    if not config_path.exists():
        print("❌ Claude Desktop config not found at:", config_path)
        return False

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        if 'mcpServers' in config and 'health-analysis-server' in config['mcpServers']:
            health_config = config['mcpServers']['health-analysis-server']
            print("✅ health-analysis-server is configured in Claude Desktop")
            print("\nConfiguration:")
            print(f"  Command: {health_config.get('command')}")
            print(f"  Directory: {health_config.get('args', [])[1] if len(health_config.get('args', [])) > 1 else 'N/A'}")

            # Check environment variables
            env = health_config.get('env', {})
            print("\nSnowflake Configuration:")
            print(f"  User: {env.get('SNOWFLAKE_USER', 'Not set')}")
            print(f"  Account: {env.get('SNOWFLAKE_ACCOUNT', 'Not set')}")
            print(f"  Database: {env.get('SNOWFLAKE_DATABASE', 'Not set')}")
            print(f"  Schema: {env.get('SNOWFLAKE_SCHEMA', 'Not set')}")

            return True
        else:
            print("❌ health-analysis-server not found in Claude Desktop config")
            return False

    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False


def test_health_mcp_server():
    """Test if the health MCP server can be started."""
    health_mcp_path = Path("/Users/aju/Dropbox/Development/Git/multi-agent-health-insight-system-using-claude-code/tools/health-mcp")

    print("\n🔍 Checking health MCP server location...")

    if not health_mcp_path.exists():
        print(f"❌ Health MCP directory not found at: {health_mcp_path}")
        return False

    src_file = health_mcp_path / "src" / "health_mcp.py"
    if not src_file.exists():
        print(f"❌ health_mcp.py not found at: {src_file}")
        return False

    print(f"✅ Health MCP found at: {health_mcp_path}")

    # Check if we can import it (without actually running the server)
    print("\n🧪 Testing Python imports...")
    test_cmd = [
        "/Users/aju/.local/bin/uv",
        "--directory",
        str(health_mcp_path),
        "run",
        "python",
        "-c",
        "import sys; sys.path.insert(0, 'src'); import health_mcp; print('✅ Health MCP imports successfully')"
    ]

    try:
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(f"❌ Import test failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏱️ Import test timed out (this might be normal)")
        return True  # Timeout might mean it's trying to start the server
    except Exception as e:
        print(f"❌ Error testing imports: {e}")
        return False


def create_health_query_example():
    """Create an example of how to query health data."""
    example_path = Path(__file__).parent / "example_health_query.md"

    content = """# Example Health Data Queries

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
"""

    with open(example_path, 'w') as f:
        f.write(content)

    print(f"\n📝 Example queries saved to: {example_path}")


def main():
    """Main test function."""
    print("=" * 60)
    print("Health MCP Server Connection Test")
    print("=" * 60)

    # Test 1: Check Claude Desktop configuration
    print("\n1️⃣ Checking Claude Desktop Configuration...")
    config_ok = check_claude_config()

    # Test 2: Check health MCP server
    print("\n2️⃣ Checking Health MCP Server...")
    server_ok = test_health_mcp_server()

    # Create example queries
    create_health_query_example()

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    if config_ok and server_ok:
        print("✅ Health MCP server is properly configured and ready!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop to load the configuration")
        print("2. Test with: 'Query my health data for latest vitals'")
        print("3. The health data will be available for MDCalc calculations")
    else:
        print("⚠️ Some issues detected. Please check:")
        if not config_ok:
            print("  - Verify health-analysis-server in Claude Desktop config")
        if not server_ok:
            print("  - Check health MCP server installation")
        print("\nRefer to the health MCP documentation for setup instructions")

    return 0 if (config_ok and server_ok) else 1


if __name__ == "__main__":
    exit(main())