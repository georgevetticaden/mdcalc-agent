# MDCalc MCP Server - Deployment Guide

## Phase 2: Local Testing

### 1. Set Up Environment

```bash
cd mcp-servers/mdcalc-automation-mcp

# Copy environment template
cp .env.example .env

# Edit .env with your Auth0 credentials (already filled in .env.example)
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Test Locally

```bash
# Run the server
python -m uvicorn src.server:app --host 0.0.0.0 --port 8080 --reload

# In another terminal, test endpoints
curl http://localhost:8080/health

curl http://localhost:8080/.well-known/oauth-protected-resource

# Test protected endpoint (should return 401 without token)
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}'
```

### 4. Test with Token

To test with a valid token, you need to get one from Auth0:

```bash
# Get access token from Auth0
curl -X POST https://YOUR-TENANT.auth0.com/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "https://mdcalc-mcp-server",
    "grant_type": "client_credentials"
  }'

# Extract the access_token from response, then test:
export TOKEN="your_access_token_here"

curl -X POST http://localhost:8080/sse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

---

## Phase 3: Google Cloud Run Deployment

### Prerequisites

1. Google Cloud project: `mdcalc-474013`
2. gcloud CLI installed and initialized
3. Billing enabled

### Deployment Steps

```bash
cd mcp-servers/mdcalc-automation-mcp

# Deploy to Cloud Run
gcloud run deploy mdcalc-mcp-server \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300 \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="AUTH0_DOMAIN=YOUR-TENANT.auth0.com" \
  --set-env-vars="AUTH0_API_AUDIENCE=https://mdcalc-mcp-server" \
  --set-env-vars="AUTH0_ISSUER=https://YOUR-TENANT.auth0.com/" \
  --project mdcalc-474013
```

**Note**: The `MCP_SERVER_URL` will be set automatically after deployment.

### Post-Deployment

```bash
# Get the deployed URL
SERVICE_URL=$(gcloud run services describe mdcalc-mcp-server \
  --region us-central1 \
  --format='value(status.url)' \
  --project mdcalc-474013)

echo "Service URL: $SERVICE_URL"

# Update Cloud Run with actual MCP_SERVER_URL
gcloud run services update mdcalc-mcp-server \
  --region us-central1 \
  --set-env-vars="MCP_SERVER_URL=$SERVICE_URL" \
  --project mdcalc-474013

# Update Auth0 API Audience to match Cloud Run URL
# Go to Auth0 Dashboard → APIs → mdcalc-mcp-server
# Update Identifier to: $SERVICE_URL
```

### Test Deployed Service

```bash
# Health check
curl $SERVICE_URL/health

# OAuth metadata
curl $SERVICE_URL/.well-known/oauth-protected-resource

# Get token with updated audience
curl -X POST https://YOUR-TENANT.auth0.com/oauth/token \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"YOUR_CLIENT_ID\",
    \"client_secret\": \"YOUR_CLIENT_SECRET\",
    \"audience\": \"$SERVICE_URL\",
    \"grant_type\": \"client_credentials\"
  }"
```

---

## Phase 4: Claude.ai Configuration

### Add Connector

1. Go to https://claude.ai → Settings → Connectors
2. Click "Add connector"
3. Enter the Cloud Run URL (from `$SERVICE_URL`)
4. **Leave "Advanced Settings" empty** - Claude discovers Auth0 automatically
5. Complete OAuth flow when prompted
6. Grant consent for scopes: `mdcalc:read`, `mdcalc:calculate`

### Verify on Claude Android

1. Close and reopen Claude Android app
2. Wait 1-2 minutes for sync
3. Start a new chat
4. Enable the MDCalc connector
5. Test with voice: "Search MDCalc for HEART score"

---

## Monitoring

### View Logs

```bash
gcloud run services logs tail mdcalc-mcp-server \
  --region us-central1 \
  --project mdcalc-474013
```

### Check Metrics

```bash
gcloud run services describe mdcalc-mcp-server \
  --region us-central1 \
  --project mdcalc-474013
```

---

## Troubleshooting

### "Unable to add connector"

Check OAuth metadata is accessible:
```bash
curl $SERVICE_URL/.well-known/oauth-protected-resource
```

### "Dynamic Client Registration failed"

Test DCR directly:
```bash
curl -X POST https://YOUR-TENANT.auth0.com/oidc/register \
  -H "Content-Type: application/json" \
  -d '{"client_name":"Test","redirect_uris":["https://localhost/callback"]}'
```

### "401 Unauthorized"

Check Auth0 configuration:
- Audience matches MCP_SERVER_URL exactly
- Issuer has trailing slash
- API scopes are defined (mdcalc:read, mdcalc:calculate)

### View detailed logs

```bash
gcloud run services logs read mdcalc-mcp-server \
  --region us-central1 \
  --limit 100 \
  --project mdcalc-474013
```
