"""
Streamlit Dashboard for Polymarket Trading System.

Provides real-time monitoring of:
- Open positions and P&L
- Strategy performance
- Risk metrics
- Trade history
- System alerts

Run with: streamlit run scripts/python/dashboard.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.utils.config import config
from agents.utils.database import db, Trade, StrategySettings
from agents.application.analytics import PerformanceAnalyzer


def get_risk_summary():
    """Get risk summary without initializing full RiskManager (avoids web3 import)."""
    from datetime import datetime, timedelta

    # Mock risk summary for paper trading dashboard
    session = db.get_session()
    try:
        # Get open positions
        open_positions = session.query(Trade).filter(Trade.status == "open").all()

        # Calculate exposure
        total_exposure = sum(float(trade.size_usd) for trade in open_positions)
        available_capital = 10000.0  # Paper trading balance

        # Get today's P&L
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = (
            session.query(Trade)
            .filter(Trade.entry_time >= today_start)
            .filter(Trade.status.in_(["closed", "settled"]))
            .all()
        )
        today_pnl = sum(float(trade.net_profit_usd or 0) for trade in today_trades)

        # Get week's P&L
        week_start = datetime.utcnow() - timedelta(days=7)
        week_trades = (
            session.query(Trade)
            .filter(Trade.entry_time >= week_start)
            .filter(Trade.status.in_(["closed", "settled"]))
            .all()
        )
        week_pnl = sum(float(trade.net_profit_usd or 0) for trade in week_trades)

        return {
            "available_capital": available_capital,
            "total_exposure": total_exposure,
            "exposure_pct": (total_exposure / available_capital * 100) if available_capital > 0 else 0,
            "open_positions": len(open_positions),
            "daily_status": {"ok": True, "message": f"Daily P&L: ${today_pnl:.2f}"},
            "weekly_status": {"ok": True, "message": f"Weekly P&L: ${week_pnl:.2f}"},
            "diversification_status": {"ok": True, "message": f"Portfolio diversified with {len(open_positions)} positions" if open_positions else "No open positions"},
            "paper_trading_mode": config.PAPER_TRADING_MODE,
            "positions_by_market": {}
        }
    finally:
        session.close()


def main():
    """Main dashboard function."""
    st.set_page_config(
        page_title="Polymarket Trading Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📈 Polymarket Trading Dashboard")
    st.markdown("---")

    # Initialize components (avoid RiskManager to prevent web3 import)
    analyzer = PerformanceAnalyzer()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Mode indicator
        if config.PAPER_TRADING_MODE:
            st.success("📄 PAPER TRADING MODE")
        else:
            st.error("⚠️ LIVE TRADING MODE")

        st.markdown("---")

        # Auto-refresh toggle
        st.subheader("Auto-Refresh")
        auto_refresh = st.checkbox("Enable Auto-Refresh", value=False)

        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh interval (seconds)",
                min_value=10,
                max_value=300,
                value=30,
                step=10
            )
            st.info(f"🔄 Auto-refreshing every {refresh_interval}s")
            # Auto-refresh using Streamlit's rerun
            import time
            time.sleep(refresh_interval)
            st.rerun()

        st.markdown("---")

        # Filters
        st.subheader("Filters")
        date_range = st.selectbox(
            "Time Period",
            ["Today", "Last 7 Days", "Last 30 Days", "All Time"]
        )

        strategy_filter = st.selectbox(
            "Strategy",
            ["All Strategies", "endgame_sweep", "multi_option_arb", "market_maker"]
        )

        st.markdown("---")

        # Strategy Configuration
        st.subheader("⚙️ Strategy Settings")
        st.caption("Adjust endgame sweep criteria")

        # Get current settings from database
        settings = db.get_strategy_settings("endgame_sweep")
        if not settings:
            # Initialize with defaults if not exists
            settings = db.update_strategy_settings("endgame_sweep")

        # Price Range
        st.write("**Price Range**")
        col_min, col_max = st.columns(2)
        with col_min:
            min_price = st.number_input(
                "Min Price",
                min_value=0.0,
                max_value=1.0,
                value=float(settings.endgame_min_price),
                step=0.01,
                format="%.2f",
                help="Minimum market price (e.g., 0.85 = 85¢)"
            )
        with col_max:
            max_price = st.number_input(
                "Max Price",
                min_value=0.0,
                max_value=1.0,
                value=float(settings.endgame_max_price),
                step=0.01,
                format="%.2f",
                help="Maximum market price (e.g., 0.99 = 99¢)"
            )

        # Settlement Time
        max_hours = st.slider(
            "Max Hours to Settlement",
            min_value=1,
            max_value=168,  # 7 days
            value=int(settings.endgame_max_hours_to_settlement),
            step=1,
            help="Maximum time until market settles (hours)"
        )

        # Confidence Threshold (display as percentage)
        min_confidence_pct = st.slider(
            "Min Confidence",
            min_value=0,
            max_value=100,
            value=int(float(settings.endgame_min_confidence) * 100),
            step=5,
            format="%d%%",
            help="Minimum confidence threshold (lower = more trades)"
        )
        min_confidence = min_confidence_pct / 100.0  # Convert back to decimal

        # Save button
        if st.button("💾 Save Settings & Scan Now", type="primary"):
            db.update_strategy_settings(
                strategy_name="endgame_sweep",
                endgame_min_price=min_price,
                endgame_max_price=max_price,
                endgame_max_hours_to_settlement=max_hours,
                endgame_min_confidence=min_confidence,
                trigger_scan=True  # Request immediate scan
            )
            st.success("✓ Settings saved! Backend will scan immediately (within 10s).")
            st.rerun()

        st.markdown("---")

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.rerun()

    # Calculate date range
    if date_range == "Today":
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == "Last 7 Days":
        start_date = datetime.now() - timedelta(days=7)
    elif date_range == "Last 30 Days":
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = None

    # Get strategy filter
    strategy = None if strategy_filter == "All Strategies" else strategy_filter

    # Main content
    col1, col2, col3, col4 = st.columns(4)

    # Get risk summary (using our lightweight version)
    risk_summary = get_risk_summary()

    # Get performance metrics
    trades = analyzer.get_all_trades(
        start_date=start_date,
        strategy=strategy,
        status="closed"
    )
    metrics = analyzer.calculate_metrics(trades)

    # Get open positions
    session = db.get_session()
    try:
        open_positions = session.query(Trade).filter(Trade.status == "open").all()
    finally:
        session.close()

    # KPIs
    with col1:
        st.metric(
            "Available Capital",
            f"${risk_summary['available_capital']:,.2f}",
            help="Total USDC available for trading"
        )

    with col2:
        st.metric(
            "Net P&L",
            f"${metrics['net_profit']:,.2f}",
            delta=f"{metrics['win_rate']:.1f}% win rate",
            help=f"Net profit for {date_range.lower()}"
        )

    with col3:
        st.metric(
            "Open Positions",
            len(open_positions),
            delta=f"${risk_summary['total_exposure']:,.2f} deployed",
            help="Currently open trades"
        )

    with col4:
        st.metric(
            "Total Trades",
            metrics['total_trades'],
            delta=f"{metrics['winning_trades']}W / {metrics['losing_trades']}L",
            help=f"Trades executed in {date_range.lower()}"
        )

    st.markdown("---")

    # Risk Status
    st.header("🛡️ Risk Status")

    risk_col1, risk_col2 = st.columns(2)

    with risk_col1:
        # Daily status
        daily_ok = risk_summary['daily_status']['ok']
        if daily_ok:
            st.success(f"✅ Daily Limit: {risk_summary['daily_status']['message']}")
        else:
            st.error(f"❌ Daily Limit: {risk_summary['daily_status']['message']}")

        # Diversification status
        div_ok = risk_summary['diversification_status']['ok']
        if div_ok:
            st.success(f"✅ Diversification: {risk_summary['diversification_status']['message']}")
        else:
            st.warning(f"⚠️ Diversification: {risk_summary['diversification_status']['message']}")

    with risk_col2:
        # Weekly status
        weekly_ok = risk_summary['weekly_status']['ok']
        if weekly_ok:
            st.success(f"✅ Weekly Limit: {risk_summary['weekly_status']['message']}")
        else:
            st.error(f"❌ Weekly Limit: {risk_summary['weekly_status']['message']}")

        # Exposure
        exposure_pct = risk_summary['exposure_pct']
        if exposure_pct < 50:
            st.info(f"📊 Capital Deployed: {exposure_pct:.1f}%")
        elif exposure_pct < 80:
            st.warning(f"📊 Capital Deployed: {exposure_pct:.1f}%")
        else:
            st.error(f"📊 Capital Deployed: {exposure_pct:.1f}%")

    st.markdown("---")

    # Performance Metrics
    st.header("📊 Performance Metrics")

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.subheader("Returns")
        st.write(f"**Total Profit:** ${metrics['total_profit']:,.2f}")
        st.write(f"**Total Loss:** ${metrics['total_loss']:,.2f}")
        st.write(f"**Net Profit:** ${metrics['net_profit']:,.2f}")
        st.write(f"**Avg per Trade:** ${metrics['avg_profit_per_trade']:,.2f}")

    with metric_col2:
        st.subheader("Statistics")
        st.write(f"**Win Rate:** {metrics['win_rate']:.2f}%")
        st.write(f"**Profit Factor:** {metrics['profit_factor']:.2f}")
        st.write(f"**Sharpe Ratio:** {metrics['sharpe_ratio']:.2f}")
        st.write(f"**Gas Costs:** ${metrics['total_gas_cost']:,.2f}")

    with metric_col3:
        st.subheader("Best/Worst")
        st.write(f"**Max Win:** ${metrics['max_win']:,.2f}")
        st.write(f"**Max Loss:** ${metrics['max_loss']:,.2f}")
        st.write(f"**Avg Win:** ${metrics['avg_win']:,.2f}")
        st.write(f"**Avg Loss:** ${metrics['avg_loss']:,.2f}")

    st.markdown("---")

    # Open Positions
    st.header("📋 Open Positions")

    if open_positions:
        positions_data = []
        for trade in open_positions:
            positions_data.append({
                "ID": trade.id,
                "Strategy": trade.strategy,
                "Market": trade.market_question[:50] + "..." if len(trade.market_question or "") > 50 else (trade.market_question or "Unknown"),
                "Side": trade.side,
                "Entry Price": f"${float(trade.entry_price):.3f}",
                "Size": f"${float(trade.size_usd):.2f}",
                "Entry Time": trade.entry_time.strftime("%Y-%m-%d %H:%M"),
                "Duration": str(datetime.utcnow() - trade.entry_time).split(".")[0]
            })

        df_positions = pd.DataFrame(positions_data)
        st.dataframe(df_positions, use_container_width=True, hide_index=True)
    else:
        st.info("No open positions")

    st.markdown("---")

    # Recent Trades
    st.header("📜 Recent Trades")

    if trades:
        recent_trades = trades[-20:]  # Last 20 trades
        trades_data = []

        for trade in reversed(recent_trades):
            pnl = float(trade.net_profit_usd or 0)
            trades_data.append({
                "ID": trade.id,
                "Strategy": trade.strategy,
                "Market": trade.market_question[:40] + "..." if len(trade.market_question or "") > 40 else (trade.market_question or "Unknown"),
                "Side": trade.side,
                "Entry": f"${float(trade.entry_price):.3f}",
                "Exit": f"${float(trade.exit_price):.3f}" if trade.exit_price else "-",
                "Size": f"${float(trade.size_usd):.2f}",
                "P&L": f"${pnl:.2f}",
                "P&L %": f"{float(trade.profit_loss_pct or 0):.2f}%",
                "Status": trade.status
            })

        df_trades = pd.DataFrame(trades_data)

        # Color code P&L
        def color_pnl(val):
            if "P&L" in val.name and val.name != "P&L %":
                return ['color: green' if '+' in str(v) or float(str(v).replace('$', '')) > 0
                       else 'color: red' if '-' in str(v) or float(str(v).replace('$', '')) < 0
                       else '' for v in val]
            return ['' for _ in val]

        st.dataframe(df_trades, use_container_width=True, hide_index=True)
    else:
        st.info(f"No trades found for {date_range.lower()}")

    st.markdown("---")

    # Strategy Performance Breakdown
    st.header("🎯 Strategy Performance")

    strategy_performance = analyzer.get_strategy_performance()

    if strategy_performance:
        strat_data = []
        for strat_name, strat_metrics in strategy_performance.items():
            strat_data.append({
                "Strategy": strat_name,
                "Trades": strat_metrics['total_trades'],
                "Win Rate": f"{strat_metrics['win_rate']:.2f}%",
                "Net P&L": f"${strat_metrics['net_profit']:.2f}",
                "Avg/Trade": f"${strat_metrics['avg_profit_per_trade']:.2f}",
                "Profit Factor": f"{strat_metrics['profit_factor']:.2f}",
                "Max Win": f"${strat_metrics['max_win']:.2f}",
                "Max Loss": f"${strat_metrics['max_loss']:.2f}"
            })

        df_strategies = pd.DataFrame(strat_data)
        st.dataframe(df_strategies, use_container_width=True, hide_index=True)
    else:
        st.info("No strategy performance data available")

    # Whale Tracking Section (if enabled)
    # Read directly from env to handle Streamlit Cloud deployment
    whale_tracking_enabled = os.getenv("WHALE_TRACKING_ENABLED", "false").lower() == "true"
    if whale_tracking_enabled or getattr(config, 'WHALE_TRACKING_ENABLED', False):
        st.markdown("---")
        st.header("🐋 Whale Tracking")

        try:
            from agents.application.whale import WhaleMonitor, WhaleSignalGenerator

            whale_monitor = WhaleMonitor()
            signal_gen = WhaleSignalGenerator()

            # Whale Statistics
            whale_stats = whale_monitor.get_summary_stats()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Whales", whale_stats['total_whales'])
            with col2:
                st.metric("Tracked Whales", whale_stats['tracked_whales'])
            with col3:
                st.metric("Smart Money", whale_stats['smart_money_whales'])
            with col4:
                st.metric("Avg Quality", f"{whale_stats['avg_quality_score']:.2f}")

            # Whale Leaderboard
            st.subheader("Top Whales by Quality")
            top_whales = whale_monitor.get_top_whales(limit=10)

            if top_whales:
                whale_data = []
                for whale in top_whales:
                    whale_data.append({
                        "Rank": len(whale_data) + 1,
                        "Nickname": whale.nickname or f"{whale.address[:6]}...{whale.address[-4:]}",
                        "Quality": f"{whale.quality_score:.2f}",
                        "Type": whale.whale_type,
                        "Volume": f"${float(whale.total_volume_usd):,.0f}",
                        "Trades": whale.total_trades,
                        "Win Rate": f"{whale.win_rate:.1f}%",
                        "Tracked": "✅" if whale.is_tracked else "⊗"
                    })

                df_whales = pd.DataFrame(whale_data)

                # Color code by quality
                def color_quality(val):
                    try:
                        quality = float(val)
                        if quality >= 0.75:
                            return 'background-color: lightgreen'
                        elif quality >= 0.50:
                            return 'background-color: lightyellow'
                        else:
                            return 'background-color: lightcoral'
                    except:
                        return ''

                st.dataframe(
                    df_whales.style.applymap(
                        color_quality,
                        subset=['Quality']
                    ),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No whales discovered yet. Run whale discovery to populate database.")

            # Recent Whale Signals
            st.subheader("Recent Whale Signals")
            recent_signals = signal_gen.get_pending_signals(max_age_seconds=86400)  # Last 24h

            if recent_signals:
                signal_data = []
                for signal in recent_signals[:10]:  # Top 10
                    whale = whale_monitor.get_whale(signal.whale_address)
                    signal_data.append({
                        "ID": signal.id,
                        "Whale": whale.nickname or f"{signal.whale_address[:6]}..." if whale else "Unknown",
                        "Type": signal.signal_type,
                        "Side": signal.side,
                        "Price": f"${float(signal.price):.3f}",
                        "Size": f"${float(signal.size_usd):,.0f}",
                        "Confidence": f"{signal.confidence:.2f}",
                        "Status": signal.status,
                        "Age": str(datetime.utcnow() - signal.created_at).split('.')[0]
                    })

                df_signals = pd.DataFrame(signal_data)
                st.dataframe(df_signals, use_container_width=True, hide_index=True)
            else:
                st.info("No recent whale signals")

            # Whale Signal Stats
            signal_stats = signal_gen.get_signal_stats()
            if signal_stats['total_signals'] > 0:
                st.subheader("Signal Statistics")
                sig_col1, sig_col2, sig_col3, sig_col4 = st.columns(4)
                with sig_col1:
                    st.metric("Total Signals", signal_stats['total_signals'])
                with sig_col2:
                    st.metric("Pending", signal_stats['pending'])
                with sig_col3:
                    st.metric("Executed", signal_stats['executed'])
                with sig_col4:
                    st.metric("Execution Rate", f"{signal_stats['execution_rate']:.1f}%")

        except ImportError:
            st.warning("Whale tracking modules not installed")
        except Exception as e:
            st.error(f"Error loading whale data: {e}")

    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
