# MDCalc Remote MCP Server - Project Execution Guide

**Complete workflow for deploying your MCP server from local to remote with Cloud Run + Auth0**

---

## Overview

This guide walks you through the complete process of transforming your local MDCalc MCP server into a remote, OAuth-secured service. You'll switch between different tools and environments as needed.

**Estimated Total Time**: 2-3 hours (first time)

**Tools You'll Use**:
- **Web Browser**: Auth0 setup, Google Cloud Console, Claude.ai configuration
- **Terminal**: gcloud CLI commands, testing, deployment
- **Claude Desktop**: For conversations and questions during implementation
- **Claude Code**: For actual code implementation
- **Claude Android**: For final testing

---

## Phase 1: Pre-Implementation Setup (30 minutes)

### Step 1.1: Verify Prerequisites (5 minutes)

**Tool**: Terminal

```bash
# Verify Python version
python3.11 --version  # Should show 3.11.x

# Verify gcloud is configured
gcloud config list

# Should show:
# - account: george.vetticaden@gmail.com
# - project: mdcalc-474013
# - region: us-central1

# Verify git branch
cd ~/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent
git branch  # Should show feature/remote-mcp-server-deployment

# Verify billing is enabled
gcloud billing projects describe mdcalc-474013
```

**If anything fails**: Fix it before proceeding.

### Step 1.2: Create Auth0 Account (10 minutes)

**Tool**: Web Browser

