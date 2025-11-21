#!/bin/bash
# Local Deployment Setup Script
# Sets up everything needed to run the trading system locally

set -e

echo "============================================"
echo "Polymarket Trading System - Local Setup"
echo "============================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop:"
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo "✅ Docker detected"

# Check if Python 3.10+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION detected"

# Step 1: Start Postgres
echo ""
echo "Step 1: Starting PostgreSQL database..."
if docker ps -a | grep -q polymarket-postgres; then
    echo "Postgres container exists, starting..."
    docker start polymarket-postgres
else
    echo "Creating new Postgres container..."
    docker run -d \
      --name polymarket-postgres \
      -e POSTGRES_PASSWORD=local_dev_password \
      -e POSTGRES_DB=polymarket \
      -p 5432:5432 \
      postgres:17
fi
echo "✅ PostgreSQL running on localhost:5432"

# Wait for Postgres to be ready
echo "Waiting for Postgres to accept connections..."
for i in {1..10}; do
    if docker exec polymarket-postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ Postgres is ready"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo "❌ Postgres failed to start"
        exit 1
    fi
done

# Step 2: Create virtual environment
echo ""
echo "Step 2: Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate

# Step 3: Install dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r agents/requirements.txt
pip install --quiet -r requirements.txt
echo "✅ Dependencies installed"

# Step 4: Create .env file if it doesn't exist
echo ""
echo "Step 4: Configuring environment variables..."
if [ ! -f ".env" ]; then
    cat > .env <<'EOF'
# Database
DATABASE_URL=postgresql://postgres:local_dev_password@localhost:5432/polymarket

# Trading Mode
PAPER_TRADING_MODE=true

# Polymarket API (REQUIRED - get from Railway or generate new ones)
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_API_SECRET=your_api_secret_here
POLYMARKET_API_PASSPHRASE=your_api_passphrase_here

# AI APIs (REQUIRED - get from provider dashboards)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Features
WHALE_TRACKING_ENABLED=true

# Python Path
PYTHONPATH=$(pwd)/agents

# Environment
ENVIRONMENT=local
LOG_LEVEL=INFO
EOF
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - POLYMARKET_API_KEY"
    echo "   - POLYMARKET_API_SECRET"
    echo "   - POLYMARKET_API_PASSPHRASE"
    echo "   - ANTHROPIC_API_KEY (or OPENAI_API_KEY)"
    echo ""
    echo "   You can copy these from your Railway variables or generate new ones."
    echo ""
else
    echo "✅ .env file already exists"
fi

# Make sure .env is in .gitignore
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo "✅ Added .env to .gitignore"
fi

# Step 5: Initialize database
echo ""
echo "Step 5: Initializing database tables..."
set -a
source .env
set +a

python -c "from agents.utils.database import db; db.create_tables(); print('✅ Database tables created')" 2>/dev/null || echo "⚠️  Database initialization will happen on first run"

echo ""
echo "============================================"
echo "✅ Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file and add your API keys:"
echo "   nano .env"
echo ""
echo "2. Start the trading agent (Terminal 1):"
echo "   source venv/bin/activate"
echo "   export PYTHONPATH=$(pwd)/agents"
echo "   set -a && source .env && set +a"
echo "   cd agents && python run_continuous.py --interval 15"
echo ""
echo "3. Start the dashboard (Terminal 2):"
echo "   source venv/bin/activate"
echo "   set -a && source .env && set +a"
echo "   streamlit run agents/scripts/python/dashboard.py"
echo ""
echo "4. Access dashboard at: http://localhost:8501"
echo ""
echo "See LOCAL_DEPLOYMENT.md for full documentation."
echo ""
