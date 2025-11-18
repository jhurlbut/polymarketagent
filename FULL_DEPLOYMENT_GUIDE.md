# Complete Frontend + Backend Deployment Guide

## Overview

Your Polymarket trading system has two components that need to be deployed:

1. **Frontend (Dashboard)** - Streamlit web app for monitoring
2. **Backend (Trading System)** - Python scanner that finds and executes trades

## Architecture

```
┌─────────────────────────────────────┐
│   FRONTEND: Streamlit Dashboard     │
│   Deployed on: Streamlit Cloud      │
│   URL: yourapp.streamlit.app        │
│   ├─ Shows real-time metrics        │
│   ├─ Displays trade history         │
│   └─ Risk monitoring                │
└──────────────┬──────────────────────┘
               │
               │ Reads/Writes
               ▼
┌─────────────────────────────────────┐
│   DATABASE: PostgreSQL or SQLite    │
│   Deployed on: Supabase (free)      │
│   ├─ Stores trades                  │
│   ├─ Stores market snapshots        │
│   └─ Stores performance metrics     │
└──────────────▲──────────────────────┘
               │
               │ Writes to
               │
┌─────────────────────────────────────┐
│   BACKEND: Trading System           │
│   Deployed on: Railway/Render       │
│   ├─ Scans markets continuously     │
│   ├─ Executes trades                │
│   └─ Updates database               │
└─────────────────────────────────────┘
```

---

## 🎯 Deployment Option 1: All-Free Setup (Recommended to Start)

**Cost:** $0/month
**Best for:** Testing, learning, small-scale trading

### Components:
- Frontend: Streamlit Cloud (free)
- Backend: Railway or Render (free tier)
- Database: Supabase PostgreSQL (free)

---

## Step-by-Step: All-Free Deployment

### Step 1: Set Up PostgreSQL Database (Supabase)

#### 1.1 Create Supabase Account
```
1. Go to: https://supabase.com
2. Click "Start your project"
3. Sign in with GitHub
4. Create new project:
   - Name: polymarket-trading
   - Database Password: [generate strong password]
   - Region: [closest to you]
   - Click "Create new project"
```

#### 1.2 Get Database Connection String
```
1. In Supabase dashboard, go to Settings → Database
2. Find "Connection string" section
3. Copy the URI (session pooler):
   postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

#### 1.3 Initialize Database Schema
```bash
# On your local machine
cd /Users/jbass/polymarketagent/agents
source .venv/bin/activate

# Set database URL
export DATABASE_URL="your_supabase_connection_string"

# Run database initialization
python agents/utils/database.py
```

### Step 2: Deploy Backend Trading System

#### Option A: Railway (Recommended)

##### 2.1 Create Railway Account
```
1. Go to: https://railway.app
2. Click "Login with GitHub"
3. Authorize Railway
```

##### 2.2 Deploy from GitHub
```
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose: jhurlbut/polymarketagent
4. Click "Deploy Now"
```

##### 2.3 Configure Environment Variables
```
In Railway dashboard:
1. Go to your project → Variables
2. Add these variables:

ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
DATABASE_URL=your_supabase_connection_string
PAPER_TRADING_MODE=true
PYTHONPATH=/app/agents
```

##### 2.4 Configure Start Command
```
In Railway dashboard:
1. Go to Settings → Deploy
2. Set start command:
   cd agents && python run_continuous.py --interval 15
```

##### 2.5 Deploy
```
Railway will automatically deploy when you push to GitHub.
Your backend is now running 24/7!
```

#### Option B: Render

##### 2.1 Create Render Account
```
1. Go to: https://render.com
2. Click "Get Started for Free"
3. Sign in with GitHub
```

##### 2.2 Create New Background Worker
```
1. Click "New +" → "Background Worker"
2. Connect your GitHub: jhurlbut/polymarketagent
3. Configure:
   - Name: polymarket-scanner
   - Environment: Python 3
   - Build Command: pip install -r agents/requirements.txt
   - Start Command: cd agents && python run_continuous.py --interval 15
```

##### 2.3 Add Environment Variables
```
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
DATABASE_URL=your_supabase_url
PAPER_TRADING_MODE=true
PYTHONPATH=/opt/render/project/src/agents
```

##### 2.4 Deploy
```
Click "Create Background Worker"
Render will build and deploy automatically
```

### Step 3: Deploy Frontend Dashboard

#### 3.1 Go to Streamlit Cloud
```
1. Visit: https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
```

#### 3.2 Configure App
```
- Repository: jhurlbut/polymarketagent
- Branch: main
- Main file path: agents/scripts/python/dashboard.py
```

#### 3.3 Advanced Settings (Click "Advanced settings")
```
Add these environment variables:

