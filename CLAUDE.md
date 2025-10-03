# CLAUDE.md - MDCalc Clinical Companion: Remote MCP Server Deployment

## Workspace Context
You are working in: `/Users/aju/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent`

**Current Branch**: `feature/remote-mcp-server-deployment`

**Git Repository**: https://github.com/georgevetticaden/mdcalc-agent

## Project Overview

This project transforms the MDCalc Clinical Companion from a **local MCP server** (running on Claude Desktop) to a **remote MCP server** (deployed on Google Cloud Run) accessible via **Claude Android** using voice commands.

### Architecture Transformation

**Before (Local Deployment):**
```
Claude Desktop (macOS) → Local MCP Server → MDCalc Automation
                          (stdio transport)
```

**After (Remote Deployment):**
```
Claude Android → Remote MCP Server (Cloud Run) → MDCalc Automation
                 (HTTP + OAuth 2.1 + JSON-RPC 2.0)
```

---

## Critical Documentation Structure

### Core Requirements Documentation (KEEP THESE)

**Original Agent Design:**
- `requirements/mdcalc-agent-requirements.md` - Core capabilities and features
- `requirements/mdcalc-agent-instructions.md` - Agent orchestration logic (**UNCHANGED**)
- `requirements/mdcalc-project-structure.md` - Directory layout
- `requirements/mdcalc-playwright-mcp.md` - Original MCP design
- `requirements/mdcalc-demo-scenarios.md` - Demo scripts and test cases

**Authentication & Remote Deployment (NEW):**
- **`requirements/auth-requirements/REMOTE_MCP_DESIGN_SPEC.md`** - **PRIMARY IMPLEMENTATION GUIDE**
- `requirements/auth-requirements/mcp-auth-research.md` - Authentication research

---

## What Stays the Same

### 1. Agent Intelligence (UNCHANGED)

The agent instructions in `requirements/mdcalc-agent-instructions.md` remain completely valid:
- **Smart Agent, Dumb Tools** architecture
- Automated data population logic
- Clinical interpretation and synthesis
- Multi-calculator orchestration

**Key Principle**: Claude handles ALL intelligence—data mapping, interpretation, and orchestration. Tools remain purely mechanical.

### 2. MDCalc Client Logic (MOSTLY UNCHANGED)

Your existing `mcp-servers/mdcalc-automation-mcp/src/mdcalc_client.py`:
- Playwright automation
- Calculator catalog (825 calculators)
- Screenshot-based universal support (23KB JPEGs)
- Search and execution logic

**Only the transport layer changes**—not the business logic.

### 3. Health MCP Server (UNCHANGED)

The existing health-analysis-server configuration remains operational:
```json
"health-analysis-server": {
  "command": "/Users/aju/.local/bin/uv",
  "args": ["--directory", "...", "run", "src/health_mcp.py"],
  "env": { "SNOWFLAKE_USER": "...", ... }
}
```

This continues to work locally and is independent of the remote MCP server.

---

## What Changes

### 1. MCP Server Architecture

#### Old Architecture (stdio):
```python
# mdcalc_mcp.py
async def main():
    while True:
        line = sys.stdin.readline()  # Read from stdin
        request = json.loads(line)
        response = await handle_request(request)
        sys.stdout.write(json.dumps(response) + '\n')  # Write to stdout
```

#### New Architecture (HTTP + OAuth):
```python
# server.py
@app.post("/sse")
async def mcp_endpoint(request: Request, token: Dict = Depends(verify_token)):
    body = await request.json()  # JSON-RPC 2.0 format
    
    # Extract JSON-RPC fields
    request_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})
    
    # Route to handler
    if method == "initialize":
        result = handle_initialize()
    elif method == "tools/list":
        result = handle_tools_list(token_scopes)
    elif method == "tools/call":
        result = await handle_tools_call(params, token_scopes)
    
    # Return JSON-RPC response
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    })
```

### 2. Authentication Layer (NEW)

**Components:**
- **Auth0**: External OAuth provider with Dynamic Client Registration (DCR)
- **Token Validation**: JWT verification using JWKS from Auth0
- **Scope-based Authorization**: Tools require specific scopes

**Critical New Files:**
- `mcp-servers/mdcalc-automation-mcp/src/auth.py` - Token validation
- `mcp-servers/mdcalc-automation-mcp/src/config.py` - Configuration management
- `mcp-servers/mdcalc-automation-mcp/src/server.py` - FastAPI server with OAuth

### 3. Deployment Infrastructure (NEW)

**Components:**
- **Dockerfile**: Containerizes the MCP server
- **Google Cloud Run**: Serverless hosting with auto-scaling
- **Environment Variables**: Auth0 credentials and MCP server URL

---

## Implementation Guide

**PRIMARY REFERENCE**: `requirements/auth-requirements/REMOTE_MCP_DESIGN_SPEC.md`

This document provides complete step-by-step instructions for:

### Phase 1: Auth0 Setup (15 minutes)
1. Create Auth0 account and tenant
2. **Enable Dynamic Client Registration** (CRITICAL for Claude Android)
3. Create API with scopes
4. Test DCR endpoint
5. Save credentials

### Phase 2: MCP Server Implementation

**New File Structure:**
```
mcp-servers/mdcalc-automation-mcp/
├── src/
│   ├── server.py       # NEW: FastAPI server with OAuth
│   ├── auth.py         # NEW: Token validation
│   ├── config.py       # NEW: Configuration
│   └── mdcalc_client.py # EXISTING: Your automation logic
├── Dockerfile          # NEW: Container definition
├── requirements.txt    # UPDATED: Add FastAPI, Auth0 deps
└── .dockerignore       # NEW: Exclude unnecessary files
```

**Key Implementation Requirements:**

#### 1. JSON-RPC 2.0 Format (Required by MCP spec)
```python
# Request format
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}

# Response format
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {"tools": [...]}
}

# Error format
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

#### 2. OAuth Metadata Endpoint (Required by RFC 9728)
```python
@app.get("/.well-known/oauth-protected-resource")
async def oauth_metadata():
    return {
        "resource": settings.MCP_SERVER_URL,
        "authorization_servers": [f"https://{settings.AUTH0_DOMAIN}"],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["mdcalc:calculate", "mdcalc:search", "mdcalc:read"]
    }
```

#### 3. Initialize Method (Required by MCP spec)
```python
def handle_initialize() -> Dict:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "mdcalc-mcp-server", "version": "1.0.0"}
    }
```

#### 4. CORS Preflight (Required for Claude.ai)
```python
@app.options("/sse")
async def sse_options():
    return Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    })
```

### Phase 3: Google Cloud Run Deployment

**Prerequisites:**
- Google Cloud project: `mdcalc-474013` (already configured)
- gcloud CLI installed and initialized
- Billing enabled

**Deployment Command:**
```bash
cd mcp-servers/mdcalc-automation-mcp

gcloud run deploy mdcalc-mcp-server \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars="AUTH0_DOMAIN=YOUR-TENANT.auth0.com" \
  --set-env-vars="AUTH0_API_AUDIENCE=https://mdcalc-mcp-server" \
  --set-env-vars="AUTH0_ISSUER=https://YOUR-TENANT.auth0.com/"
```

**Why `--allow-unauthenticated`?**
- OAuth handles authentication, not Google Cloud IAM
- The MCP server validates tokens, not Cloud Run
- This allows Claude Android to reach the endpoint

### Phase 4: Claude.ai Configuration

**Steps:**
1. Go to https://claude.ai → Settings → Connectors
2. Add custom connector with Cloud Run URL
3. **Leave "Advanced Settings" empty** (Claude discovers Auth0 automatically)
4. Complete OAuth flow when prompted
5. Configuration syncs to Claude Android automatically

**OAuth Flow:**
```
1. Claude fetches /.well-known/oauth-protected-resource
2. Discovers Auth0 authorization server
3. Uses Dynamic Client Registration with Auth0
4. Redirects user to Auth0 login
5. User grants consent (sees requested scopes)
6. Auth0 issues access token
7. Claude stores token and uses it for all MCP requests
```

### Phase 5: Testing with Claude Android

**Voice Commands to Test:**
```
"Search MDCalc for Wells criteria"

"Calculate Wells score for pulmonary embolism with 
recent surgery, leg swelling, heart rate 110"

"What calculators are available for heart failure?"

"I have a 72-year-old patient with atrial fibrillation. 
Calculate their stroke risk."
```

**Monitor Logs:**
```bash
gcloud run services logs tail mdcalc-mcp-server --region us-central1
```

---

## Integration with Existing Logic

### Wrapping Your MDCalc Client

**In `server.py`, update `handle_tools_call`:**

```python
from mdcalc_client import MDCalcClient

# Initialize client (reuse your existing code)
mdcalc_client = MDCalcClient()

async def handle_tools_call(params: Dict, scopes: list) -> Dict:
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name == "mdcalc_list_all":
        if "mdcalc:read" not in scopes:
            raise HTTPException(status_code=403)
        
        # Use your catalog
        calculators = await mdcalc_client.list_all_calculators()
        return {
            "content": [{
                "type": "text",
                "text": f"Found {len(calculators)} calculators"
            }]
        }
    
    elif tool_name == "mdcalc_search":
        if "mdcalc:search" not in scopes:
            raise HTTPException(status_code=403)
        
        query = arguments.get("query")
        results = await mdcalc_client.search_calculators(query=query, limit=10)
        
        results_text = "\n".join([
            f"- {r['title']}: {r['description']}"
            for r in results
        ])
        
        return {
            "content": [{
                "type": "text",
                "text": f"Found {len(results)} calculators:\n{results_text}"
            }]
        }
    
    elif tool_name == "mdcalc_get_calculator":
        if "mdcalc:read" not in scopes:
            raise HTTPException(status_code=403)
        
        calculator_id = arguments.get("calculator_id")
        details = await mdcalc_client.get_calculator_details(calculator_id)
        
        return {
            "content": [{
                "type": "text",
                "text": f"Calculator: {details['title']}\nURL: {details['url']}"
            }, {
                "type": "image",
                "data": details['screenshot_base64'],
                "mimeType": "image/jpeg"
            }]
        }
    
    elif tool_name == "mdcalc_execute":
        if "mdcalc:calculate" not in scopes:
            raise HTTPException(status_code=403)
        
        calculator_id = arguments.get("calculator_id")
        inputs = arguments.get("inputs")
        
        result = await mdcalc_client.execute_calculator(
            calculator_id=calculator_id,
            inputs=inputs
        )
        
        return {
            "content": [{
                "type": "text",
                "text": f"Score: {result['score']}\n"
                       f"Risk: {result['risk_category']}\n"
                       f"Interpretation: {result['interpretation']}"
            }]
        }
```

### Screenshot-Based Approach on Cloud Run

Your screenshot-based universal calculator support **works on Cloud Run**:

```python
async def handle_get_calculator(calculator_id: str) -> Dict:
    """Get calculator details with screenshot"""
    
    # Playwright works in Cloud Run (chromium installed via Dockerfile)
    await mdcalc_client.initialize()
    
    # Navigate and capture screenshot
    details = await mdcalc_client.get_calculator_details(calculator_id)
    
    return {
        "content": [{
            "type": "text",
            "text": f"Calculator: {details['title']}\nURL: {details['url']}"
        }, {
            "type": "image",
            "data": details['screenshot_base64'],
            "mimeType": "image/jpeg"
        }]
    }
```

**Why this works:**
- Dockerfile installs chromium: `playwright install --with-deps chromium`
- Cloud Run provides sufficient memory (1Gi default, increase to 2Gi if needed)
- Headless browser works in containerized environment

---

## Dependencies

### Minimal Requirements (requirements.txt)

```txt
# FastAPI and server
fastapi==0.115.0
uvicorn[standard]==0.32.0

# OAuth validation
python-jose[cryptography]==3.3.0
httpx==0.27.0

# Configuration
pydantic==2.9.0
pydantic-settings==2.5.0

# Your existing dependencies
playwright==1.40.0

