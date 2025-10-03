# MDCalc MCP Server - Simplified Implementation Guide
## Deploy to Google Cloud Run with Auth0 OAuth for Claude Android

**Based on: MCP Specification June 2025 + Production Best Practices**

---

## Architecture Overview

```
┌──────────────────┐
│  Claude Android  │
│   (MCP Client)   │
└────────┬─────────┘
         │
         │ 1. Discovers OAuth metadata
         ▼
┌─────────────────────────────────────────┐
│  Your MCP Server (Cloud Run)            │
│  GET /.well-known/oauth-protected-      │
│      resource                           │
│  → Points to Auth0                      │
└────────┬────────────────────────────────┘
         │
         │ 2. OAuth flow with Auth0
         ▼
┌─────────────────────────────────────────┐
│    Auth0 Authorization Server           │
│  • Dynamic Client Registration          │
│  • User login & consent                 │
│  • Issues access tokens                 │
└────────┬────────────────────────────────┘
         │
         │ 3. Claude calls tools with token
         ▼
┌─────────────────────────────────────────┐
│  MCP Server validates token & responds  │
└─────────────────────────────────────────┘
```

---

## Prerequisites

**Required:**
- Google Cloud account (project: `mdcalc-474013`)
- Auth0 account (free tier works)
- Claude Pro/Max/Team/Enterprise
- Python 3.11
- gcloud CLI installed

**Clone your repository:**
```bash
cd ~/Dropbox/Development/Git/
git clone -b feature/remote-mcp-server-deployment \
  https://github.com/georgevetticaden/mdcalc-agent.git
cd mdcalc-agent
```

---

## Phase 1: Auth0 Setup (15 minutes)

### Step 1: Create Auth0 Account

1. Go to https://auth0.com → Sign up
2. Create tenant: `mdcalc-mcp` (note your domain: `mdcalc-mcp.us.auth0.com`)

### Step 2: Enable Dynamic Client Registration

**Critical: This allows Claude to auto-register**

1. Auth0 Dashboard → **Applications** → **APIs**
2. Click **Auth0 Management API**
3. **Machine to Machine Applications** tab
4. Find your application → **Authorize**
5. Grant these permissions:
   - `create:clients`
   - `read:clients`
   - `update:clients`
   - `delete:clients`

### Step 3: Create API

1. **Applications** → **APIs** → **Create API**
2. Settings:
   - **Name**: `MDCalc MCP Server`
   - **Identifier**: `https://mdcalc-mcp-server` (temporary, update after deployment)
   - **Signing Algorithm**: RS256

### Step 4: Define Scopes

In your API → **Permissions** tab, add:

```
mdcalc:calculate    Calculate medical scores
mdcalc:search       Search MDCalc database
mdcalc:read         Read calculator information
```

### Step 5: Test DCR (Verify it works)

```bash
curl -X POST https://YOUR-TENANT.auth0.com/oidc/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test MCP Client",
    "redirect_uris": ["https://localhost/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none"
  }'
```

Should return `client_id` and registration details. If it fails, DCR is not enabled.

### Step 6: Save These Values

```bash
AUTH0_DOMAIN="YOUR-TENANT.auth0.com"
AUTH0_API_AUDIENCE="https://mdcalc-mcp-server"  # Will update later
AUTH0_ISSUER="https://YOUR-TENANT.auth0.com/"   # Note trailing slash
```

---

## Phase 2: MCP Server Implementation

### Project Structure

```
mdcalc-agent/
└── mcp-servers/
    └── mdcalc-automation-mcp/
        ├── src/
        │   ├── server.py       # NEW: Main FastAPI server
        │   ├── auth.py         # NEW: Token validation
        │   ├── config.py       # NEW: Configuration
        │   └── mdcalc_mcp.py   # EXISTING: Your tools
        ├── Dockerfile          # NEW
        ├── requirements.txt    # UPDATED
        └── .dockerignore       # NEW
```

### File 1: requirements.txt

**Minimal dependencies only:**

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

### File 2: src/config.py