DATABASE_URL=your_supabase_connection_string
PYTHONPATH=/app/agents
```

#### 3.4 Deploy
```
Click "Deploy!"
Your dashboard will be live at: https://[app-name].streamlit.app
```

---

## 🚀 Deployment Option 2: Production Setup

**Cost:** ~$12-25/month
**Best for:** Serious trading, better performance

### Components:
- Frontend: Streamlit Cloud (free)
- Backend: DigitalOcean Droplet or AWS EC2
- Database: Supabase Pro or managed PostgreSQL

### Step 1: Set Up Cloud Server

#### Option A: DigitalOcean Droplet ($4-12/month)

##### 1.1 Create Droplet
```
1. Go to: https://digitalocean.com
2. Create → Droplets
3. Choose:
   - Ubuntu 22.04 LTS
   - Basic plan: $4/month (1GB RAM) or $12/month (2GB RAM)
   - Datacenter: closest to you
   - Authentication: SSH key (recommended) or password
   - Hostname: polymarket-trading
4. Click "Create Droplet"
```

##### 1.2 Connect to Server
```bash
ssh root@your_droplet_ip
```

##### 1.3 Install Dependencies
```bash
# Update system
apt update && apt upgrade -y

# Install Python and pip
apt install -y python3 python3-pip python3-venv git

# Install supervisor for process management
apt install -y supervisor

# Clone your repository
cd /opt
git clone https://github.com/jhurlbut/polymarketagent.git
cd polymarketagent/agents

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

##### 1.4 Configure Environment Variables
```bash
# Create .env file
nano .env

# Add:
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
DATABASE_URL=your_supabase_url
PAPER_TRADING_MODE=true
```

##### 1.5 Create Supervisor Configuration
```bash
nano /etc/supervisor/conf.d/polymarket.conf

# Add:
[program:polymarket-scanner]
command=/opt/polymarketagent/agents/.venv/bin/python /opt/polymarketagent/agents/run_continuous.py --interval 15
directory=/opt/polymarketagent/agents
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/polymarket-scanner.err.log
stdout_logfile=/var/log/polymarket-scanner.out.log
environment=PYTHONPATH="/opt/polymarketagent/agents"
```

##### 1.6 Start Service
```bash
# Reload supervisor
supervisorctl reread
supervisorctl update

# Start the service
supervisorctl start polymarket-scanner

# Check status
supervisorctl status polymarket-scanner

# View logs
tail -f /var/log/polymarket-scanner.out.log
```

##### 1.7 Set Up Auto-Update (Optional)
```bash
# Create update script
nano /opt/update-polymarket.sh

# Add:
#!/bin/bash
cd /opt/polymarketagent
git pull origin main
supervisorctl restart polymarket-scanner

# Make executable
chmod +x /opt/update-polymarket.sh

# Add to crontab (update daily at 3 AM)
crontab -e
# Add line:
0 3 * * * /opt/update-polymarket.sh
```

#### Option B: AWS EC2 (Free Tier Eligible)

##### 1.1 Launch EC2 Instance
```
1. Go to AWS Console → EC2
2. Click "Launch Instance"
3. Choose:
   - Name: polymarket-trading
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t2.micro (free tier)
   - Key pair: Create new or use existing
   - Security group: Allow SSH (port 22)
4. Click "Launch Instance"
```

##### 1.2 Connect and Configure
```bash
# Connect via SSH
ssh -i your-key.pem ubuntu@your-instance-ip

# Follow same installation steps as DigitalOcean above
```

### Step 2: Deploy Frontend
Same as Option 1 Step 3 (Streamlit Cloud)

---

## 🔧 Configuration Files for Deployment

### Create Railway Configuration

Create `railway.toml` in project root:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd agents && python run_continuous.py --interval 15"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Create Render Configuration

Create `render.yaml` in project root:

```yaml
services:
  - type: worker
    name: polymarket-scanner
    env: python
    buildCommand: pip install -r agents/requirements.txt
    startCommand: cd agents && python run_continuous.py --interval 15
    envVars:
      - key: PYTHONPATH
        value: /opt/render/project/src/agents
      - key: PAPER_TRADING_MODE
        value: true
      - key: DATABASE_URL
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
```

---

## 🗄️ Database Migration (SQLite → PostgreSQL)

### Update Database Configuration

Edit `agents/utils/database.py`:

```python
import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

def get_database_url():
    """Get database URL from environment or default to SQLite"""
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Fix Heroku/Railway Postgres URL format
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    else:
        # Default to SQLite for local development
        db_path = os.path.join(os.path.dirname(__file__), "..", "polymarket_trading.db")
        return f"sqlite:///{db_path}"

# Update engine creation
engine = create_engine(
    get_database_url(),
    echo=False,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets
```bash
# Already protected by .gitignore:
# - .env files
# - *.db files
# - *.key files
```

### 2. Use Paper Trading for Public Deployments
```bash
# Always set this for deployments
PAPER_TRADING_MODE=true
```

### 3. Rotate API Keys Regularly
```bash
# Update keys monthly:
# - Anthropic dashboard
# - OpenAI dashboard
# - Update in deployment platform
```

### 4. Monitor Access
```bash
# Check who has access:
# - GitHub repo collaborators
# - Streamlit Cloud team members
# - Cloud server SSH keys
```

### 5. Set Up Alerts
```python
# Add to your .env:
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
DISCORD_WEBHOOK_URL=your_webhook

