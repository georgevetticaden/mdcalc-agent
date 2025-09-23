#!/usr/bin/env python3
"""
MDCalc MCP Server
Provides atomic tools for MDCalc automation via Model Context Protocol.
Claude handles all intelligence and mapping - tools are purely mechanical.
"""

import asyncio
import json
import sys
import logging
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mdcalc_client import MDCalcClient

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors to stderr
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MDCalcMCPServer:
    """
    MCP server for MDCalc automation.
    Provides atomic tools - Claude handles ALL orchestration and intelligence.
    """

    def __init__(self):
        self.client = None
        self.initialized = False

    async def initialize(self):
        """Initialize the MDCalc client."""
        if not self.initialized:
            self.client = MDCalcClient()
            await self.client.initialize(headless=True)
            self.initialized = True
            logger.info("MDCalc MCP Server initialized")

    async def handle_request(self, request: Dict) -> Dict:
        """Handle incoming JSON-RPC requests."""
        request_id = request.get('id')
        method = request.get('method')
        params = request.get('params', {})

        try:
            # Initialize client on first tool use
            if method == 'tools/call' and not self.initialized:
                await self.initialize()

            # Handle different methods
            if method == 'initialize':
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {
                            'tools': {}
                        },
                        'serverInfo': {
                            'name': 'mdcalc-automation',
                            'version': '1.0.0'
                        }
                    }
                }

            elif method == 'tools/list':
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'tools': self.get_tools()
                    }
                }

            elif method == 'tools/call':
                tool_name = params.get('name')
                arguments = params.get('arguments', {})

                result = await self.execute_tool(tool_name, arguments)

                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': result
                }

            else:
                # Method not found
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }

    def get_tools(self) -> List[Dict]:
        """Return available tools - atomic operations only."""
        return [
            {
                'name': 'mdcalc_list_all',
                'description': 'Get comprehensive list of all available MDCalc calculators organized by category',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            },
            {
                'name': 'mdcalc_search',
                'description': 'Search MDCalc for medical calculators by condition or name',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {
                            'type': 'string',
                            'description': 'Search term (condition, symptom, or calculator name)'
                        },
                        'limit': {
                            'type': 'integer',
                            'description': 'Maximum number of results to return',
                            'default': 10
                        }
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'mdcalc_get_calculator',
                'description': 'Get input requirements and structure for a specific calculator',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'calculator_id': {
                            'type': 'string',
                            'description': 'MDCalc calculator ID (e.g., "1752") or slug (e.g., "heart-score")'
                        }
                    },
                    'required': ['calculator_id']
                }
            },
            {
                'name': 'mdcalc_execute',
                'description': 'Execute a calculator with provided inputs. Tool is mechanical - YOU must map all values intelligently.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'calculator_id': {
                            'type': 'string',
                            'description': 'MDCalc calculator ID or slug'
                        },
                        'inputs': {
                            'type': 'object',
                            'description': 'Input values mapped to field names. YOU must convert patient data to appropriate values.',
                            'additionalProperties': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': ['calculator_id', 'inputs']
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Execute the specified tool with given arguments."""
        try:
            if tool_name == 'mdcalc_list_all':
                calculators = await self.client.get_all_calculators()

                # Group by category
                by_category = {}
                for calc in calculators:
                    category = calc.get('category', 'Other')
                    if category not in by_category:
                        by_category[category] = []
                    by_category[category].append(calc)

                return {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps({
                                'success': True,
                                'total_count': len(calculators),
                                'categories': list(by_category.keys()),
                                'calculators_by_category': by_category,
                                'all_calculators': calculators
                            }, indent=2)
                        }
                    ]
                }

            elif tool_name == 'mdcalc_search':
                query = arguments.get('query', '')
                limit = arguments.get('limit', 10)

                results = await self.client.search_calculators(query, limit)

                return {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps({
                                'success': True,
                                'count': len(results),
                                'calculators': results
                            }, indent=2)
                        }
                    ]
                }

            elif tool_name == 'mdcalc_get_calculator':
                calculator_id = arguments.get('calculator_id')

                details = await self.client.get_calculator_details(calculator_id)

                # Build response with screenshot as image content
                content = []

                # Add the screenshot as an image if available
                if details.get('screenshot_base64'):
                    content.append({
                        'type': 'image',
                        'data': details['screenshot_base64'],
                        'mimeType': 'image/jpeg'
                    })

                # Add text details (without the base64 data)
                calculator_info = {
                    'success': True,
                    'title': details.get('title'),
                    'url': details.get('url'),
                    'fields_detected': len(details.get('fields', [])),
                    'screenshot_included': bool(details.get('screenshot_base64'))
                }

                content.append({
                    'type': 'text',
                    'text': json.dumps(calculator_info, indent=2)
                })

                return {
                    'content': content
                }

            elif tool_name == 'mdcalc_execute':
                calculator_id = arguments.get('calculator_id')
                inputs = arguments.get('inputs', {})

                result = await self.client.execute_calculator(calculator_id, inputs)

                # Parse the score from the result
                score_text = result.get('score', '')
                risk_text = result.get('risk', '')

                # Extract numeric score if present
                score_value = None
                if score_text and 'point' in score_text.lower():
                    # Extract first number
                    import re
                    match = re.search(r'(\d+)\s*point', score_text.lower())
                    if match:
                        score_value = int(match.group(1))

                # Clean up risk text
                if risk_text:
                    # Extract the actual risk percentage if present
                    risk_match = re.search(r'Risk.*?(\d+\.?\d*%)', risk_text)
                    if risk_match:
                        risk_percentage = risk_match.group(1)
                    else:
                        risk_percentage = None

                    # Extract risk category
                    if 'Low Score' in risk_text:
                        risk_category = 'Low'
                    elif 'Moderate Score' in risk_text:
                        risk_category = 'Moderate'
                    elif 'High Score' in risk_text:
                        risk_category = 'High'
                    else:
                        risk_category = None
                else:
                    risk_percentage = None
                    risk_category = None

                return {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps({
                                'success': result.get('success', False),
                                'score': score_value,
                                'score_text': score_text,
                                'risk_category': risk_category,
                                'risk_percentage': risk_percentage,
                                'full_result': result
                            }, indent=2)
                        }
                    ]
                }

            else:
                return {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps({
                                'success': False,
                                'error': f'Unknown tool: {tool_name}'
                            })
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': json.dumps({
                            'success': False,
                            'error': str(e)
                        })
                    }
                ]
            }

    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.cleanup()
            self.initialized = False


async def main():
    """Main entry point for MCP server."""
    server = MDCalcMCPServer()

    logger.info("MDCalc MCP Server starting...")

    # Read from stdin and write to stdout (MCP protocol)
    while True:
        try:
            # Read line from stdin
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )

            if not line:
                break

            # Parse JSON-RPC request
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                continue

            # Handle request
            response = await server.handle_request(request)

            # Send response
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Server error: {e}")
            error_response = {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }
            sys.stdout.write(json.dumps(error_response) + '\n')
            sys.stdout.flush()

    # Cleanup
    await server.cleanup()
    logger.info("MDCalc MCP Server stopped")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass