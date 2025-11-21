# Deploy Dashboard to Railway - Step-by-Step

All configuration files are ready and pushed to GitHub. Follow these exact steps:

---

## Step 1: Open Railway Dashboard

Go to: **https://railway.app/dashboard**

Log in with your GitHub account.

---

## Step 2: Open Your Project

Find and click on your project: **"joyful-spontaneity"** (or "polymarketagent")

You should see 2 existing services:
- Postgres
- polymarket-scanner

---

## Step 3: Create New Service

1. Click the **"+ New"** button (top right)
2. Select **"GitHub Repo"**
3. You'll see a list of your repositories
4. Select: **"jhurlbut/polymarketagent"**
5. Railway will start configuring the service

---

## Step 4: Configure the Service

Railway will create a new service. Now configure it:

### 4a. Name the Service
1. Click on the new service card
2. Click on **"Settings"** (gear icon)
3. Under **"Service Name"**, change it to: **dashboard**

### 4b. Set Start Command
Still in Settings:
1. Scroll to **"Deploy"** section
2. Find **"Custom Start Command"**
3. Enter:
```
streamlit run agents/scripts/python/dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=true
```
4. Click **"Update"** or it auto-saves

### 4c. Set Root Directory (if needed)
1. Still in Settings → Deploy section
2. If there's a **"Root Directory"** field, leave it as: **/** (or blank)

---

## Step 5: Verify Environment Variables

1. Click on the **"Variables"** tab
2. Railway should automatically have:
   - ✅ `DATABASE_URL` - (from Postgres service)
   - ✅ `PORT` - (auto-injected by Railway)

3. **Add these additional variables** (click "New Variable" for each):
   ```
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   PAPER_TRADING_MODE=true
   ```

4. Click **"Add"** for each variable

---

## Step 6: Trigger Deployment

Railway should auto-deploy after configuration. If not:

1. Go to **"Deployments"** tab
2. Click **"Deploy"** or **"Redeploy"**
3. Watch the build logs:
   - Building with Nixpacks
   - Installing requirements
   - Starting Streamlit

**Expected logs:**
```
Collecting usage statistics...
You can now view your Streamlit app in your browser.
```

---

## Step 7: Generate Public Domain

1. Go to **"Settings"** tab
2. Find **"Networking"** section
3. Click **"Generate Domain"**
4. Railway will provide a URL like:
   ```
   https://dashboard-production-xxxx.up.railway.app
   ```
5. **Copy this URL** - this is your dashboard!

---

## Step 8: Verify Dashboard Works

1. Open the generated domain URL in your browser
2. You should see the Polymarket Trading Dashboard
3. Check for:
   - ✅ No database connection errors
   - ✅ Strategy settings load
   - ✅ Trade history appears (may be empty)
   - ✅ No crashes or timeouts

If you see database errors, verify the Postgres service is running.

---

## Step 9: Check Logs (if issues)

```bash
# From your terminal
railway logs --service dashboard --follow
```

Or in Railway dashboard:
1. Click on **dashboard** service
2. Go to **"Deployments"** tab
3. Click on the latest deployment
4. View **"Build Logs"** and **"Deploy Logs"**

---

## Troubleshooting

### Build fails with "requirements.txt not found"
- Check Root Directory is set to `/` or blank
- Verify requirements.txt is in the repository root

### "Port already in use" or "Address in use"
- Railway's `$PORT` variable might not be set
- Check Settings → Deploy → Custom Start Command includes `--server.port=$PORT`

### Database connection errors
- Verify Postgres service is running (green status)
- Check `DATABASE_URL` is in Variables tab
- Restart dashboard service

### 502 Bad Gateway
- Service might be starting up (wait 30-60 seconds)
- Check deploy logs for Python errors
- Verify start command is correct

---

## After Successful Deployment

Your dashboard is now:
- ✅ Running on Railway's internal network
- ✅ Connected directly to Postgres (no external proxy)
- ✅ Accessible via public domain
- ✅ Auto-deploys on git push to main branch

**Bookmark the domain URL for easy access!**

---

## Commands Reference

```bash
# View dashboard logs
railway logs --service dashboard

# Restart dashboard
railway restart --service dashboard

# Check status
railway status --service dashboard

# Redeploy after code changes
git push origin main
# Railway auto-deploys
```

---

**Ready to proceed?** Follow steps 1-8 above. The entire process takes ~5 minutes.
