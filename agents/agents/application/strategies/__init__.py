"""
Trading strategies for Polymarket.

Available strategies:
- EndgameSweepStrategy: Trade near-certain outcomes close to settlement
"""

from agents.application.strategies.endgame_sweep import EndgameSweepStrategy

__all__ = [
    "EndgameSweepStrategy",
]
