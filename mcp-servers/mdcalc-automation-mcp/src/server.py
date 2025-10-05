"""
FastAPI server for MDCalc MCP with OAuth 2.1 authentication.

Transforms the stdio-based MCP server into an HTTP-based server
accessible via Claude Android using OAuth 2.1 with Auth0.

Endpoints:
    GET /health - Health check
    GET /.well-known/oauth-protected-resource - OAuth metadata (RFC 9728)
    OPTIONS /sse - CORS preflight
    POST /sse - MCP endpoint with token validation
"""

import json
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .auth import verify_token, get_token_scopes, require_scope
from .mdcalc_client import MDCalcClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global MDCalc client instance
mdcalc_client: Optional[MDCalcClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Initialize and cleanup resources.
    """
    global mdcalc_client

    # Startup
    logger.info("Initializing MDCalc client...")
    mdcalc_client = MDCalcClient()
    await mdcalc_client.initialize(headless=True)
    logger.info("MDCalc MCP Server ready")

    yield

    # Shutdown
    logger.info("Shutting down MDCalc client...")
    if mdcalc_client:
        await mdcalc_client.cleanup()
    logger.info("MDCalc MCP Server stopped")


# Create FastAPI app
app = FastAPI(
    title="MDCalc MCP Server",
    description="Remote MCP server for MDCalc automation with OAuth 2.1",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Claude.ai and Claude Android
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mdcalc-mcp-server",
        "version": "1.0.0"
    }


@app.get("/.well-known/oauth-protected-resource")
async def oauth_metadata():
    """
    OAuth Protected Resource Metadata (RFC 9728).

    Required for Claude to discover Auth0 as the authorization server
    and initiate Dynamic Client Registration.
    """
    return {
        "resource": settings.MCP_SERVER_URL,
        "authorization_servers": [f"https://{settings.AUTH0_DOMAIN}"],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["mdcalc:read", "mdcalc:calculate"]
    }


@app.options("/sse")
async def sse_options():
    """CORS preflight handler for /sse endpoint."""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        }
    )


@app.post("/sse")
async def mcp_endpoint(
    request: Request,
    token_payload: Dict = Depends(verify_token)
):
    """
    Main MCP endpoint (JSON-RPC 2.0 over HTTP).

    Handles all MCP protocol messages including:
    - initialize
    - tools/list
    - tools/call

    Requires valid OAuth token from Auth0.
    """
    try:
        # Parse JSON-RPC request
        body = await request.json()
        request_id = body.get('id')
        method = body.get('method')
        params = body.get('params', {})

        logger.info(f"MCP request: method={method}, id={request_id}")

        # Extract scopes from token
        scopes = get_token_scopes(token_payload)
        logger.info(f"Token scopes: {scopes}")

        # Handle different MCP methods
        if method == 'initialize':
            return JSONResponse({
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {
                        'tools': {}
                    },
                    'serverInfo': {
                        'name': 'mdcalc-mcp-server',
                        'version': '1.0.0'
                    }
                }
            })

        elif method == 'notifications/initialized':
            # Notification, no response needed
            return Response(status_code=204)

        elif method == 'tools/list':
            # List available tools (filtered by scopes if needed)
            tools = get_tools()
            return JSONResponse({
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'tools': tools
                }
            })

        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})

            # Execute tool with scope validation
            result = await execute_tool(tool_name, arguments, scopes)

            return JSONResponse({
                'jsonrpc': '2.0',
                'id': request_id,
                'result': result
            })

        else:
            # Method not found
            return JSONResponse(
                status_code=200,
                content={
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }
            )

    except HTTPException:
        # Re-raise HTTP exceptions (from token validation)
        raise

    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return JSONResponse(
            status_code=200,
            content={
                'jsonrpc': '2.0',
                'id': request_id if 'request_id' in locals() else None,
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }
        )


def get_tools() -> list:
    """
    Return available MDCalc MCP tools.

    These are atomic, mechanical operations. Claude handles ALL intelligence,
    clinical interpretation, and data mapping. The tools simply navigate,
    screenshot, click, and extract.
    """
    return [
        {
            'name': 'mdcalc_list_all',
            'description': (
                'Get the complete catalog of all 825 MDCalc calculators in an optimized format (~31K tokens). '
                'Returns compact list with just ID, name, and medical category for each calculator. '
                'Use for comprehensive assessments where you need to review all available options by specialty. '
                'URLs can be constructed as: https://www.mdcalc.com/calc/{id}'
            ),
            'inputSchema': {
                'type': 'object',
                'properties': {},
                'required': []
            }
        },
        {
            'name': 'mdcalc_search',
            'description': (
                'Search MDCalc using their sophisticated web search that understands clinical relationships. '
                'Returns semantically relevant calculators, not just keyword matches. '
                'Use for targeted queries when you know what you are looking for. '
                'Example queries: "chest pain" (finds HEART, TIMI), "afib" (finds CHA2DS2-VASc), "sepsis" (finds SOFA).'
            ),
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Search term - can be condition (e.g., "chest pain"), symptom (e.g., "dyspnea"), body system (e.g., "cardiac"), or calculator name (e.g., "HEART Score")'
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum number of results to return (default: 10, max: 50)',
                        'default': 10,
                        'minimum': 1,
                        'maximum': 50
                    }
                },
                'required': ['query']
            }
        },
        {
            'name': 'mdcalc_get_calculator',
            'description': (
                'Get a screenshot and details of a specific MDCalc calculator. '
                'Returns a JPEG screenshot (23KB) of the calculator interface for visual understanding, '
                'plus metadata including title and URL. The screenshot shows all input fields, options, '
                'and current values. YOU must use vision to understand the calculator structure and '
                'map patient data to the appropriate buttons/inputs shown in the screenshot.'
            ),
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'calculator_id': {
                        'type': 'string',
                        'description': (
                            'MDCalc calculator ID or slug. Can be numeric ID (e.g., "1752" for HEART Score) '
                            'or slug format (e.g., "heart-score", "cha2ds2-vasc", "curb-65"). '
                            'Get IDs from mdcalc_search or mdcalc_list_all results.'
                        )
                    }
                },
                'required': ['calculator_id']
            }
        },
        {
            'name': 'mdcalc_execute',
            'description': (
                'Execute a calculator by filling inputs and clicking buttons based on provided values. '
                'This is a MECHANICAL tool - it only clicks what you tell it. YOU must: '
                '1) First call mdcalc_get_calculator to SEE the calculator visually, '
                '2) Map patient data to the EXACT button text or input values shown, '
                '3) Pass the mapped values to this tool. '
                'Returns calculation results AND a result screenshot showing all inputs and results. '
                'ALWAYS examine the result screenshot to verify correct execution and see conditional fields.'
            ),
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'calculator_id': {
                        'type': 'string',
                        'description': 'MDCalc calculator ID (e.g., "1752") or slug (e.g., "heart-score")'
                    },
                    'inputs': {
                        'type': 'object',
                        'description': (
                            'Field values mapped to calculator inputs. Keys should be field names '
                            '(e.g., "age", "history", "troponin"). Values must match EXACT button text '
                            'as shown in screenshot (e.g., "≥65", "Moderately suspicious", "≤1x normal limit"). '
                            'For numeric inputs, provide the numeric value. YOU are responsible for all mapping.'
                        ),
                        'additionalProperties': {
                            'type': 'string'
                        }
                    }
                },
                'required': ['calculator_id', 'inputs']
            }
        }
    ]


async def execute_tool(tool_name: str, arguments: Dict, scopes: list) -> Dict:
    """
    Execute the specified MDCalc tool with given arguments.

    Validates scopes and delegates to MDCalcClient.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        scopes: OAuth scopes from token

    Returns:
        Dict containing 'content' with tool results

    Raises:
        HTTPException: If scope validation fails
    """
    try:
        if tool_name == 'mdcalc_list_all':
            # Requires mdcalc:read scope
            require_scope('mdcalc:read', scopes)

            calculators = await mdcalc_client.get_all_calculators()

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
            # Requires mdcalc:read scope
            require_scope('mdcalc:read', scopes)

            query = arguments.get('query', '')
            limit = arguments.get('limit', 10)

            results = await mdcalc_client.search_calculators(query, limit)

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
            # Requires mdcalc:read scope
            require_scope('mdcalc:read', scopes)

            calculator_id = arguments.get('calculator_id')

            details = await mdcalc_client.get_calculator_details(calculator_id)

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
            # Requires mdcalc:calculate scope
            require_scope('mdcalc:calculate', scopes)

            calculator_id = arguments.get('calculator_id')
            inputs = arguments.get('inputs', {})

            result = await mdcalc_client.execute_calculator(calculator_id, inputs)

            # Parse the score from the result
            score_text = result.get('score', '')
            risk_text = result.get('risk', '')

            # Extract numeric score if present
            score_value = None
            if score_text and 'point' in score_text.lower():
                import re
                match = re.search(r'(\d+)\s*point', score_text.lower())
                if match:
                    score_value = int(match.group(1))

            # Clean up risk text
            if risk_text:
                import re
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

            # Build response content
            content = []

            # Include the result screenshot if available
            if result.get('result_screenshot_base64'):
                content.append({
                    'type': 'image',
                    'data': result['result_screenshot_base64'],
                    'mimeType': 'image/jpeg'
                })

            # Add text results (without the base64 data)
            text_result = {
                'success': result.get('success', False),
                'score': score_value,
                'score_text': score_text,
                'risk_category': risk_category,
                'risk_percentage': risk_percentage,
                'screenshot_included': bool(result.get('result_screenshot_base64')),
                'interpretation': result.get('interpretation'),
                'recommendations': result.get('recommendations')
            }

            # Only include full_result if no screenshot (to avoid duplication)
            if not result.get('result_screenshot_base64'):
                text_result['full_result'] = {
                    k: v for k, v in result.items()
                    if k != 'result_screenshot_base64'
                }

            content.append({
                'type': 'text',
                'text': json.dumps(text_result, indent=2)
            })

            return {
                'content': content
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

    except HTTPException:
        # Re-raise scope validation errors
        raise

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


# For local development/testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True
    )
