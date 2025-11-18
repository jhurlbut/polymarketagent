# Quick Start Guide - Polymarket Trading System

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd /Users/jbass/polymarketagent/agents

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

**Minimum Required:**
```env
# Get from: https://console.anthropic.com
ANTHROPIC_API_KEY="your_key_here"

# Get from: https://platform.openai.com
OPENAI_API_KEY="your_key_here"

# Keep paper trading enabled for testing
PAPER_TRADING_MODE="true"
```

Save and exit (Ctrl+X, Y, Enter)

### Step 3: Initialize Database

```bash
export PYTHONPATH="."
python agents/utils/database.py
```

### Step 4: Run Your First Strategy!

```bash
# Run the system (paper trading mode - safe!)
python run_trading_system.py
```

You should see output like:
```
======================================================================
POLYMARKET TRADING SYSTEM
======================================================================
Started at: 2025-11-17 12:00:00

Validating configuration...
✓ Configuration is valid

Initializing database...
✓ Database initialized successfully

Initializing components...
✓ Polymarket client initialized
✓ Risk manager initialized
✓ Strategy manager initialized

Registering strategies...
✓ Registered: Endgame Sweep Strategy

...
```

### Step 5: View the Dashboard

Open a new terminal:

```bash
cd /Users/jbass/polymarketagent/agents
source .venv/bin/activate
streamlit run scripts/python/dashboard.py
```

Dashboard will open at: http://localhost:8501

## What You'll See

### Dashboard Shows:
- 💰 Available Capital
- 📈 Net P&L
- 📋 Open Positions
- ✅ Risk Status
- 📊 Performance Metrics
- 📜 Trade History

### First Run Results:
- System will scan for endgame sweep opportunities
- Find markets priced 0.95-0.99 near settlement
- Calculate optimal position sizes
- **In paper trading mode**: Simulate trades (no real money)
- Track everything in database
- Display results in dashboard

## Common Commands

```bash
# Run all strategies
python run_trading_system.py

# Run specific strategy
python run_trading_system.py --strategy endgame_sweep

# Test mode (find opportunities only, don't execute)
python run_trading_system.py --test

# Verbose logging
python run_trading_system.py --verbose

# View dashboard
streamlit run scripts/python/dashboard.py
```

## Test the Components

```bash
# Test configuration
python -c "from agents.utils.config import config; config.print_config()"

# Test database
python agents/utils/database.py

# Test risk manager
python agents/application/risk_manager.py

# Test analytics
python agents/application/analytics.py

# Test strategy manager
python agents/application/strategy_manager.py

# Test endgame strategy
python agents/application/strategies/endgame_sweep.py
```

## Expected First Run

When you run `python run_trading_system.py` for the first time:

1. ✅ System validates configuration
2. ✅ Database tables created
3. ✅ Polymarket client initialized
4. ✅ Risk manager checks limits
5. ✅ Strategy scans markets
6. ✅ Finds 0-10 opportunities (depending on market conditions)
7. ✅ Simulates trades (paper mode)
8. ✅ Records in database
9. ✅ Shows summary

### Sample Output:
```
Found 5 endgame sweep opportunities

Attempting to execute: Endgame sweep: YES @ $0.970, expected profit 3.09%, confidence 80%
PAPER TRADE: Would buy 800.00 USDC of YES @ 0.970
Paper trade recorded: Trade #1

Total trades executed: 5
Total capital deployed: $4000.00

Executed trades:
  1. endgame_sweep - Will Bitcoin reach $100k by Dec 2025?... - $800.00
  2. endgame_sweep - Will Trump win 2028 election?... - $850.00
  ...
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"

```bash
# Make sure you activated the virtual environment
source .venv/bin/activate

# Then reinstall
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not set"

```bash
# Edit .env file and add your API key
nano .env

# Make sure you're in the agents directory
cd /Users/jbass/polymarketagent/agents
```

### "Database errors"

```bash
# Re-initialize database
export PYTHONPATH="."
python agents/utils/database.py
```

### "No opportunities found"

This is normal! Depending on market conditions:
- There may be no markets in the 0.95-0.99 range
- Markets may not be close to settlement
- Black swan risk may be too high

Try:
- Running at different times of day
- Adjusting thresholds in .env
- Checking Polymarket.com for active markets

## Next Steps

### 1. Monitor Performance (1-2 weeks)

Run the system daily and watch the dashboard:
- Check trade execution
- Monitor win rate
- Track P&L
- Analyze strategy performance

### 2. Optimize Settings (After testing)

Edit `.env` to tune parameters:
```env
ENDGAME_MIN_PRICE=0.93  # Lower for more opportunities
ENDGAME_MAX_PRICE=0.98  # Adjust range
MAX_POSITION_SIZE_PCT=5  # More conservative
```

### 3. Add More Strategies

Implement additional strategies:
- Multi-option arbitrage
- Market making
- News trading

Follow the framework in `agents/application/strategies/`

### 4. Go Live (When ready)

After 1-2 months of successful paper trading:

```env
# Edit .env
PAPER_TRADING_MODE="false"
POLYGON_WALLET_PRIVATE_KEY="your_wallet_key"
```

**⚠️ Important**:
- Start with small capital ($500-1000)
- Monitor closely for first week
- Gradually increase capital
- Never risk more than you can afford to lose

## Getting Help

### Documentation
- 📖 `ENHANCED_SYSTEM_README.md` - Full documentation
- 📋 `POLYMARKET_TRADING_PLAN.md` - Implementation plan
- 📝 `IMPLEMENTATION_SUMMARY.md` - What we built

### Logs
- Check `polymarket_trading.log` for details
- Use `--verbose` flag for more info

### Test Mode
- Always use `--test` flag to find opportunities without executing

## Success Metrics

After 1 week of paper trading, you should see:
- ✅ 10-50 trades executed
- ✅ 70-90% win rate
- ✅ Positive net P&L
- ✅ No system errors
- ✅ Risk limits functioning

## Remember

✅ **Start in paper trading mode** (default)
✅ **Test thoroughly** before going live
✅ **Monitor daily** via dashboard
✅ **Start small** when going live
✅ **Never risk** more than you can afford to lose
✅ **Follow regulations** in your jurisdiction

---

## One-Command Summary

```bash
# The whole setup:
cd /Users/jbass/polymarketagent/agents && \
python3 -m venv .venv && \
source .venv/bin/activate && \
pip install -r requirements.txt && \
cp .env.example .env && \
echo "Now edit .env to add your API keys, then run:" && \
echo "export PYTHONPATH='.' && python agents/utils/database.py && python run_trading_system.py"
```

---

**You're ready to trade! 🚀**

Start with paper trading, monitor performance, and scale gradually. Good luck! 📈