# Utilities
python-dotenv==1.0.0
```

**What we DON'T include (intentionally):**
- ❌ `sse-starlette` - Not needed (simple HTTP POST works)
- ❌ `slowapi` - Cloud Run handles rate limiting
- ❌ `python-json-logger` - Cloud Run logs are already structured

---

## Environment Configuration

### Local Development (.env)

```bash
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_API_AUDIENCE=http://localhost:8080
AUTH0_ISSUER=https://your-tenant.auth0.com/
MCP_SERVER_URL=http://localhost:8080
PORT=8080
```

### Production (Cloud Run Environment Variables)

```bash
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_API_AUDIENCE=https://mdcalc-mcp-server-xyz.run.app
AUTH0_ISSUER=https://your-tenant.auth0.com/
MCP_SERVER_URL=https://mdcalc-mcp-server-xyz.run.app
PORT=8080
```

---

## Testing Strategy

### 1. Local Testing (Before Deployment)

```bash
# Run server locally
cd mcp-servers/mdcalc-automation-mcp
python src/server.py

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/.well-known/oauth-protected-resource
```

### 2. Cloud Run Testing (After Deployment)

```bash
SERVICE_URL=$(gcloud run services describe mdcalc-mcp-server \
  --region us-central1 --format='value(status.url)')

# Health check
curl $SERVICE_URL/health

# OAuth metadata
curl $SERVICE_URL/.well-known/oauth-protected-resource

# Protected endpoint (should return 401 without token)
curl -X POST $SERVICE_URL/sse
```

### 3. End-to-End Testing (With Claude)

**Via Claude Web:**
1. Add connector in claude.ai
2. Complete OAuth flow
3. Test: "Search MDCalc for HEART score"

**Via Claude Android:**
1. Wait for sync (1-2 minutes)
2. Enable connector in chat
3. Voice: "Calculate Wells score"

---

## Troubleshooting

### Common Issues & Solutions

#### 1. "Unable to add connector"
```bash
# Verify OAuth metadata is accessible
curl https://your-server.run.app/.well-known/oauth-protected-resource

# Should return JSON with authorization_servers field
```

#### 2. "Dynamic Client Registration failed"
```bash
# Test DCR directly
curl -X POST https://YOUR-TENANT.auth0.com/oidc/register \
  -H "Content-Type: application/json" \
  -d '{"client_name":"Test","redirect_uris":["https://localhost/callback"]}'

# Should return client_id
# If fails, DCR is not enabled in Auth0
```

#### 3. "401 Unauthorized" when calling tools
```bash
# Check Cloud Run logs
gcloud run services logs read mdcalc-mcp-server \
  --region us-central1 --limit 50

# Verify Auth0 settings:
# - Audience matches MCP_SERVER_URL exactly
# - Issuer has trailing slash
# - API scopes are defined
```

#### 4. Connector not appearing on Claude Android
- Close and reopen Claude Android app
- Wait 2 minutes for sync
- Verify same Claude account on web and mobile
- Check Claude Android version (update if needed)

#### 5. "Token validation error"
```bash
# Verify JWKS is accessible
curl https://YOUR-TENANT.auth0.com/.well-known/jwks.json

# Should return public keys
```

---

## Production Checklist

### Before Going Live:

- [ ] Auth0 DCR tested and working
- [ ] OAuth metadata endpoint returns valid JSON
- [ ] Token validation working (test with curl)
- [ ] Cloud Run service deploys successfully
- [ ] Health checks passing
- [ ] Connector added and authorized in claude.ai
- [ ] Tools working in Claude web interface
- [ ] Tools synced to Claude Android
- [ ] Voice commands working on mobile

### Production Hardening:

```bash
# Custom domain (optional)
gcloud run domain-mappings create \
  --service mdcalc-mcp-server \
  --domain mdcalc.yourdomain.com

# Increase resources if needed
gcloud run services update mdcalc-mcp-server \
  --memory 2Gi \
  --cpu 2

# Keep warm to avoid cold starts
gcloud run services update mdcalc-mcp-server \
  --min-instances 1

# Set up monitoring
gcloud logging metrics create mcp_requests \
  --log-filter='resource.type="cloud_run_revision"
    AND resource.labels.service_name="mdcalc-mcp-server"'