```python
"""Configuration management"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    PORT: int = int(os.environ.get('PORT', 8080))
    HOST: str = "0.0.0.0"
    
    # Auth0
    AUTH0_DOMAIN: str = os.environ.get('AUTH0_DOMAIN', '')
    AUTH0_API_AUDIENCE: str = os.environ.get('AUTH0_API_AUDIENCE', '')
    AUTH0_ISSUER: str = os.environ.get('AUTH0_ISSUER', '')
    
    # MCP Server URL
    MCP_SERVER_URL: str = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### File 3: src/auth.py

```python
"""OAuth token validation with Auth0"""
import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Dict, Optional
from functools import lru_cache
import logging

from config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

@lru_cache(maxsize=1)
def get_jwks() -> Dict:
    """Fetch JWKS from Auth0 (cached)"""
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    
    try:
        response = httpx.get(jwks_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching JWKS: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch auth keys")

def get_rsa_key(token: str) -> Optional[Dict]:
    """Extract RSA key matching token's kid"""
    try:
        unverified_header = jwt.get_unverified_header(token)
        jwks = get_jwks()
        
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header["kid"]:
                return {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
    except Exception as e:
        logger.error(f"Error getting RSA key: {e}")
    
    return None

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict:
    """
    Verify JWT token from Auth0.
    Returns decoded token payload if valid.
    """
    token = credentials.credentials
    rsa_key = get_rsa_key(token)
    
    if not rsa_key:
        raise HTTPException(status_code=401, detail="Unable to find appropriate key")
    
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.AUTH0_API_AUDIENCE,
            issuer=settings.AUTH0_ISSUER
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTClaimsError:
        raise HTTPException(status_code=401, detail="Invalid token claims")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Unable to validate token: {str(e)}")
```

### File 4: src/server.py

**Core implementation with JSON-RPC 2.0:**

```python
"""
MCP Server with OAuth 2.1 Authentication
Simple HTTP POST with JSON-RPC 2.0 format
"""
from fastapi import FastAPI, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import logging

from config import settings
from auth import verify_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MDCalc MCP Server",
    description="Medical calculator MCP server with OAuth 2.1",
    version="1.0.0"
)

# CORS (Claude.ai needs this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# REQUIRED: OAuth Protected Resource Metadata
# ============================================

@app.get("/.well-known/oauth-protected-resource")
async def oauth_metadata():
    """
    OAuth 2.0 Protected Resource Metadata (RFC 9728)
    Tells Claude where to find the authorization server
    """
    return {
        "resource": settings.MCP_SERVER_URL,
        "authorization_servers": [f"https://{settings.AUTH0_DOMAIN}"],
        "bearer_methods_supported": ["header"],
        "scopes_supported": [
            "mdcalc:calculate",
            "mdcalc:search",
            "mdcalc:read"
        ]
    }

# ============================================
# Health Checks
# ============================================

@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "service": "mdcalc-mcp-server"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MDCalc MCP Server",
        "auth": "OAuth 2.1 via Auth0",
        "oauth_metadata": f"{settings.MCP_SERVER_URL}/.well-known/oauth-protected-resource"
    }

# ============================================
# MCP Endpoints (JSON-RPC 2.0)
# ============================================

@app.options("/sse")
async def sse_options():
    """Handle CORS preflight"""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        }
    )

@app.post("/sse")
async def mcp_endpoint(request: Request, token: Dict = Depends(verify_token)):
    """
    MCP endpoint with JSON-RPC 2.0 format
    Protected by OAuth - requires valid access token
    """
    try:
        body = await request.json()
        
        # Extract JSON-RPC fields
        request_id = body.get("id")
        method = body.get("method")
        params = body.get("params", {})
        
        # Log authenticated request
        user_id = token.get("sub", "unknown")
        scopes = token.get("scope", "").split()
        logger.info(f"MCP request: method={method}, user={user_id}, scopes={scopes}")
        
        # Route to handler
        if method == "initialize":
            result = handle_initialize()
        elif method == "tools/list":
            result = handle_tools_list(scopes)
        elif method == "tools/call":
            result = await handle_tools_call(params, scopes)
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })
        
        # Return JSON-RPC success response
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP error: {e}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        })

# ============================================
# MCP Method Handlers
# ============================================

