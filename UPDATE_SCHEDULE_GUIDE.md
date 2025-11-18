# Update Schedule Guide - Polymarket Trading System

## 📊 How Often Does Everything Update?

### Current Default Behavior:

#### 🤖 Trading System (Opportunity Scanner):
- **Default:** MANUAL - Runs only when you execute the command
- **No automatic scanning** - You control when it runs
- **Each run:** Scans all markets and looks for opportunities

#### 📈 Dashboard (Front-End):
- **Default:** MANUAL - Shows database data, refresh by clicking button or reloading browser
- **NEW:** Auto-refresh feature available (10-300 seconds)
- **Data source:** Reads from database (shows what trading system has found)

---

## 🔄 Update Options

### Option 1: Manual Execution (Current Setup)

**Pros:**
- Full control over when trades execute
- Good for testing and learning
- No surprises

**Cons:**
- Must remember to run it
- May miss opportunities

**How to use:**
```bash
cd /Users/jbass/polymarketagent/agents
source .venv/bin/activate
python run_trading_system.py
```

**Recommended frequency:** 2-4 times per day
- Morning (9 AM)
- Midday (12 PM)
- Afternoon (4 PM)
- Evening (8 PM)

---

### Option 2: Continuous Mode (Just Created!)

**NEW Script:** `run_continuous.py`

**Pros:**
- Automatic scanning at regular intervals
- Never miss opportunities
- Set it and forget it

**Cons:**
- Runs continuously (uses system resources)
- Need to monitor logs

**How to use:**

```bash
# Scan every 15 minutes (recommended)
python run_continuous.py --interval 15

# Scan every 30 minutes
python run_continuous.py --interval 30

# Scan every 5 minutes (aggressive)
python run_continuous.py --interval 5

# Scan every hour (conservative)
python run_continuous.py --interval 60
```

**Stop with:** Ctrl+C

**Logs saved to:** `continuous_trading.log`

---

### Option 3: Cron Job (Production Setup)

**Pros:**
- Runs in background automatically
- System restart safe
- Most professional approach

**Cons:**
- Requires cron setup
- Less flexible timing

**Setup:**

```bash
# Edit crontab
crontab -e

# Add one of these schedules:

# Every 15 minutes
*/15 * * * * cd /Users/jbass/polymarketagent/agents && source .venv/bin/activate && python run_trading_system.py >> logs/cron.log 2>&1

# Every 30 minutes
*/30 * * * * cd /Users/jbass/polymarketagent/agents && source .venv/bin/activate && python run_trading_system.py >> logs/cron.log 2>&1

# Every hour
0 * * * * cd /Users/jbass/polymarketagent/agents && source .venv/bin/activate && python run_trading_system.py >> logs/cron.log 2>&1

# 4 times per day (9 AM, 12 PM, 4 PM, 8 PM)
0 9,12,16,20 * * * cd /Users/jbass/polymarketagent/agents && source .venv/bin/activate && python run_trading_system.py >> logs/cron.log 2>&1

# During market hours only (9 AM - 9 PM, every 30 min)
*/30 9-21 * * * cd /Users/jbass/polymarketagent/agents && source .venv/bin/activate && python run_trading_system.py >> logs/cron.log 2>&1
```

**View cron jobs:**
```bash
crontab -l
```

**Remove cron job:**
```bash
crontab -e
# Delete the line and save
```

---

### Option 4: Background Service (Advanced)

**For 24/7 operation**, create a system service:

```bash
# Create service file
sudo nano /Library/LaunchDaemons/com.polymarket.trading.plist

# Add:
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.polymarket.trading</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/jbass/polymarketagent/agents/.venv/bin/python</string>
        <string>/Users/jbass/polymarketagent/agents/run_continuous.py</string>
        <string>--interval</string>
        <string>15</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>

# Load service
sudo launchctl load /Library/LaunchDaemons/com.polymarket.trading.plist
```

---

## 📈 Dashboard Auto-Refresh (NEW!)

I just added auto-refresh to your dashboard!

**How to enable:**

1. Open dashboard: http://localhost:8501
2. In sidebar, check **"Enable Auto-Refresh"**
3. Adjust slider for refresh interval (10-300 seconds)
4. Dashboard will automatically reload at that interval

