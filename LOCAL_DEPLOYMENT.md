# Local Deployment Guide

Run the entire Polymarket trading system on your local machine - **no cloud costs**.

---

## Prerequisites

- Python 3.10+
- Docker (for Postgres database)
- Git (already installed)

---

## Step 1: Set Up Local Postgres Database

### Option A: Using Docker (Recommended)

```bash
# Start Postgres in Docker
docker run -d \
  --name polymarket-postgres \
  -e POSTGRES_PASSWORD=local_dev_password \
  -e POSTGRES_DB=polymarket \
  -p 5432:5432 \
  postgres:17

# Verify it's running
docker ps | grep polymarket-postgres
```

Your local DATABASE_URL will be:
```
postgresql://postgres:local_dev_password@localhost:5432/polymarket
```

### Option B: Native Postgres Installation

If you prefer not to use Docker:

**macOS:**
```bash
brew install postgresql@17
brew services start postgresql@17
createdb polymarket
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb polymarket
```

DATABASE_URL:
```
postgresql://postgres@localhost:5432/polymarket
```

---

## Step 2: Set Up Python Environment

```bash
cd /Users/jbass/polymarketagent

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r agents/requirements.txt
pip install -r requirements.txt  # For dashboard
```

---

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cat > .env <<'EOF'
# Database
DATABASE_URL=postgresql://postgres:local_dev_password@localhost:5432/polymarket

# Trading Mode
PAPER_TRADING_MODE=true

# Polymarket API (copy these from Railway variables or generate new ones)
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_API_SECRET=your_api_secret_here
POLYMARKET_API_PASSPHRASE=your_api_passphrase_here

# AI APIs (get these from your provider dashboards)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Features
WHALE_TRACKING_ENABLED=true

# Python Path
PYTHONPATH=/Users/jbass/polymarketagent/agents

# Environment
ENVIRONMENT=local
LOG_LEVEL=INFO
EOF
```

**Important**: Add `.env` to `.gitignore` if not already there:
```bash
echo ".env" >> .gitignore
```

---

## Step 4: Initialize Database

```bash
# Activate virtual environment if not already
source venv/bin/activate

# Set Python path
export PYTHONPATH=/Users/jbass/polymarketagent/agents

# Load environment variables
set -a
source .env
set +a

# Create database tables
python -c "from agents.utils.database import db; db.create_tables(); print('✅ Database initialized')"
```

---

## Step 5: Run Trading Agents

### Terminal 1: Main Trading Agent

```bash
cd /Users/jbass/polymarketagent
source venv/bin/activate
export PYTHONPATH=/Users/jbass/polymarketagent/agents

# Load environment
set -a
source .env
set +a

# Run the trading system (checks every 15 minutes)
cd agents
python run_continuous.py --interval 15
```

You should see:
```
✅ Database connection established successfully
✅ Configuration loaded
📊 Starting scan #1...
🔍 Scanning for trading opportunities...
```

---

## Step 6: Run Dashboard

### Terminal 2: Streamlit Dashboard

```bash
cd /Users/jbass/polymarketagent
source venv/bin/activate

# Load environment
set -a
source .env
set +a

# Run dashboard
streamlit run agents/scripts/python/dashboard.py
```

Dashboard will open automatically in your browser at:
```
http://localhost:8501
```

---

## Usage

### Start Everything (Quick Commands)

Create a startup script:

```bash
cat > start_local.sh <<'EOF'
#!/bin/bash

# Start Postgres (if using Docker)
docker start polymarket-postgres 2>/dev/null || \
docker run -d \
  --name polymarket-postgres \
  -e POSTGRES_PASSWORD=local_dev_password \
  -e POSTGRES_DB=polymarket \
  -p 5432:5432 \
  postgres:17

echo "✅ Postgres started"

# Activate venv
source venv/bin/activate

# Load environment
set -a
source .env
set +a

export PYTHONPATH=/Users/jbass/polymarketagent/agents

echo "✅ Environment loaded"
echo ""
echo "Run these commands in separate terminals:"
echo ""
echo "Terminal 1 (Trading Agent):"
echo "  cd agents && python run_continuous.py --interval 15"
echo ""
echo "Terminal 2 (Dashboard):"
echo "  streamlit run agents/scripts/python/dashboard.py"
echo ""
EOF

chmod +x start_local.sh
```

Then just run:
```bash
./start_local.sh
```

### Stop Everything

```bash
# Stop Postgres
docker stop polymarket-postgres

# Ctrl+C in both terminal windows
```

---

## Accessing Services

- **Dashboard**: http://localhost:8501
- **Postgres**: localhost:5432
- **Logs**: Directly in your terminal windows

---

## Advantages of Local Deployment

✅ **Zero Cost**: No cloud hosting fees
✅ **Fast**: No network latency, instant database access
✅ **Easy Debugging**: Direct log access, can use debugger
✅ **Full Control**: No service restarts, no rate limits
✅ **Privacy**: All data stays on your machine

---

## Monitoring

### Check if services are running:

```bash
# Check Postgres
docker ps | grep polymarket-postgres

# Check if agents are running
ps aux | grep run_continuous

# Check if dashboard is running
ps aux | grep streamlit
```

### View logs:

- Trading agent logs: See Terminal 1
- Dashboard logs: See Terminal 2
- Postgres logs: `docker logs polymarket-postgres`

---

## Troubleshooting

### Port 5432 already in use
```bash
# Find what's using port 5432
lsof -i :5432

# If it's another Postgres, stop it:
brew services stop postgresql
# or
sudo systemctl stop postgresql
```

### Can't connect to database
```bash
# Verify Postgres is running
docker ps

# Test connection
psql postgresql://postgres:local_dev_password@localhost:5432/polymarket -c "SELECT 1"
```

### Module not found errors
```bash
# Make sure PYTHONPATH is set
export PYTHONPATH=/Users/jbass/polymarketagent/agents

# Reinstall dependencies
pip install -r agents/requirements.txt
```

### Dashboard won't load
```bash
# Check if port 8501 is available
lsof -i :8501

# Try different port
streamlit run agents/scripts/python/dashboard.py --server.port 8502
```

---

## Optional: Run in Background

If you want services to run in the background:

```bash
# Trading agent in background
nohup python agents/run_continuous.py --interval 15 > trading.log 2>&1 &

# Dashboard in background
nohup streamlit run agents/scripts/python/dashboard.py > dashboard.log 2>&1 &

# View logs
tail -f trading.log
tail -f dashboard.log
```

---

## Cost Comparison

**Railway (estimated):**
- Postgres: $5-10/month
- polymarket-scanner: $5-10/month
- Dashboard: $5/month
- **Total: $15-25/month**

**Local:**
- **Total: $0/month** ✅

Only costs are:
- Electricity (negligible)
- Your machine needs to be running

---

## Next Steps

1. Follow Steps 1-6 above
2. Verify dashboard loads at http://localhost:8501
3. Watch Terminal 1 for trading opportunities
4. Keep both terminals running while you want the system active

---

**Ready to start?** Begin with Step 1: Set Up Local Postgres Database
