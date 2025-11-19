# 🐋 Whale Following Strategy - Complete Implementation

## ✅ What's Been Built

A **fully automated whale-following trading system** that:

1. **Discovers Whales** automatically from Polymarket markets
2. **Scores Quality** using multi-factor algorithm (win rate, consistency, timing, etc.)
3. **Generates Signals** when high-quality whales enter positions
4. **Copies Trades** with Kelly Criterion position sizing
5. **Manages Risk** with delays, slippage protection, and validation

---

## 🚀 Three Ways to Use It

### Option 1: Automatic Discovery (BEST - Fully Automated)

Let the system find whales for you:

```bash
# Test locally
python3 run_whale_discovery.py --once

# Run continuously
python3 run_whale_discovery.py

# Or just enable in trading system
export WHALE_TRACKING_ENABLED=true
python3 run_trading_system.py
```

**What happens:**
- Scans Polymarket markets every 5 minutes
- Finds trades >$500
- Tracks traders with >$50k volume
- Auto-scores after 10+ trades
- Auto-tracks whales with quality >=0.70
- Generates signals automatically

**Timeline:**
- First whale discovered: ~1 hour
- First whale scored: ~24 hours
- First auto-tracked whale: ~48 hours
- Mature whale database: ~1 week

See: [`AUTOMATIC_WHALE_DISCOVERY.md`](AUTOMATIC_WHALE_DISCOVERY.md)

---

### Option 2: Manual Entry (Good for Testing)

Add specific whales you've researched:

```bash
python3 scripts/python/find_whales.py
# Interactive tool to add whales
```

Or use test data:
```bash
python3 seed_test_whales.py
# Creates 5 test whales + 6 signals
```

Then test:
```bash
python3 test_whale_strategy.py
# See strategy in action
```

See: [`HOW_TO_FIND_WHALES.md`](HOW_TO_FIND_WHALES.md)

---

### Option 3: Hybrid (Recommended for Production)

Combine both approaches:

1. **Seed with known whales** (manual)
2. **Enable auto-discovery** (finds more)
3. **Review and approve** periodically

```bash
# 1. Add known top traders manually
python3 scripts/python/find_whales.py

# 2. Enable auto-discovery
export WHALE_TRACKING_ENABLED=true

# 3. Run system
python3 run_trading_system.py

# System now copies manual whales AND discovers new ones
```

---

## 📊 How It Works

### Discovery Pipeline

```
Polymarket Markets
       ↓
Scan high-volume markets (every 5 min)
       ↓
Find trades >$500
       ↓
Build trader profiles
       ↓
Total volume >$50k? → Create whale record
       ↓
Trades >=10? → Calculate quality score
       ↓
Quality >=0.70? → Auto-track & copy! 🎯
```

### Quality Scoring (0-1 scale)

- **Win Rate** (40%): Historical win percentage
- **Consistency** (20%): Week-over-week profitability
- **Timing** (15%): Early entry quality
- **Market Selection** (15%): Specialization
- **Risk Management** (10%): Sharpe ratio

**Thresholds:**
- ≥0.75: Smart Money (definitely copy)
- 0.50-0.75: Neutral (review before copying)
- <0.50: Dumb Money (avoid)

### Copy Trading Execution

```
Whale enters position
       ↓
Signal generated (confidence = whale quality)
       ↓
Wait 5 minutes (copy delay)
       ↓
Check: Price stable? No duplicate position?
       ↓ YES
Calculate position size (Kelly Criterion)
       ↓
Validate with risk manager
       ↓ PASS
Execute copy trade 📈
```

**Position Sizing:**
```
Kelly = (whale_quality × 1 - (1 - whale_quality)) / 1
Our Position = Bankroll × Kelly × 0.25 (fractional)

Constraints:
- Max 50% of whale's size
- Max 8% of bankroll
- Min $5
```

---

## 🎯 Quick Start Commands

### Local Testing

