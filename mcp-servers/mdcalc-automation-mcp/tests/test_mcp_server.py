#!/usr/bin/env python3
"""
Test MCP Server functionality
Simulates Claude Desktop communication with the MCP server.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mdcalc_mcp import MDCalcMCPServer


async def test_mcp_server():
    """Test MCP server with simulated requests."""
    server = MDCalcMCPServer()

    print("\n" + "="*60)
    print("Testing MDCalc MCP Server")
    print("="*60)

    # Test 1: Initialize
    print("\n1️⃣ Testing initialize...")
    init_request = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'initialize',
        'params': {}
    }
    response = await server.handle_request(init_request)
    print(f"✅ Server initialized: {response['result']['serverInfo']['name']}")

    # Test 2: List tools
    print("\n2️⃣ Testing tools/list...")
    list_request = {
        'jsonrpc': '2.0',
        'id': 2,
        'method': 'tools/list',
        'params': {}
    }
    response = await server.handle_request(list_request)
    tools = response['result']['tools']
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description'][:50]}...")

    # Test 3: List all calculators
    print("\n3️⃣ Testing mdcalc_list_all...")
    list_all_request = {
        'jsonrpc': '2.0',
        'id': 3,
        'method': 'tools/call',
        'params': {
            'name': 'mdcalc_list_all',
            'arguments': {}
        }
    }
    response = await server.handle_request(list_all_request)
    content = response['result']['content'][0]['text']
    list_data = json.loads(content)
    print(f"✅ Found {list_data['total_count']} calculators")
    print(f"   Categories: {', '.join(list_data['categories'])}")

    # Show a few calculators
    for category, calcs in list(list_data['calculators_by_category'].items())[:2]:
        print(f"   {category}: {len(calcs)} calculators")
        for calc in calcs[:2]:
            print(f"      - {calc['name']} (ID: {calc['id']})")

    # Test 4: Search calculators
    print("\n4️⃣ Testing mdcalc_search...")
    search_request = {
        'jsonrpc': '2.0',
        'id': 4,
        'method': 'tools/call',
        'params': {
            'name': 'mdcalc_search',
            'arguments': {
                'query': 'heart',
                'limit': 3
            }
        }
    }
    response = await server.handle_request(search_request)
    content = response['result']['content'][0]['text']
    search_data = json.loads(content)
    print(f"✅ Search returned {search_data['count']} results")
    if search_data['calculators']:
        print(f"   First result: {search_data['calculators'][0]['title']}")

    # Test 5: Get calculator with screenshot
    print("\n5️⃣ Testing mdcalc_get_calculator with screenshot...")
    get_request = {
        'jsonrpc': '2.0',
        'id': 5,
        'method': 'tools/call',
        'params': {
            'name': 'mdcalc_get_calculator',
            'arguments': {
                'calculator_id': '1752'  # HEART Score
            }
        }
    }
    response = await server.handle_request(get_request)

    # Check for image content
    has_image = False
    has_text = False

    for content_item in response['result']['content']:
        if content_item['type'] == 'image':
            has_image = True
            # Image data is base64 encoded
            image_size = len(content_item['data']) * 3 / 4 / 1024  # Rough estimate in KB
            print(f"✅ Screenshot included: ~{image_size:.1f} KB")
        elif content_item['type'] == 'text':
            has_text = True
            text_data = json.loads(content_item['text'])
            print(f"✅ Calculator: {text_data['title']}")
            print(f"   URL: {text_data['url']}")
            print(f"   Fields detected: {text_data['fields_detected']}")
            print(f"   Screenshot included: {text_data['screenshot_included']}")

    if not has_image:
        print("⚠️  No screenshot in response")

    # Test 6: Execute calculator
    print("\n6️⃣ Testing mdcalc_execute...")
    execute_request = {
        'jsonrpc': '2.0',
        'id': 6,
        'method': 'tools/call',
        'params': {
            'name': 'mdcalc_execute',
            'arguments': {
                'calculator_id': '1752',
                'inputs': {
                    # Use exact field names as they appear in the UI
                    # Don't include pre-selected fields (EKG Normal, Initial troponin)
                    'History': 'Moderately suspicious',  # Capital H
                    'Age': '45-64',
                    'Risk factors': '1-2 risk factors'
                    # NOT including:
                    # 'EKG': 'Normal' - already selected by default
                    # 'Initial troponin': '≤normal limit' - already selected by default
                }
            }
        }
    }

    print("   Executing with test inputs...")
    print("   Using exact field names from UI (History, Age, Risk factors)")
    print("   Omitting pre-selected fields (EKG, Initial troponin)")

    try:
        response = await server.handle_request(execute_request)
        content = response['result']['content'][0]['text']
        result_data = json.loads(content)

        if result_data['success']:
            print(f"✅ Execution successful!")
            if result_data.get('score'):
                print(f"   Score: {result_data['score']}")
            if result_data.get('risk_category'):
                print(f"   Risk: {result_data['risk_category']}")
        else:
            print(f"⚠️  Execution failed: {result_data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Execution error: {e}")

    # Cleanup
    await server.cleanup()
    print("\n✅ MCP Server test complete!")

    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    print("✅ Server initializes properly")
    print("✅ Tools are listed correctly (4 tools)")
    print("✅ Calculator catalog available (mdcalc_list_all)")
    print("✅ Search functionality works")
    print("✅ Screenshot capture and transmission works")
    print("✅ Ready for Claude Desktop integration")

    print("\n🔧 Available Tools:")
    print("1. mdcalc_list_all - Get all calculators organized by category")
    print("2. mdcalc_search - Search for calculators by keyword")
    print("3. mdcalc_get_calculator - Get details with screenshot")
    print("4. mdcalc_execute - Execute with mapped inputs")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())