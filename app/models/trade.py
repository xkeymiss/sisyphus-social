"""Trade and position persistence model."""

from datetime import datetime, timezone
import uuid
from app.extensions import db


class Trade(db.Model):
    """Trades database model."""

    __tablename__ = 'trades'

    id = db.Column(db.String(36), primary_key=True, default=lambda: f"trade-{str(uuid.uuid4())[:8]}")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Trader Bilgileri
    trader_name = db.Column(db.String(100), nullable=False, default='Utku')
    trader_handle = db.Column(db.String(64), nullable=False, default='@utku')
    trader_badge = db.Column(db.String(100), nullable=False, default='👑 Sistem Yöneticisi & Trader')
    
    # İşlem Parametreleri
    symbol = db.Column(db.String(50), nullable=False, index=True)
    side = db.Column(db.String(10), nullable=False, default='LONG')  # 'LONG' | 'SHORT'
    leverage = db.Column(db.String(20), nullable=False, default='20x')
    timeframe = db.Column(db.String(10), nullable=False, default='15m')
    
    # Fiyat Seviyeleri
    entry_price = db.Column(db.Float, nullable=False, default=0.0)
    close_price = db.Column(db.Float, nullable=True)
    exit_price = db.Column(db.Float, nullable=True)
    target_tp = db.Column(db.Float, nullable=False, default=0.0)
    stop_loss = db.Column(db.Float, nullable=False, default=0.0)
    strategy_name = db.Column(db.String(100), nullable=False, default='Manuel İşlem')
    
    # Durum ve PnL
    status = db.Column(db.String(20), nullable=False, default='ACTIVE', index=True)  # 'ACTIVE', 'PENDING', 'TP_HIT', 'SL_HIT', 'CLOSED'
    status_label = db.Column(db.String(50), nullable=False, default='🟢 Aktif Pozisyon')
    current_pnl_pct = db.Column(db.Float, nullable=False, default=0.0)
    raw_pnl_pct = db.Column(db.Float, nullable=False, default=0.0)  # Kaldıraçsız saf fiyat kârı
    
    notes = db.Column(db.Text, nullable=False, default='')
    likes_count = db.Column(db.Integer, nullable=False, default=0)
    
    # Zaman Damgaları
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    closed_at = db.Column(db.DateTime, nullable=True, index=True)

    def to_dict(self) -> dict:
        """Serialize trade model to dictionary."""
        from app.utils.time_utils import format_tr_datetime
        
        created_display = format_tr_datetime(self.created_at) if self.created_at else 'Şimdi'
        closed_display = format_tr_datetime(self.closed_at) if self.closed_at else None

        return {
            'id': self.id,
            'user_id': self.user_id,
            'trader_name': self.trader_name,
            'trader_handle': self.trader_handle,
            'trader_badge': self.trader_badge,
            'created_at': created_display,
            'created_at_iso': self.created_at.isoformat() if self.created_at else None,
            'symbol': self.symbol,
            'side': self.side,
            'leverage': self.leverage,
            'timeframe': self.timeframe,
            'entry_price': self.entry_price,
            'close_price': self.close_price,
            'exit_price': self.exit_price or self.close_price,
            'target_tp': self.target_tp,
            'stop_loss': self.stop_loss,
            'strategy_name': self.strategy_name,
            'status': self.status,
            'status_label': self.status_label,
            'current_pnl_pct': self.current_pnl_pct,
            'raw_pnl_pct': self.raw_pnl_pct,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'closed_display': closed_display,
            'notes': self.notes,
            'likes_count': self.likes_count,
            'is_liked': False,
            'comments': []
        }

    def __repr__(self) -> str:
        return f"<Trade {self.id}: {self.symbol} {self.side} ({self.status})>"