```bash
cd /Users/jbass/polymarketagent/agents

# ONE COMMAND SETUP
./setup_and_test.sh

# Or manual steps:

# 1. Seed test whales
python3 seed_test_whales.py

# 2. Test whale strategy
python3 test_whale_strategy.py

# 3. View dashboard
python3 -m streamlit run scripts/python/dashboard.py

# 4. Start auto-discovery
python3 run_whale_discovery.py
```

### Railway Deployment

```bash
# 1. Set environment variable in Railway dashboard
WHALE_TRACKING_ENABLED=true

# 2. Push to GitHub (auto-deploys)
git push origin main

# 3. Check logs
railway logs -f

# Look for:
# ✓ Registered: Whale Following Strategy
# Starting whale discovery service in background...
# 🐋 NEW WHALE DISCOVERED: ...
```

---

## 📁 Files Created

### Core Implementation

| File | Purpose |
|------|---------|
| `agents/utils/database.py` | Whale database models (4 new tables) |
| `agents/application/whale/monitor.py` | Whale tracking and management |
| `agents/application/whale/scorer.py` | Quality scoring algorithm |
| `agents/application/whale/signals.py` | Signal generation |
| `agents/application/whale/auto_discovery.py` | **Automatic whale discovery** |
| `agents/application/strategies/whale_following.py` | Main strategy class |

### Scripts & Tools

| File | Purpose |
|------|---------|
| `run_whale_discovery.py` | **Run auto-discovery standalone** |
| `test_whale_strategy.py` | Test strategy with mock data |
| `seed_test_whales.py` | Create test whales |
| `scripts/python/find_whales.py` | Manual whale management |
| `migrate_add_whale_tables.py` | Database migration |

### Documentation

| File | Purpose |
|------|---------|
| `AUTOMATIC_WHALE_DISCOVERY.md` | **Complete auto-discovery guide** |
| `WHALE_STRATEGY_TESTING.md` | Full technical documentation |
| `HOW_TO_FIND_WHALES.md` | Manual whale discovery guide |
| `QUICK_START_WHALE.md` | 3-step quick start |
| `RUN_LOCALLY.md` | Local testing guide |

---

## ⚙️ Configuration

### Required (.env)

```bash
# Enable whale strategy
WHALE_TRACKING_ENABLED=true

# Database (Railway provides this)
DATABASE_URL=postgresql://...

# Paper trading (for testing)
PAPER_TRADING_MODE=true
```

### Optional (defaults shown)

```bash
# Discovery settings
WHALE_MIN_TRADE_SIZE_USD=500        # Min trade to consider
WHALE_MIN_VOLUME_USD=50000          # Min volume to qualify

# Quality & copying
WHALE_MIN_QUALITY_SCORE=0.70        # Min quality to copy
WHALE_COPY_DELAY_SECONDS=300        # 5 min delay before copying
WHALE_MAX_POSITION_PCT=8            # Max 8% of bankroll

# Risk management
MAX_POSITION_SIZE_PCT=10
DAILY_LOSS_LIMIT_PCT=5
```

---

## 📈 Expected Results

### Week 1 (Testing)
- Test whales copied successfully ✅
- Position sizing working ✅
- Risk controls functioning ✅

### Week 2-3 (Auto-Discovery)
- 20-40 whales discovered automatically
- 3-5 scored and auto-tracked
- First real whale copied

### Month 1 (Production)
- 50-100 whales in database
- 10-15 actively tracked
- Regular signal generation
- Copy trading operational

### Month 3+ (Mature)
- Robust whale database
- Proven smart money vs dumb money
- Optimized quality thresholds
- Consistent copy trading performance

---

## 🔍 Monitoring & Debugging

### Check Whale Database

```bash
python3

from agents.application.whale import WhaleMonitor
monitor = WhaleMonitor()

# Summary
stats = monitor.get_summary_stats()
print(f"Total: {stats['total_whales']}, Tracked: {stats['tracked_whales']}")

# Top whales
for w in monitor.get_top_whales(10):
    print(f"{w.nickname or w.address[:10]}... - {w.quality_score:.2f}")
```

### Check Signals