```

---

## Key Architecture Decisions

### Why Auth0 (Not Google OAuth)?
- ✅ Supports Dynamic Client Registration (RFC 7591)
- ✅ Required by MCP spec for mobile clients
- ❌ Google OAuth doesn't support DCR programmatically

### Why Simple HTTP POST (Not True SSE)?
- ✅ MCP spec supports both HTTP and SSE
- ✅ Simpler implementation
- ✅ Works perfectly for request-response pattern
- ✅ No need for `sse-starlette` library

### Why JSON-RPC 2.0?
- ✅ Required by MCP specification
- ✅ Standard protocol for RPC over HTTP
- ✅ Claude expects this format

### Why No Rate Limiting Library?
- ✅ Cloud Run provides concurrency limits
- ✅ Can set max concurrent requests
- ✅ Auto-scales based on traffic
- ✅ Application-level rate limiting is redundant

---

## Related Documentation

### MCP Specification:
- [MCP Spec June 2025](https://modelcontextprotocol.io/specification/2024-11-05/basic/authorization/)
- [JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [RFC 9728 - OAuth Protected Resource Metadata](https://datatracker.ietf.org/doc/html/rfc9728)
- [RFC 7591 - Dynamic Client Registration](https://datatracker.ietf.org/doc/html/rfc7591)

### Auth0 Documentation:
- [Auth0 APIs](https://auth0.com/docs/api/management/v2)
- [Dynamic Client Registration](https://auth0.com/docs/api/authentication#dynamic-client-registration)
- [Token Validation](https://auth0.com/docs/secure/tokens/json-web-tokens/validate-json-web-tokens)

### Google Cloud Run:
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Hosting MCP Servers](https://cloud.google.com/run/docs/host-mcp-servers)
- [Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)

---

## Implementation Checklist

### Phase 6: Remote MCP Server Deployment

- [ ] **Auth0 Setup**
  - [ ] Create Auth0 account and tenant
  - [ ] Enable Dynamic Client Registration
  - [ ] Create API with scopes
  - [ ] Test DCR endpoint
  - [ ] Save credentials

- [ ] **MCP Server Implementation**
  - [ ] Create `src/server.py` with FastAPI
  - [ ] Create `src/auth.py` for token validation
  - [ ] Create `src/config.py` for configuration
  - [ ] Update `requirements.txt`
  - [ ] Create `Dockerfile`
  - [ ] Create `.dockerignore`

- [ ] **Local Testing**
  - [ ] Run server locally
  - [ ] Test OAuth metadata endpoint
  - [ ] Test health check
  - [ ] Verify token validation

- [ ] **Cloud Run Deployment**
  - [ ] Enable required APIs
  - [ ] Deploy to Cloud Run
  - [ ] Update environment variables
  - [ ] Update Auth0 with real URL
  - [ ] Test deployed endpoints

- [ ] **Claude Configuration**
  - [ ] Add connector in claude.ai
  - [ ] Complete OAuth flow
  - [ ] Test in Claude web
  - [ ] Verify sync to Claude Android

- [ ] **End-to-End Testing**
  - [ ] Test voice commands
  - [ ] Verify calculator execution
  - [ ] Check Cloud Run logs
  - [ ] Monitor performance

---

## Success Metrics

After successful deployment:

### Functional Metrics:
- ✅ MCP server accessible from Claude Android
- ✅ OAuth authentication working end-to-end
- ✅ Voice commands trigger correct tool calls
- ✅ Calculator results returned within 5 seconds
- ✅ Screenshot-based approach working on Cloud Run

### Technical Metrics:
- Response time: <3s for tool calls
- Cold start: <10s (eliminated with min-instances=1)
- Error rate: <1%
- Token validation: 100% success rate
- Uptime: 99.9%

---

## Summary

This guide transforms your local MDCalc MCP server into a remote, OAuth-secured service accessible via Claude Android voice commands.

**Key Points:**
1. Follow `requirements/auth-requirements/REMOTE_MCP_DESIGN_SPEC.md` for implementation
2. Existing MDCalc client logic remains mostly unchanged
3. Agent instructions stay the same
4. Authentication layer is new but straightforward
5. Deploy to Google Cloud Run with minimal configuration
6. Voice commands work exactly like desktop conversations

**The goal:** Enable voice-based clinical calculator access on mobile while maintaining all desktop capabilities.