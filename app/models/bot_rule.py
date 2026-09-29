"""Automated bot trading rule model."""

from datetime import datetime, timezone
from app.extensions import db


class BotRule(db.Model):
    """Bot rule database model."""

    __tablename__ = 'bot_rules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    symbol = db.Column(db.String(50), nullable=False, index=True)
    timeframe = db.Column(db.String(10), nullable=False, default='15m')
    strategy_key = db.Column(db.String(10), nullable=False, default='A')
    strategy_name = db.Column(db.String(100), nullable=False, default='Strateji A (Bollinger/POC)')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    backtest_pnl = db.Column(db.Float, nullable=False, default=0.0)
    win_rate = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('symbol', 'timeframe', name='uq_bot_rule_symbol_tf'),
    )

    def to_dict(self) -> dict:
        """Serialize rule model to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'strategy_key': self.strategy_key,
            'strategy_name': self.strategy_name,
            'is_active': self.is_active,
            'backtest_pnl': self.backtest_pnl,
            'win_rate': self.win_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<BotRule {self.symbol} {self.timeframe} -> {self.strategy_key}>"
