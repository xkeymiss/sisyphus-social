"""Social interaction models for follow, like, and comment."""

from datetime import datetime, timezone
from app.extensions import db


class Follow(db.Model):
    """User follow relationship model."""

    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    follower_handle = db.Column(db.String(64), nullable=False, index=True)
    followed_handle = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('follower_handle', 'followed_handle', name='uq_follow_pair'),
    )


class Like(db.Model):
    """Trade like model."""

    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trade_id = db.Column(db.String(36), db.ForeignKey('trades.id', ondelete='CASCADE'), nullable=False, index=True)
    user_handle = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('trade_id', 'user_handle', name='uq_trade_like'),
    )


class Comment(db.Model):
    """Trade comment model."""

    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trade_id = db.Column(db.String(36), db.ForeignKey('trades.id', ondelete='CASCADE'), nullable=False, index=True)
    author = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        from app.utils.time_utils import format_tr_datetime
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'author': self.author,
            'text': self.text,
            'time': format_tr_datetime(self.created_at) if self.created_at else 'Az önce'
        }
