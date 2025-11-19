"""
Whale Tracking and Following Module.

This module provides functionality for identifying and tracking high-performing
"whale" traders on Polymarket, analyzing their trading patterns, and generating
copy-trading signals.

Components:
- monitor: Real-time whale transaction monitoring
- scorer: Whale quality scoring and classification
- signals: Copy-trading signal generation
- blockchain_monitor: Automated whale detection (placeholder - manual entry required)

Current Status:
- ✅ Whale tracking and quality scoring works
- ✅ Signal generation and copy trading works
- ⚠️ Automated whale discovery requires manual implementation
- → Use scripts/python/find_whales.py to add whales manually
"""

from agents.application.whale.monitor import WhaleMonitor
from agents.application.whale.scorer import WhaleScorer
from agents.application.whale.signals import WhaleSignalGenerator
from agents.application.whale.blockchain_monitor import BlockchainMonitor, PolymarketAPIMonitor

__all__ = [
    'WhaleMonitor',
    'WhaleScorer',
    'WhaleSignalGenerator',
    'BlockchainMonitor',
    'PolymarketAPIMonitor'
]