1. Go to https://auth0.com
2. Click "Sign Up"
3. Choose "Personal" account type
4. Complete registration
5. **Choose tenant name carefully**: `mdcalc-mcp` (you can't change this easily)
6. Select region: **US** (closest to your Cloud Run region)
7. Complete setup wizard

**Save these values immediately**:
```bash
# Create a file: ~/auth0-credentials.txt
AUTH0_DOMAIN=mdcalc-mcp.us.auth0.com
AUTH0_TENANT=mdcalc-mcp
```

### Step 1.3: Enable Dynamic Client Registration (10 minutes)

**Tool**: Web Browser (Auth0 Dashboard)

1. Auth0 Dashboard → **Applications** → **APIs**
2. Click **Auth0 Management API** (this is pre-created)
3. Go to **Machine to Machine Applications** tab
4. You'll see your default application listed
5. Toggle it to **Authorized**
6. Click the arrow to expand permissions
7. **Search and enable these 4 permissions**:
   - `create:clients`
   - `read:clients`
   - `update:clients`
   - `delete:clients`
8. Click **Update**

**Verify DCR is working** (Tool: Terminal):
```bash
curl -X POST https://mdcalc-mcp.us.auth0.com/oidc/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test MCP Client",
    "redirect_uris": ["https://localhost/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none"
  }'
```

**Expected**: JSON response with `client_id` field

**If it fails**: DCR is not properly enabled. Go back to Auth0 dashboard and verify the 4 permissions are checked.

### Step 1.4: Create Auth0 API (5 minutes)

**Tool**: Web Browser (Auth0 Dashboard)

1. **Applications** → **APIs** → **Create API**
2. Fill in:
   - **Name**: `MDCalc MCP Server`
   - **Identifier**: `https://mdcalc-mcp-server` (temporary - we'll update after deployment)
   - **Signing Algorithm**: RS256
3. Click **Create**

4. Go to **Permissions** tab
5. Add these scopes (one at a time):

```
Scope               Description
mdcalc:calculate    Calculate medical scores using MDCalc
mdcalc:search       Search MDCalc calculator database
mdcalc:read         Read calculator information and metadata
```

6. Click **Save** after each scope

**Update your credentials file**:
```bash
# Add to ~/auth0-credentials.txt
AUTH0_API_AUDIENCE=https://mdcalc-mcp-server
AUTH0_ISSUER=https://mdcalc-mcp.us.auth0.com/
```

**IMPORTANT**: Note the trailing slash in `AUTH0_ISSUER` - this is required!

---

## Phase 2: Code Implementation (60 minutes)

### Step 2.1: Switch to Claude Code

**Tool**: Claude Code (VS Code extension)

1. Open VS Code
2. Open workspace: `~/Dropbox/Development/Git/09-22-25-mdcalc-agent-v2/mdcalc-agent`
3. Open Claude Code chat panel
4. Load the project context:

**Say to Claude Code**:
```
I'm implementing the remote MCP server deployment per CLAUDE.md 
and requirements/auth-requirements/REMOTE_MCP_DESIGN_SPEC.md.

Please create all the new files needed for Phase 2:
- src/server.py
- src/auth.py  
- src/config.py
- Dockerfile
- .dockerignore
- Update requirements.txt

Use the specifications exactly as written in REMOTE_MCP_DESIGN_SPEC.md
```

**Claude Code will**:
1. Read the specification files
2. Create all necessary files
3. Show you diffs for changes to existing files (requirements.txt)

### Step 2.2: Review Generated Files (10 minutes)

**Tool**: VS Code + Terminal

**Check each file Claude Code created**:

```bash
cd mcp-servers/mdcalc-automation-mcp

# List all new files
ls -la src/
ls -la Dockerfile .dockerignore

# Quick review of key files
cat src/config.py      # Check settings structure
cat src/auth.py        # Check token validation logic
head -50 src/server.py # Check FastAPI setup
cat Dockerfile         # Check container setup
cat requirements.txt   # Check dependencies
```

**Verify these critical elements**:
- [ ] `src/config.py` has Settings class with all Auth0 fields
- [ ] `src/auth.py` has `verify_token` function
- [ ] `src/server.py` has `@app.get("/.well-known/oauth-protected-resource")`
- [ ] `src/server.py` has `@app.post("/sse")` with JSON-RPC 2.0 handling
- [ ] `src/server.py` has `handle_initialize()` method
- [ ] `Dockerfile` installs playwright and chromium
- [ ] `requirements.txt` has fastapi, uvicorn, python-jose, httpx, playwright

### Step 2.3: Create Local Environment File (5 minutes)

**Tool**: Terminal

```bash
cd mcp-servers/mdcalc-automation-mcp

# Create .env file for local testing
cat > .env << 'EOF'
AUTH0_DOMAIN=mdcalc-mcp.us.auth0.com
AUTH0_API_AUDIENCE=http://localhost:8080
AUTH0_ISSUER=https://mdcalc-mcp.us.auth0.com/
MCP_SERVER_URL=http://localhost:8080
PORT=8080
EOF

# Add .env to .gitignore
echo ".env" >> .gitignore
```

### Step 2.4: Local Testing (15 minutes)

**Tool**: Terminal

```bash
# Install dependencies in virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install playwright browsers
playwright install chromium

# Run the server
python src/server.py
```

**In another terminal tab**:
```bash
# Test health endpoint
curl http://localhost:8080/health

# Expected: {"status":"healthy","service":"mdcalc-mcp-server"}

# Test OAuth metadata endpoint
curl http://localhost:8080/.well-known/oauth-protected-resource

# Expected: JSON with "authorization_servers" field

# Test protected endpoint (should fail with 401)
curl -X POST http://localhost:8080/sse

# Expected: 401 with WWW-Authenticate header
```

**If any test fails**: 
- Check terminal for error messages
- Verify .env file is correct
- Ask Claude Code: "The [endpoint] test failed with [error]. What's wrong?"

**If all tests pass**: Kill the local server (Ctrl+C) and proceed.

---

## Phase 3: Deploy to Google Cloud Run (30 minutes)

### Step 3.1: Enable Required APIs (5 minutes)

**Tool**: Terminal

```bash
cd mcp-servers/mdcalc-automation-mcp

# Verify project is set
gcloud config get-value project
# Should show: mdcalc-474013

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Wait for APIs to be enabled (takes 1-2 minutes)
```

### Step 3.2: Initial Deployment (15 minutes)

**Tool**: Terminal

**IMPORTANT**: Replace `mdcalc-mcp.us.auth0.com` with YOUR actual Auth0 domain!

```bash
# Deploy to Cloud Run
gcloud run deploy mdcalc-mcp-server \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --platform managed \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars="AUTH0_DOMAIN=mdcalc-mcp.us.auth0.com" \
  --set-env-vars="AUTH0_API_AUDIENCE=https://mdcalc-mcp-server" \
  --set-env-vars="AUTH0_ISSUER=https://mdcalc-mcp.us.auth0.com/"
```

**This will**:
1. Build a container from your Dockerfile
2. Push to Google Artifact Registry
3. Deploy to Cloud Run
4. Output a service URL

**Expected output** (after 5-10 minutes):
```
Service URL: https://mdcalc-mcp-server-[RANDOM-HASH].run.app
```

**Save this URL**:
```bash
# Save to variable
SERVICE_URL="https://mdcalc-mcp-server-[YOUR-HASH].run.app"

# Save to file
echo "SERVICE_URL=$SERVICE_URL" >> ~/auth0-credentials.txt
```

### Step 3.3: Update Environment Variables (5 minutes)

**Tool**: Terminal

```bash
# Update MCP_SERVER_URL to actual deployed URL
gcloud run services update mdcalc-mcp-server \
  --region us-central1 \
  --update-env-vars="MCP_SERVER_URL=$SERVICE_URL"

# Update audience to match
gcloud run services update mdcalc-mcp-server \
  --region us-central1 \
  --update-env-vars="AUTH0_API_AUDIENCE=$SERVICE_URL"
```

### Step 3.4: Test Deployed Service (5 minutes)

**Tool**: Terminal

```bash
# Test health check
curl $SERVICE_URL/health

# Expected: {"status":"healthy","service":"mdcalc-mcp-server"}

# Test OAuth metadata
curl $SERVICE_URL/.well-known/oauth-protected-resource

# Expected: JSON with your Auth0 domain in "authorization_servers"

# Test protected endpoint (should return 401)
curl -X POST $SERVICE_URL/sse

# Expected: 401 Unauthorized with WWW-Authenticate header
```

**All tests pass?** Proceed to Auth0 update.

**Any test fails?** Check Cloud Run logs:
```bash
gcloud run services logs read mdcalc-mcp-server \
  --region us-central1 \
  --limit 50
```

---

## Phase 4: Update Auth0 with Real URL (10 minutes)

### Step 4.1: Update Auth0 API Settings

**Tool**: Web Browser (Auth0 Dashboard)

1. Go to Auth0 Dashboard → **Applications** → **APIs**
2. Click **MDCalc MCP Server**
3. Go to **Settings** tab
4. Update **Identifier** field:
   - **Old**: `https://mdcalc-mcp-server`
   - **New**: Your actual Cloud Run URL (e.g., `https://mdcalc-mcp-server-abc123.run.app`)
5. **Important**: No trailing slash in the identifier!
6. Click **Save Changes**

### Step 4.2: Verify Configuration

**Tool**: Terminal

```bash
# Test OAuth metadata again (should now show your real URL)
curl $SERVICE_URL/.well-known/oauth-protected-resource | jq

# Verify the "resource" field matches your SERVICE_URL
# Verify "authorization_servers" contains your Auth0 domain
```

---

## Phase 5: Configure in Claude.ai (15 minutes)

### Step 5.1: Add Custom Connector

**Tool**: Web Browser

1. Go to https://claude.ai
2. Click your profile icon → **Settings**
3. In left sidebar → **Connectors**
4. Scroll to bottom → Click **Add custom connector**

### Step 5.2: Enter Connector Details

**In the dialog**:
- **Name**: `MDCalc Clinical Companion`
- **URL**: Paste your Cloud Run URL (e.g., `https://mdcalc-mcp-server-abc123.run.app`)
- **Description** (optional): `Medical calculator automation with voice support`
- **Advanced Settings**: **Leave completely empty** - Claude will discover Auth0 automatically

**Click "Add"**

### Step 5.3: Complete OAuth Flow

**What happens next**:

1. Claude fetches `/.well-known/oauth-protected-resource` from your server
2. Discovers Auth0 authorization server
3. Attempts Dynamic Client Registration with Auth0
4. Redirects you to Auth0 login page

**On Auth0 login page**:
- If you're already logged in to Auth0, you'll see consent screen immediately
- If not logged in, log in with your Auth0 account credentials

**On consent screen**:
- You'll see the requested scopes:
  - `mdcalc:calculate` - Calculate medical scores using MDCalc
  - `mdcalc:search` - Search MDCalc calculator database
  - `mdcalc:read` - Read calculator information and metadata
- Click **Accept** or **Authorize**

**Back on Claude.ai**:
- Connector should now show "Connected" with green indicator
- You'll see your connector in the list

### Step 5.4: Test in Claude Web (5 minutes)

**Tool**: Web Browser (Claude.ai)

1. Start a new conversation in Claude.ai
2. In the chat, the connector should be automatically available
3. Try this message:

```
Search MDCalc for Wells criteria for pulmonary embolism
```

**Expected behavior**:
- Claude should call your MCP server
- You should see the connector being used
- Claude should return search results

**If it works**: Great! Proceed to mobile testing.

**If it fails**: 
- Check if connector shows as "Connected" (green)
- Try disconnecting and reconnecting
- Check Cloud Run logs for errors

---

## Phase 6: Test on Claude Android (20 minutes)

### Step 6.1: Wait for Sync (5 minutes)

**Tool**: Claude Android App

1. Open Claude Android app
2. Go to **Settings** (bottom navigation)
3. Look for **Connectors** or **Tools** section
4. **Wait 1-2 minutes** if you don't see "MDCalc Clinical Companion" yet
5. Close and reopen app if needed

**Connector should appear** as "MDCalc Clinical Companion"

### Step 6.2: Enable Connector in Chat (2 minutes)

**Tool**: Claude Android App

1. Go back to main chat screen
2. Start a **new conversation**
3. Tap the **paperclip icon** or **+** button
4. You should see "Tools" section
5. Find "MDCalc Clinical Companion"
6. **Toggle it ON**

### Step 6.3: Test with Voice Commands (10 minutes)

**Tool**: Claude Android App + Your Voice**

Try these voice commands one by one:

**Test 1: Simple Search**
```
Voice: "Search MDCalc for Wells criteria"
```

**Expected**: Claude searches and returns calculator information

**Test 2: List Calculators**
```
Voice: "What MDCalc calculators are available for heart failure?"
```

**Expected**: Claude lists relevant calculators

**Test 3: Clinical Scenario**
```
Voice: "I have a 68-year-old male patient with chest pain, 
history of hypertension and diabetes. He's a former smoker. 
What cardiac risk calculators should I use?"
```

**Expected**: Claude suggests HEART Score, TIMI, or GRACE calculators

**Test 4: Calculator Execution** (if you've integrated the logic)
```
Voice: "Calculate the Wells score for pulmonary embolism 
for a patient with recent surgery and leg swelling"
```

**Expected**: Claude executes calculator and returns results

### Step 6.4: Monitor Cloud Run Logs (During Testing)

**Tool**: Terminal (in a separate window during mobile testing)

```bash
# Stream logs in real-time
gcloud run services logs tail mdcalc-mcp-server --region us-central1
```

**Watch for**:
- MCP requests coming from Claude Android
- Token validation success messages
- Tool execution logs
- Any error messages

---

## Phase 7: Integrate Your MDCalc Logic (60 minutes)

**Now that the infrastructure works, integrate your actual calculator logic.**

### Step 7.1: Switch Back to Claude Code

**Tool**: Claude Code

**Say to Claude Code**:
```
The remote MCP server is deployed and OAuth is working. 
Now I need to integrate my existing MDCalc client logic 
from mdcalc_client.py into the server.py handlers.

Please update handle_tools_call in server.py to:
1. Import and initialize MDCalcClient
2. Wire up mdcalc_list_all tool
3. Wire up mdcalc_search tool
4. Wire up mdcalc_get_calculator tool (with screenshots)
5. Wire up mdcalc_execute tool

Use the integration examples from CLAUDE.md
```

### Step 7.2: Review and Deploy Changes

**Tool**: Terminal

```bash
# Test locally first
python src/server.py

# In another terminal, test with curl
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

**If local tests pass**:
```bash
# Deploy updated code
gcloud run deploy mdcalc-mcp-server \
  --source . \
  --region us-central1
```

### Step 7.3: End-to-End Testing

**Tool**: Claude Android App

Test full workflow with voice:
```
Voice: "I have a 72-year-old woman with new onset atrial fibrillation. 
She has heart failure with an ejection fraction of 45%, hypertension, 
and type 2 diabetes. She had a GI bleed 2 years ago. 

Should we anticoagulate and what agent should we use?"
```

**Expected**: Claude should:
1. Search for CHA2DS2-VASc and HAS-BLED calculators
2. Calculate both scores
3. Interpret results
4. Recommend anticoagulation approach

---

## Troubleshooting Guide

### Issue: DCR Test Fails in Phase 1

**Symptom**: curl to `/oidc/register` returns 404 or 403

**Fix**:
1. Go to Auth0 Dashboard → Applications → APIs → Auth0 Management API
2. Machine to Machine Applications tab
3. Verify your app is **Authorized** (toggle is ON)
4. Click the arrow to expand
5. Verify all 4 permissions are checked:
   - `create:clients` ✓
   - `read:clients` ✓
   - `update:clients` ✓
   - `delete:clients` ✓
6. Click **Update**
7. Wait 1 minute and retry DCR test

### Issue: Local Server Won't Start

**Symptom**: `python src/server.py` fails with import errors

**Fix**:
```bash
# Verify virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Install playwright
playwright install chromium

# Check for syntax errors
python -m py_compile src/server.py
python -m py_compile src/auth.py
python -m py_compile src/config.py
```

### Issue: Cloud Run Deployment Fails

**Symptom**: Build fails or service won't deploy

**Common causes**:

**1. Dockerfile syntax error**:
```bash
# Test Docker build locally
docker build -t mdcalc-test .
```

**2. Missing dependencies in requirements.txt**:
```bash
# Verify all imports are in requirements.txt
grep -r "^import\|^from" src/*.py | cut -d: -f2 | sort -u
```

**3. Memory issues during build**:
```bash
# Increase memory for build
gcloud run deploy mdcalc-mcp-server \
  --source . \
  --region us-central1 \
  --memory 2Gi  # Increased from 1Gi
```

### Issue: OAuth Metadata Returns 404

**Symptom**: `curl $SERVICE_URL/.well-known/oauth-protected-resource` returns 404

**Fix**:
```bash
# Check if route is defined
curl $SERVICE_URL/  # Should return service info

# Check logs for startup errors
gcloud run services logs read mdcalc-mcp-server \
  --region us-central1 --limit 100

# Verify FastAPI is mounting the route
# Look for line: GET /.well-known/oauth-protected-resource
```

### Issue: Token Validation Fails (401 errors)

**Symptom**: All MCP requests return 401

**Diagnosis**:
```bash
# Get a test token from Auth0
# (Use Postman or Auth0 Dashboard to get a token)

# Test token validation
curl -X POST $SERVICE_URL/sse \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Check logs for specific error
gcloud run services logs tail mdcalc-mcp-server --region us-central1
```

**Common fixes**:

1. **Audience mismatch**:
```bash
# Verify audience matches exactly
curl $SERVICE_URL/.well-known/oauth-protected-resource | jq -r '.resource'
# Should match AUTH0_API_AUDIENCE environment variable

# Update if needed
gcloud run services update mdcalc-mcp-server \
  --region us-central1 \
  --update-env-vars="AUTH0_API_AUDIENCE=$SERVICE_URL"
```

2. **Missing trailing slash in issuer**:
```bash
# Verify issuer has trailing slash
gcloud run services describe mdcalc-mcp-server \
  --region us-central1 \
  --format='value(spec.template.spec.containers[0].env)'

# Should show: AUTH0_ISSUER=https://your-tenant.auth0.com/
#                                                          ^ trailing slash required
```

### Issue: Connector Won't Add in Claude.ai

**Symptom**: "Unable to add connector" or "Failed to fetch metadata"

**Fix**:

1. **Verify OAuth metadata is accessible**:
```bash
curl $SERVICE_URL/.well-known/oauth-protected-resource

# Should return valid JSON with:
# - "resource" field
# - "authorization_servers" array
# - "scopes_supported" array
```

2. **Check CORS headers**:
```bash
curl -X OPTIONS $SERVICE_URL/sse \
  -H "Origin: https://claude.ai" \
  -H "Access-Control-Request-Method: POST"

# Should return Access-Control-Allow-* headers
```

3. **Verify service is public**:
```bash
# Check IAM policy
gcloud run services get-iam-policy mdcalc-mcp-server \
  --region us-central1

# Should show allUsers with roles/run.invoker
```

### Issue: Connector Not Syncing to Claude Android

**Symptom**: Connector works in web but not mobile

**Fix**:

1. **Force sync**:
   - Close Claude Android completely (swipe away from app switcher)
   - Wait 30 seconds
   - Reopen app
   - Go to Settings
   - Wait 2 minutes

2. **Verify account**:
   - Ensure using same account on mobile and web
   - Check account email matches

3. **Check app version**:
   - Update Claude Android to latest version
   - Remote MCP support requires recent app version

4. **Check account plan**:
   - Custom connectors require Claude Pro/Max/Team/Enterprise
   - Free tier does not support custom connectors

---

## Success Checklist

### Phase 1: Auth0 Setup ✓
- [ ] Auth0 account created
- [ ] Dynamic Client Registration enabled
- [ ] DCR test passes (curl returns client_id)
- [ ] API created with scopes defined
- [ ] Credentials saved to file

### Phase 2: Code Implementation ✓
- [ ] All files created by Claude Code
- [ ] Local .env file configured
- [ ] Dependencies installed
- [ ] Local server starts without errors
- [ ] Health check passes (curl localhost:8080/health)
- [ ] OAuth metadata endpoint works locally

### Phase 3: Cloud Run Deployment ✓
- [ ] Required APIs enabled
- [ ] Initial deployment succeeds
- [ ] Service URL obtained
- [ ] Environment variables updated with real URL
- [ ] Health check passes on deployed service
- [ ] OAuth metadata endpoint works on deployed service
- [ ] Protected endpoint returns 401 without token

### Phase 4: Auth0 Update ✓
- [ ] Auth0 API identifier updated to real URL
- [ ] Configuration saved in Auth0

### Phase 5: Claude.ai Configuration ✓
- [ ] Custom connector added
- [ ] OAuth flow completed successfully
- [ ] Connector shows as "Connected"
- [ ] Test query works in Claude web

### Phase 6: Claude Android Testing ✓
- [ ] Connector synced to mobile (visible in Settings)
- [ ] Connector enabled in chat
- [ ] Voice command triggers tool call
- [ ] Results returned successfully
- [ ] Cloud Run logs show requests from mobile

### Phase 7: Logic Integration ✓
- [ ] MDCalcClient integrated into server.py
- [ ] All 4 tools implemented (list, search, get, execute)
- [ ] Local tests pass
- [ ] Deployed and tested on mobile
- [ ] End-to-end clinical scenario works

---

## Time Estimates by Experience Level

### First Time (Complete Novice)
- Phase 1: 45 minutes (reading docs, understanding Auth0)
- Phase 2: 90 minutes (understanding code, troubleshooting)
- Phase 3: 45 minutes (deployment issues, learning gcloud)
- Phase 4: 10 minutes
- Phase 5: 20 minutes
- Phase 6: 30 minutes (waiting, troubleshooting sync)
- Phase 7: 90 minutes (understanding integration)
- **Total**: 5.5 hours

### With Some Experience
- Phase 1: 20 minutes
- Phase 2: 45 minutes
- Phase 3: 20 minutes
- Phase 4: 5 minutes
- Phase 5: 10 minutes
- Phase 6: 15 minutes
- Phase 7: 60 minutes
- **Total**: 2.75 hours

### Expert (Done Before)
- Phase 1: 10 minutes
- Phase 2: 20 minutes (code generation)
- Phase 3: 10 minutes
- Phase 4: 5 minutes
- Phase 5: 5 minutes
- Phase 6: 10 minutes
- Phase 7: 30 minutes
- **Total**: 1.5 hours

---

## Next Steps After Completion

### 1. Add Monitoring
```bash
gcloud logging metrics create mcp_requests \
  --log-filter='resource.type="cloud_run_revision"
    AND resource.labels.service_name="mdcalc-mcp-server"'
```

### 2. Set Up Alerts
```bash
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL \
  --display-name="MCP Server Errors" \
  --condition-threshold-value=10
```

### 3. Enable Custom Domain (Optional)
```bash
gcloud run domain-mappings create \
  --service mdcalc-mcp-server \
  --domain mdcalc.yourdomain.com
```

### 4. Optimize Performance
```bash
# Keep warm to avoid cold starts
gcloud run services update mdcalc-mcp-server \
  --min-instances 1

# Increase resources if needed
gcloud run services update mdcalc-mcp-server \
  --memory 2Gi \
  --cpu 2
```

---

## Summary

You've successfully transformed your local MCP server into a production remote service with:

✅ OAuth 2.1 authentication via Auth0  
✅ Dynamic Client Registration for Claude Android  
✅ Serverless deployment on Google Cloud Run  
✅ Voice command support on mobile  
✅ Maintained all existing intelligence and capabilities  

**Your MDCalc tools are now accessible via voice on Claude Android!**