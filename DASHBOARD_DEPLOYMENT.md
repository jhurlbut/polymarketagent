# Streamlit Dashboard Deployment on Railway

This guide explains how to deploy the Streamlit dashboard as a separate Railway service with internal database connectivity.

## Why Deploy on Railway?

The dashboard needs reliable access to the Postgres database. External connections from Streamlit Cloud to Railway's Postgres are unstable. Deploying the dashboard on Railway provides:

- **Reliable Internal Networking**: No external TCP proxy needed
- **Fast Database Queries**: Low latency via Railway's private network
- **Automatic Retries**: Built-in retry logic in `database.py`
- **Environment Variables**: Shared with other services

## Deployment Steps

### 1. Create New Railway Service

Using Railway CLI:

```bash
# Make sure you're in the project directory
cd /path/to/polymarketagent

# Link to your Railway project (if not already linked)
railway link

# Create a new service for the dashboard
railway service create dashboard

# Link to the new service
railway service link dashboard
```

Or via Railway Dashboard:
1. Go to your Railway project
2. Click **"+ New Service"**
3. Select **"GitHub Repo"**
4. Choose your repository
5. Name it: `dashboard`

### 2. Configure Service Settings

In the Railway dashboard for the **dashboard** service:

#### Build Configuration
- **Builder**: Nixpacks (auto-detected)
- **Build Command**: (leave default)
- **Start Command**:
  ```
  streamlit run agents/scripts/python/dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
  ```

#### Environment Variables

The dashboard needs access to the Postgres database. Railway should automatically provide:
- `DATABASE_URL` - Connection string to Railway Postgres (internal)

Add these additional variables:
```
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Note**: The dashboard will automatically use Railway's internal `DATABASE_URL` which provides a stable private network connection.

### 3. Deploy via Railway CLI

```bash
# Switch to the dashboard service context
railway service

# Deploy the current code
railway up

# Watch the deployment logs
railway logs
```

### 4. Configure Public URL

1. In Railway dashboard, go to the **dashboard** service
2. Click **"Settings"** → **"Networking"**
3. Click **"Generate Domain"** to get a public URL
4. Your dashboard will be accessible at: `https://dashboard-production-xxxx.up.railway.app`

## Alternative: Deploy via Git Push

### Option A: Separate Branch (Recommended)

Create a dashboard-specific branch:

```bash
# Create and switch to dashboard branch
git checkout -b dashboard-deploy

# Commit dashboard configuration
git add Procfile.dashboard railway.json DASHBOARD_DEPLOYMENT.md
git commit -m "Add Railway dashboard service configuration"

# Push to trigger deployment
git push origin dashboard-deploy
```

Configure Railway service to deploy from `dashboard-deploy` branch.

### Option B: Root Directory Deployment

If deploying from `main` branch, Railway will use `Procfile.dashboard` if you rename it to `Procfile`:

```bash
# In the dashboard service settings, set Root Directory to: /
# And ensure Start Command is set correctly
```

## Verification

After deployment, verify the dashboard is working:

```bash
# Check logs
railway logs --service dashboard

# You should see:
# ✓ Streamlit server started
# ✓ Database connection established
# ✓ You can now view your app in your browser
```

Visit the generated domain URL to access the dashboard.

## Troubleshooting

### "Module not found" errors
- Verify `requirements.txt` includes all dependencies
- Check build logs: `railway logs --deployment`

### Database connection errors
- Ensure `DATABASE_URL` is set (automatically provided by Railway)
- Check the Postgres service is running
- Verify both services are in the same Railway project

### Port binding errors
- Streamlit must bind to `$PORT` environment variable
- Railway automatically injects this variable
- Start command should include: `--server.port=$PORT`

### 404 on root URL
- Streamlit serves on `/` by default
- Access the generated Railway domain directly

## Cost Optimization

The dashboard service will:
- Use Railway's free tier if available
- Scale down during inactivity (if configured)
- Share the same Postgres database (no additional DB cost)

Estimated monthly cost: $5-10 depending on usage.

## Monitoring

Check dashboard health:

```bash
# Live logs
railway logs --service dashboard --follow

# Recent deployments
railway deployments --service dashboard

# Service status
railway status --service dashboard
```

## Rollback

If something goes wrong:

```bash
# List recent deployments
railway deployments --service dashboard

# Rollback to previous deployment
railway rollback <deployment-id>
```

## Next Steps

After successful deployment:
1. Remove Streamlit Cloud deployment (no longer needed)
2. Update any bookmarks to use the new Railway URL
3. Configure custom domain (optional)
4. Set up monitoring/alerting for the dashboard service
