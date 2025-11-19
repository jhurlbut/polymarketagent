"""
Trading strategies for Polymarket.

Available strategies:
- EndgameSweepStrategy: Trade near-certain outcomes close to settlement
- WhaleFollowingStrategy: Copy trades from high-quality whale traders
"""

from agents.application.strategies.endgame_sweep import EndgameSweepStrategy
from agents.application.strategies.whale_following import WhaleFollowingStrategy

__all__ = [
    "EndgameSweepStrategy",
    "WhaleFollowingStrategy",
]