**Recommended intervals:**
- **30 seconds** - If running continuous scanner
- **60 seconds** - Good balance
- **5 minutes** - If running manual scans

**Note:** Dashboard shows data from database. It updates instantly when trading system runs and saves new trades.

---

## 🎯 Recommended Setup by Use Case

### 🧪 Testing & Learning (You are here)
```
Trading System: Manual, 2-4 times per day
Dashboard: Manual refresh or 60s auto-refresh
```

### 📊 Active Monitoring
```
Trading System: Continuous mode (15-30 min intervals)
Dashboard: 30-60s auto-refresh
Keep both running in terminal
```

### 🚀 Production Trading
```
Trading System: Cron job (every 15-30 minutes)
Dashboard: 30s auto-refresh
Logs: Monitor continuously
Alerts: Enable Telegram/Discord
```

### 🏃 Aggressive Trading
```
Trading System: Continuous mode (5-10 min intervals)
Dashboard: 10-30s auto-refresh
Multiple strategies enabled
```

### 😴 Passive/Conservative
```
Trading System: Cron job (4 times per day)
Dashboard: Manual refresh when checking
Focus on high-quality opportunities
```

---

## 📊 Data Flow

```
1. Trading System runs
   ↓
2. Scans Polymarket markets (100 markets)
   ↓
3. Finds opportunities (applies filters)
   ↓
4. Executes trades (paper or live)
   ↓
5. Saves to database (SQLite)
   ↓
6. Dashboard reads from database
   ↓
7. Shows updated metrics/trades
```

**Key Point:** Dashboard is ALWAYS showing latest database data. It updates whenever trading system adds new trades to database.

---

## ⚙️ Current Configuration

Your system right now:
- ✅ Trading System: **Manual execution**
- ✅ Dashboard: **Running with auto-refresh option** (http://localhost:8501)
- ✅ Database: **SQLite** (instant updates)
- ✅ Mode: **Paper Trading** (safe)

---

## 🚀 Quick Start Commands

```bash
cd /Users/jbass/polymarketagent/agents
source .venv/bin/activate

# Run once manually
python run_trading_system.py

# Run continuously (every 15 min)
python run_continuous.py --interval 15

# Run diagnostics
python market_diagnostics.py

# Dashboard is already running at:
# http://localhost:8501
```

---

## 📝 Monitoring & Logs

### Trading System Logs:
```bash
# Main log
tail -f polymarket_trading.log

# Continuous mode log
tail -f continuous_trading.log

# Cron log (if using cron)
tail -f logs/cron.log
```

### Dashboard:
- Open in browser: http://localhost:8501
- Enable auto-refresh in sidebar
- Check "Recent Trades" table for new executions

---

## 💡 Best Practices

### Update Frequency Recommendations:

**By Strategy Type:**
- **Endgame Sweep:** 15-30 minutes (opportunities are time-sensitive)
- **Multi-Option Arbitrage:** 5-10 minutes (need speed)
- **Market Making:** Continuous (always providing liquidity)
- **News Trading:** Real-time (< 1 minute reaction)

**By Market Conditions:**
- **High volatility:** More frequent (5-15 min)
- **Normal conditions:** Standard (15-30 min)
- **Low activity:** Less frequent (30-60 min or 4x/day)

**Resource Considerations:**
- Each scan = 1 API call to Polymarket
- More frequent = better opportunity capture
- Less frequent = lower API usage
- Paper trading = no API rate limits to worry about

---

## 🎊 Summary

### Right Now:
- **Trading:** You run manually when you want
- **Dashboard:** Running with optional auto-refresh
- **Updates:** Only when you execute trading system

### To Make Fully Automated:
```bash
# Option A: Run in terminal (easy to stop)
python run_continuous.py --interval 15

# Option B: Set up cron (runs in background)
crontab -e
# Add: */15 * * * * cd /path/to/agents && source .venv/bin/activate && python run_trading_system.py
```

### Dashboard Auto-Refresh:
- Already added!
- Enable in sidebar
- Choose 10-300 second intervals

---

**Your choice!** The system is flexible - start manual, go continuous when ready. 🚀