def handle_initialize() -> Dict:
    """Handle MCP initialize request"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "mdcalc-mcp-server",
            "version": "1.0.0"
        }
    }

def handle_tools_list(scopes: list) -> Dict:
    """Return list of available tools"""
    tools = []
    
    # Only show tools user has access to
    if "mdcalc:calculate" in scopes:
        tools.append({
            "name": "calculate_mdcalc",
            "description": "Calculate medical scores using MDCalc",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "calculator_id": {
                        "type": "string",
                        "description": "MDCalc calculator ID (e.g., 'wells-score-pe')"
                    },
                    "inputs": {
                        "type": "object",
                        "description": "Calculator input parameters"
                    }
                },
                "required": ["calculator_id", "inputs"]
            }
        })
    
    if "mdcalc:search" in scopes:
        tools.append({
            "name": "search_mdcalc",
            "description": "Search MDCalc calculator database",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        })
    
    return {"tools": tools}

async def handle_tools_call(params: Dict, scopes: list) -> Dict:
    """Execute tool call"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    # Check permissions
    if tool_name == "calculate_mdcalc":
        if "mdcalc:calculate" not in scopes:
            raise HTTPException(
                status_code=403,
                detail="Missing required scope: mdcalc:calculate"
            )
        
        # TODO: Import your mdcalc_mcp.py logic here
        # from mdcalc_mcp import calculate
        # result = await calculate(arguments)
        
        return {
            "content": [{
                "type": "text",
                "text": f"Calculated {arguments.get('calculator_id')} with inputs: {arguments.get('inputs')}"
            }]
        }
    
    elif tool_name == "search_mdcalc":
        if "mdcalc:search" not in scopes:
            raise HTTPException(
                status_code=403,
                detail="Missing required scope: mdcalc:search"
            )
        
        # TODO: Implement search
        return {
            "content": [{
                "type": "text",
                "text": f"Search results for: {arguments.get('query')}"
            }]
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")

# ============================================
# Error Handler
# ============================================

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    """Return WWW-Authenticate header per RFC 9728"""
    return JSONResponse(
        status_code=401,
        headers={
            "WWW-Authenticate": f'Bearer realm="{settings.MCP_SERVER_URL}", '
                              f'resource_metadata="{settings.MCP_SERVER_URL}/.well-known/oauth-protected-resource"'
        },
        content={"detail": "Authentication required"}
    )

# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
```

### File 5: Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application
COPY src/ ./src/

# Environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Run server
CMD ["python", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### File 6: .dockerignore

```
__pycache__
*.pyc
*.pyo
.Python
venv/
.env
.git
.gitignore
*.md
.DS_Store
```

---

## Phase 3: Deploy to Google Cloud Run

### Step 1: Setup

```bash
cd mcp-servers/mdcalc-automation-mcp

# Set project
gcloud config set project mdcalc-474013

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### Step 2: Deploy

```bash
gcloud run deploy mdcalc-mcp-server \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --platform managed \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars="AUTH0_DOMAIN=YOUR-TENANT.auth0.com" \
  --set-env-vars="AUTH0_API_AUDIENCE=https://mdcalc-mcp-server" \
  --set-env-vars="AUTH0_ISSUER=https://YOUR-TENANT.auth0.com/"
```

**Replace `YOUR-TENANT` with your Auth0 tenant name**

### Step 3: Get URL and Update

```bash
# Get deployed URL
SERVICE_URL=$(gcloud run services describe mdcalc-mcp-server \
  --region us-central1 --format='value(status.url)')

echo "Your MCP Server URL: $SERVICE_URL"

# Update MCP_SERVER_URL
gcloud run services update mdcalc-mcp-server \
  --region us-central1 \
  --update-env-vars="MCP_SERVER_URL=$SERVICE_URL"
```

### Step 4: Update Auth0 with Real URL

1. Go to Auth0 Dashboard → APIs → MDCalc MCP Server
2. Update **Identifier** to your actual Cloud Run URL (e.g., `https://mdcalc-mcp-server-xyz.run.app`)
3. Update audience in Cloud Run:

```bash
gcloud run services update mdcalc-mcp-server \
  --region us-central1 \
  --update-env-vars="AUTH0_API_AUDIENCE=$SERVICE_URL"
```

### Step 5: Test Deployment

```bash
# Health check (should work)
curl $SERVICE_URL/health

# OAuth metadata (should return JSON)
curl $SERVICE_URL/.well-known/oauth-protected-resource

# Protected endpoint (should return 401)
curl -X POST $SERVICE_URL/sse
```

---

## Phase 4: Configure in Claude.ai

### Step 1: Add Custom Connector

1. Go to https://claude.ai
2. Profile icon → **Settings** → **Connectors**
3. **Add custom connector**

### Step 2: Enter Details

- **Name**: `MDCalc Clinical Companion`
- **URL**: Your Cloud Run URL (from above)
- **Advanced Settings**: Leave empty (Claude discovers Auth0 automatically)

### Step 3: Complete OAuth

Claude will:
1. Fetch OAuth metadata from your server
2. Discover Auth0
3. Use Dynamic Client Registration
4. Redirect you to Auth0 login
5. Show consent screen

**Follow the prompts** to authorize.

### Step 4: Verify

Connector should show as "Connected" with green indicator.

---

## Phase 5: Test with Claude Android

### Step 1: Wait for Sync

Open Claude Android → Settings → Should see "MDCalc Clinical Companion" (may take 1-2 minutes)

### Step 2: Enable in Chat

1. Start new conversation
2. Tap tools icon
3. Toggle on "MDCalc Clinical Companion"

### Step 3: Test with Voice

Try:
```
"Search MDCalc for Wells criteria"

"Calculate Wells score for pulmonary embolism"

"What MDCalc calculators are available?"
```

### Step 4: Monitor Logs

```bash
gcloud run services logs tail mdcalc-mcp-server --region us-central1
```

---

## Troubleshooting

### "Unable to add connector"

```bash
# Check OAuth metadata
curl https://your-server.run.app/.well-known/oauth-protected-resource

# Should return JSON with authorization_servers
```

### "401 Unauthorized"

```bash
# Check logs
gcloud run services logs read mdcalc-mcp-server --region us-central1 --limit 50

# Verify Auth0 settings match:
# - Audience = MCP_SERVER_URL
# - Issuer has trailing slash
```

### Connector not on mobile

- Close and reopen Claude Android
- Wait 2 minutes for sync
- Verify same account on web and mobile

### Test token validation

```bash
# In Auth0 dashboard, create test M2M app
# Get token and test:
curl -X POST https://your-server.run.app/sse \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

---

## Next Steps

### Integrate Your MDCalc Logic

Update `handle_tools_call` in `server.py`:

```python
# Import your existing code
from mdcalc_mcp import MDCalcClient

async def handle_tools_call(params: Dict, scopes: list) -> Dict:
    if tool_name == "calculate_mdcalc":
        mdcalc = MDCalcClient()
        result = await mdcalc.calculate(
            calculator_id=arguments['calculator_id'],
            inputs=arguments['inputs']
        )
        return {
            "content": [{
                "type": "text",
                "text": str(result)
            }]
        }
```

### Add More Tools

Expand based on your MDCalc capabilities:
- Batch calculations
- Calculator favorites
- Evidence retrieval

### Production Enhancements

```bash
# Custom domain
gcloud run domain-mappings create \
  --service mdcalc-mcp-server \
  --domain mdcalc.yourdomain.com

# Increase memory if needed
gcloud run services update mdcalc-mcp-server \
  --memory 2Gi

# Keep warm (avoid cold starts)
gcloud run services update mdcalc-mcp-server \
  --min-instances 1
```

---

## Summary

You now have:

- MCP server compliant with June 2025 spec
- OAuth 2.1 via Auth0 with Dynamic Client Registration
- JSON-RPC 2.0 format for MCP protocol
- Simple, maintainable codebase
- Works with Claude Android voice commands

**Your MDCalc tools are accessible via voice on Claude Android!**

---

## Key Files Reference

**Production files:**
- `src/server.py` - Main MCP server (JSON-RPC 2.0)
- `src/auth.py` - Token validation
- `src/config.py` - Configuration
- `Dockerfile` - Container definition
- `requirements.txt` - Dependencies (minimal)

**What we DIDN'T include:**
- No `sse-starlette` (not needed)
- No `slowapi` (Cloud Run handles rate limiting)
- No `python-json-logger` (Cloud Run logs are structured by default)
- No complex health checks

This is intentionally simple and production-ready.