# Alerts for:
# - Large trades
# - System errors
# - Daily P&L summaries
```

---

## 📊 Monitoring Your Deployment

### Check Backend Status

#### Railway:
```
1. Go to Railway dashboard
2. Click your project
3. View logs in real-time
4. Check metrics (CPU, Memory)
```

#### Render:
```
1. Go to Render dashboard
2. Click your worker
3. View logs
4. Check metrics
```

#### DigitalOcean/AWS:
```bash
# SSH into server
ssh root@your_ip

# Check service status
supervisorctl status polymarket-scanner

# View logs
tail -f /var/log/polymarket-scanner.out.log

# Check resource usage
htop
```

### Check Frontend Status

```
1. Visit your Streamlit app URL
2. Click "Manage app" in bottom right
3. View logs
4. Check analytics
```

### Check Database

```bash
# Local testing with psql
psql "your_supabase_connection_string"

# Or use Supabase dashboard:
1. Go to Supabase project
2. Click "Table Editor"
3. View tables: trades, market_snapshots, etc.
```

---

## 💰 Cost Comparison

### Free Tier (Total: $0/month)
- Frontend: Streamlit Cloud Free (1 app)
- Backend: Railway Free (500 hours/month) or Render Free
- Database: Supabase Free (500MB, 50K requests)
- **Limitations:**
  - Railway free tier: 500 hours/month = ~20 days
  - Render free tier: Sleeps after inactivity
  - Supabase free tier: Limited storage/requests

### Budget Setup (Total: $4-12/month)
- Frontend: Streamlit Cloud Free
- Backend: DigitalOcean Droplet $4-12/month (24/7 uptime)
- Database: Supabase Free (500MB)
- **Best for:** Reliable 24/7 operation

### Professional Setup (Total: $37-57/month)
- Frontend: Streamlit Cloud Team $20/month (or keep free)
- Backend: DigitalOcean $12/month (2GB RAM)
- Database: Supabase Pro $25/month (better performance)
- **Best for:** Serious trading, high volume

---

## 🚨 Troubleshooting

### Backend Not Starting
```bash
# Check logs for errors
# Railway: View in dashboard
# Render: View in dashboard
# DigitalOcean: supervisorctl tail -f polymarket-scanner

# Common issues:
# 1. Missing environment variables
# 2. Wrong PYTHONPATH
# 3. Database connection failed
# 4. Missing dependencies
```

### Database Connection Errors
```bash
# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"

# Common issues:
# 1. Wrong connection string format
# 2. Firewall blocking connection
# 3. Database not initialized
```

### Dashboard Not Loading Data
```bash
# Check if DATABASE_URL is set in Streamlit Cloud
# Check if database has data
# Check Streamlit logs for errors
```

---

## 📈 Scaling Up

### When to Scale:

1. **More Markets:** Increase backend resources (more RAM/CPU)
2. **More Strategies:** Deploy multiple backend workers
3. **More Users:** Upgrade Streamlit Cloud plan
4. **More Data:** Upgrade database storage

### How to Scale:

#### Railway/Render:
```
Upgrade to paid plan: $5-20/month
More resources, better reliability
```

#### DigitalOcean:
```
Resize droplet: $4 → $12 → $24/month
More RAM, CPU, bandwidth
```

#### Multiple Workers:
```
Deploy multiple backend instances
Each running different strategies
All writing to same database
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Test locally with paper trading mode
- [ ] Verify all API keys work
- [ ] Check database schema is correct
- [ ] Review risk management settings
- [ ] Test dashboard displays correctly

### Database Setup
- [ ] Create Supabase account
- [ ] Create new project
- [ ] Get connection string
- [ ] Initialize schema
- [ ] Test connection

### Backend Deployment
- [ ] Choose platform (Railway/Render/DigitalOcean)
- [ ] Create account
- [ ] Deploy from GitHub
- [ ] Set environment variables
- [ ] Test scanner is running
- [ ] Check logs for errors

### Frontend Deployment
- [ ] Create Streamlit Cloud account
- [ ] Deploy from GitHub
- [ ] Set environment variables
- [ ] Test dashboard loads
- [ ] Verify data displays correctly

### Post-Deployment
- [ ] Monitor for 24 hours
- [ ] Check trades are being recorded
- [ ] Verify database is updating
- [ ] Test dashboard auto-refresh
- [ ] Set up alerts (optional)
- [ ] Document your deployment

---

## 🎊 You're Live!

Once deployed, you'll have:

✅ **Frontend Dashboard:** `https://[your-app].streamlit.app`
✅ **Backend Scanner:** Running 24/7 on your chosen platform
✅ **Database:** PostgreSQL storing all your data
✅ **Monitoring:** Logs and metrics for everything
✅ **Auto-restart:** If anything crashes, it restarts automatically

---

## 📞 Support

- GitHub: https://github.com/jhurlbut/polymarketagent
- Streamlit Docs: https://docs.streamlit.io
- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- Supabase Docs: https://supabase.com/docs

---

**Start with the free tier, test thoroughly, then scale up as needed. Good luck! 🚀**
