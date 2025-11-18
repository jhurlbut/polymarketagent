# Deployment Guide

## GitHub Repository

Your code is now live at: **https://github.com/jhurlbut/polymarketagent**

## Deploy Dashboard to Streamlit Cloud

### Option 1: Streamlit Cloud (Recommended)

Streamlit Cloud is the best option for deploying your Streamlit dashboard - it's free, easy, and designed specifically for Streamlit apps.

#### Steps:

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io
   - Click "Sign up" or "Sign in with GitHub"

2. **Connect Your Repository**
   - Click "New app"
   - Select your GitHub account: `jhurlbut`
   - Select repository: `polymarketagent`
   - Select branch: `main`
   - Main file path: `agents/scripts/python/dashboard.py`

3. **Configure Environment Variables** (Optional)
   - Click "Advanced settings"
   - Add any required environment variables if needed:
     - `ANTHROPIC_API_KEY` (if using live mode)
     - `OPENAI_API_KEY` (if using live mode)
     - `PAPER_TRADING_MODE=true` (recommended for public deployment)

4. **Deploy**
   - Click "Deploy!"
   - Your app will be live at: `https://[your-app-name].streamlit.app`

#### Notes:
- Free tier includes: 1 GB RAM, 1 app deployment
- Your database will need to be recreated on Streamlit Cloud (SQLite doesn't persist)
- For production with persistent data, consider using PostgreSQL (see below)

### Option 2: Vercel (Alternative - Not Recommended for Streamlit)

While you mentioned Vercel, it's not ideal for Streamlit apps. Vercel is designed for Next.js and static sites. If you want to use Vercel, you'd need to:
- Convert the dashboard to a React app, or
- Use a different Python framework like Flask/FastAPI

**Recommendation:** Stick with Streamlit Cloud for the dashboard.

---

## Running Locally

### Quick Start

```bash
cd /Users/jbass/polymarketagent/agents
source .venv/bin/activate

# Run single scan
python run_trading_system.py

# Run continuous (1-minute intervals)
python run_continuous.py --interval 1

# Launch dashboard
streamlit run scripts/python/dashboard.py
```

### Access Points
- Dashboard: http://localhost:8501
- Logs: `continuous_trading.log`, `polymarket_trading.log`

---

## Production Deployment Considerations

### Database

For production with persistent data storage:

1. **PostgreSQL (Recommended)**
   ```python
   # Update agents/utils/database.py
   # Change:
   db_url = f"sqlite:///{db_path}"
   # To:
   db_url = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
   ```

2. **Free PostgreSQL Options:**
   - Supabase: https://supabase.com (Free tier: 500MB)
   - Neon: https://neon.tech (Free tier: 3GB)
   - Railway: https://railway.app (Free tier: 1GB)

### Background Trading System

The continuous trading scanner needs to run separately from the dashboard:

**Option A: Cloud VM (Recommended)**
- DigitalOcean Droplet: $4/month
- AWS EC2 t2.micro: Free tier eligible
- Google Cloud Compute: Free tier eligible

Setup:
```bash
# Install dependencies
pip install -r requirements.txt

# Run continuous scanner with PM2 or systemd
pm2 start "python run_continuous.py --interval 15" --name polymarket-scanner

# Or use systemd service (Linux)
sudo systemctl enable polymarket-trading
sudo systemctl start polymarket-trading
```

**Option B: GitHub Actions (Limited)**
- Free for public repos
- Can run scheduled workflows
- Limited to 6 hour max runtime per job
- Good for periodic scans, not continuous

**Option C: Railway/Render (PaaS)**
- Railway: https://railway.app
- Render: https://render.com
- Both offer free tiers for background workers

### Architecture for Production

```
┌─────────────────────────────────────┐
│   Streamlit Cloud (Dashboard)       │
│   https://yourapp.streamlit.app     │
│   ├─ Real-time metrics              │
│   ├─ Trade history                  │
│   └─ Risk monitoring                │
└──────────────┬──────────────────────┘
               │
               │ Reads from
               ▼
┌─────────────────────────────────────┐
│   PostgreSQL Database (Supabase)    │
│   ├─ trades table                   │
│   ├─ market_snapshots table         │
│   ├─ performance_metrics table      │
│   └─ alerts table                   │
└──────────────▲──────────────────────┘
               │
               │ Writes to
               │
┌─────────────────────────────────────┐
│   Cloud VM (DigitalOcean/AWS)       │
│   Trading System + Scanner          │
│   ├─ run_continuous.py (24/7)       │
│   ├─ Scans markets every 15 min     │
│   ├─ Executes trades                │
│   └─ Updates database               │
└─────────────────────────────────────┘
```

### Cost Estimate (Production)

**Minimal Setup (Free):**
- Streamlit Cloud: Free (1 app)
- Supabase PostgreSQL: Free (500MB)
- GitHub Actions: Free (scheduled scans only)
- **Total: $0/month**

**Recommended Setup:**
- Streamlit Cloud: Free (1 app)
- Supabase PostgreSQL: Free (500MB)
- DigitalOcean Droplet: $4/month (continuous scanner)
- **Total: $4/month**

**Professional Setup:**
- Streamlit Cloud: Free or $20/month (more apps)
- Supabase Pro: $25/month (better performance)
- DigitalOcean Droplet: $12/month (2GB RAM)
- **Total: $37-57/month**

---

## Environment Variables for Deployment

When deploying to Streamlit Cloud or other platforms, set these environment variables:

### Required
```bash
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Recommended
```bash
PAPER_TRADING_MODE=true  # Always use paper trading for public deployments
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # For PostgreSQL
```

### Optional
```bash
MAX_POSITION_SIZE_PCT=10
DAILY_LOSS_LIMIT_PCT=5
WEEKLY_LOSS_LIMIT_PCT=10
ENDGAME_MIN_PRICE=0.95
ENDGAME_MAX_PRICE=0.99
ENDGAME_MAX_TIME_TO_SETTLEMENT_HOURS=24
```

---

## Security Considerations

### For Public Deployments:

1. **Never commit API keys or private keys**
   - Already protected by `.gitignore`
   - Use environment variables on deployment platform

2. **Use Paper Trading Mode**
   - Set `PAPER_TRADING_MODE=true` for public deployments
   - Only use live trading on private, secure infrastructure

3. **Database Access**
   - Use read-only credentials for dashboard if possible
   - Restrict write access to trading system only

4. **Rate Limiting**
   - Monitor API usage to avoid hitting rate limits
   - Implement backoff strategies

---

## Monitoring & Alerts

### Telegram Notifications (Optional)

1. Create Telegram bot: https://t.me/BotFather
2. Get your chat ID: https://t.me/userinfobot
3. Add to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

### Discord Webhooks (Optional)

1. Create webhook in Discord server settings
2. Add to `.env`:
   ```bash
   DISCORD_WEBHOOK_URL=your_webhook_url
   ```

---

## Next Steps

1. **Deploy Dashboard to Streamlit Cloud** (5 minutes)
   - Follow steps above
   - Test with paper trading mode

2. **Set up PostgreSQL** (if needed for production)
   - Create Supabase account
   - Create database
   - Update `DATABASE_URL` environment variable

3. **Deploy Trading System** (optional)
   - Set up cloud VM for continuous scanning
   - Configure systemd or PM2 for auto-restart
   - Monitor logs

4. **Test Everything**
   - Verify dashboard shows data
   - Check trades are being recorded
   - Monitor performance metrics

5. **Go Live** (when ready)
   - Switch to live trading mode (at your own risk)
   - Start with small position sizes
   - Monitor closely for first week

---

## Support & Documentation

- GitHub Repo: https://github.com/jhurlbut/polymarketagent
- Streamlit Docs: https://docs.streamlit.io
- Polymarket API: https://docs.polymarket.com

---

**Good luck with deployment! Start with paper trading and test thoroughly before going live. 🚀**