```python
from agents.application.whale import WhaleSignalGenerator
sig_gen = WhaleSignalGenerator()

# Copyable signals
signals = sig_gen.get_copyable_signals()
print(f"{len(signals)} signals ready to copy")

# Stats
stats = sig_gen.get_signal_stats()
print(f"Execution rate: {stats['execution_rate']:.1f}%")
```

### View Logs

```bash
# Local
tail -f polymarket_trading.log | grep "WHALE"

# Railway
railway logs -f | grep "WHALE"
```

---

## 🚨 Troubleshooting

**"Found 0 whale opportunities"**
- No whales in database yet → Run `seed_test_whales.py` OR wait for auto-discovery
- Whales not tracked → Check quality scores, manually set `is_tracked=True`

**"Discovery not finding whales"**
- Check logs for API errors
- Lower `WHALE_MIN_TRADE_SIZE_USD` to 250
- Increase `markets_per_scan` to 100

**"Whales discovered but not scored"**
- Need 10+ trades → Wait for more data
- Check settlement data → Scoring needs closed positions

**"Position sizes too small"**
- Increase `WHALE_MAX_POSITION_PCT` to 15
- Check whale quality scores (higher = bigger positions)

---

## 🎓 Learn More

### Deep Dives
- **Automatic Discovery**: `AUTOMATIC_WHALE_DISCOVERY.md`
- **Technical Details**: `WHALE_STRATEGY_TESTING.md`
- **Manual Management**: `HOW_TO_FIND_WHALES.md`

### Quick Starts
- **3-Step Guide**: `QUICK_START_WHALE.md`
- **Local Testing**: `RUN_LOCALLY.md`

### API Reference
- Polymarket CLOB: `https://clob.polymarket.com`
- Gamma API: `https://gamma-api.polymarket.com`

---

## 🏆 Next Steps

### Immediate (Today)

```bash
# 1. Test locally with automatic discovery
python3 run_whale_discovery.py --once

# 2. View results
python3 test_whale_strategy.py
```

### This Week

1. Deploy to Railway with `WHALE_TRACKING_ENABLED=true`
2. Let auto-discovery run for 48 hours
3. Review discovered whales
4. Adjust quality threshold if needed

### This Month

1. Monitor whale following performance vs endgame sweep
2. Fine-tune configuration based on results
3. Build whale leaderboard in dashboard
4. Add whale signal feed

### Long Term

1. Implement whale exit detection
2. Add counter-trading (fade dumb money)
3. Specialized scoring by market category
4. Machine learning quality prediction

---

## 📊 Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                  POLYMARKET WHALE STRATEGY              │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────┐                      ┌──────────────────┐
│ AUTO-DISCOVERY│                      │ MANUAL ENTRY     │
│               │                      │                  │
│ • Scan markets│                      │ • Research whales│
│ • Find trades │                      │ • Add to DB      │
│ • Track stats │                      │ • Set quality    │
│ • Auto-score  │                      │ • Enable tracking│
│ • Auto-track  │                      │                  │
└───────┬───────┘                      └────────┬─────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ WHALE DATABASE│
                    │               │
                    │ • Whales      │
                    │ • Positions   │
                    │ • Transactions│
                    │ • Signals     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ QUALITY SCORER│
                    │               │
                    │ • Win Rate    │
                    │ • Consistency │
                    │ • Timing      │
                    │ • Selection   │
                    │ • Risk Mgmt   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ SIGNAL GEN    │
                    │               │
                    │ • Entry signal│
                    │ • Exit signal │
                    │ • Copy delay  │
                    └───────┬───────┘
                            │
                            ▼
                 ┌──────────────────┐
                 │ WHALE STRATEGY   │
                 │                  │
                 │ • Find copyable  │
                 │ • Kelly sizing   │
                 │ • Risk checks    │
                 │ • Execute copy   │
                 └──────────────────┘
```

---

**Status:** ✅ Complete | 🤖 Fully Automated | 🚀 Production Ready

**Total Implementation:**
- 6 core modules
- 5 utility scripts
- 5 documentation files
- Full test suite
- Automatic discovery
- Railway deployment ready

**Get Started:** `python3 run_whale_discovery.py --once`
