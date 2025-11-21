# URGENT: Fix Postgres Misconfiguration

## Problem Identified

The Railway Postgres service is **CRASHED** because it's misconfigured to use the wrong Docker image.

### What Happened:

**Last working deployment (Nov 19, 01:51 UTC):**
```json
{
  "builder": "RAILPACK",
  "image": "ghcr.io/railwayapp-templates/postgres-ssl:17"
}
```
✅ This is the correct Postgres container

**Current crashed deployment (Nov 21, 03:20 UTC):**
```json
{
  "builder": "DOCKERFILE",
  "dockerfilePath": "Dockerfile"
}
```
❌ This is trying to run your Python application code as the database!

### Why It's Failing:

Railway is trying to build Postgres using your application's `Dockerfile` (which contains Python/Streamlit/trading code), instead of using the official PostgreSQL container. This causes:
- Build failures
- Service crashes
- "Connection refused" errors from all other services

---

## How to Fix

You have **2 options**: Quick Fix (recommended) or Complete Reset.

---

## OPTION 1: Quick Fix - Redeploy Postgres Correctly (Recommended)

### Step 1: Go to Railway Dashboard
https://railway.app/dashboard

### Step 2: Find the Postgres Service
- Open your project: "joyful-spontaneity"
- Click on the **Postgres** service card

### Step 3: Check Service Settings
1. Click **"Settings"** (gear icon)
2. Scroll to **"Service Source"**
3. You'll likely see it's connected to your GitHub repo - **THIS IS WRONG**

### Step 4: Disconnect from GitHub
1. In Settings → Source
2. If it shows "jhurlbut/polymarketagent" as the source, click **"Disconnect"**
3. Confirm the disconnection

### Step 5: Delete the Broken Postgres Service
1. Still in Settings, scroll to the bottom
2. Click **"Delete Service"**
3. Type the service name to confirm
4. **IMPORTANT**: This will delete the database! If you have critical data, stop here and contact Railway support

### Step 6: Create New Postgres Service
1. In your project dashboard, click **"+ New"**
2. Select **"Database"**
3. Click **"Add PostgreSQL"**
4. Railway will provision a fresh Postgres instance using the correct template
5. Wait ~30 seconds for it to start

### Step 7: Verify It's Working
```bash
railway logs --service Postgres

# You should see:
# PostgreSQL Database directory appears to contain a database; Skipping initialization
# PostgreSQL init process complete; ready for start up.
# database system is ready to accept connections
```

### Step 8: Restart Other Services
Once Postgres is running, restart the polymarket-scanner service:
```bash
railway restart --service polymarket-scanner
```

Or via dashboard:
- Click **polymarket-scanner** → Settings → **"Restart"**

---

## OPTION 2: Complete Reset (If Option 1 Doesn't Work)

If the quick fix doesn't work, you may need to completely remove and recreate the Postgres service:

### Step 1: Backup Data (if any exists)
If you have critical data in the database, export it first:
```bash
# Connect to Postgres and export
railway run --service Postgres pg_dump > backup.sql
```

### Step 2: Delete Postgres Service
1. Railway dashboard → Postgres service → Settings
2. Scroll to bottom → **"Delete Service"**
3. Confirm deletion

### Step 3: Remove Volume (if attached)
1. In project dashboard, check for orphaned volumes
2. Delete any volumes associated with the old Postgres service

### Step 4: Add Fresh Postgres
1. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway provisions a clean Postgres instance
3. New `DATABASE_URL` is automatically injected into all services

### Step 5: Recreate Database Schema
The database will be empty. Your application should auto-create tables on first connection, but if not:
```bash
railway run python -c "from agents.utils.database import db; db.create_tables()"
```

---

## Verification Checklist

After fixing, verify each component:

- [ ] Postgres service shows **"Running"** (green) in Railway dashboard
- [ ] Postgres logs show: `"database system is ready to accept connections"`
- [ ] polymarket-scanner service starts without database errors
- [ ] No more "Connection refused" errors in logs
- [ ] Can deploy dashboard service successfully

---

## Check Current Status

```bash
# List all services
railway service

# Check Postgres deployment status
railway status --service Postgres

# Watch Postgres logs
railway logs --service Postgres --follow

# Check polymarket-scanner after Postgres is fixed
railway logs --service polymarket-scanner --follow
```

---

## Why This Happened

**Root cause**: The `railway.toml` file in your repository root likely caused Railway to treat the Postgres service as a code deployment instead of a managed database service.

**Prevention**:
1. Keep `railway.toml` only for application services
2. Don't connect GitHub repo to database services
3. Use Railway's database templates exclusively for databases

---

## If Problems Persist

1. **Check Railway Status**: https://railway.statuspage.io/
2. **Railway Discord**: https://discord.gg/railway (fast support)
3. **Railway Support**: Create a ticket at railway.app/help

Include this info:
- Project ID: 3ac684fd-1c22-49f9-88f0-ccdbdefd4bab
- Service: Postgres
- Issue: Service trying to build with Dockerfile instead of RAILPACK
- Deployment ID: 6be48f4b-7fb9-4f8b-9c53-db66aaeee094

---

## Timeline

- **Nov 19, 01:51 UTC**: Postgres working correctly (using ghcr.io/railwayapp-templates/postgres-ssl:17)
- **Nov 21, 03:16 UTC**: First broken deployment (switched to Dockerfile builder)
- **Nov 21, 03:20 UTC**: Current crashed deployment
- **Current Status**: CRASHED - not accepting connections

---

**ACTION REQUIRED**: Follow Option 1 steps immediately to restore database service.
