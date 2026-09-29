"""User authentication and profile model."""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    """User database model."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False, default='Trader')
    handle = db.Column(db.String(64), unique=True, nullable=False, default='@trader')
    badge = db.Column(db.String(64), nullable=False, default='Trader')
    role = db.Column(db.String(32), nullable=False, default='user')  # 'admin' | 'user'
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not getattr(self, 'handle', None) and getattr(self, 'username', None):
            self.handle = f"@{self.username}"

    def set_password(self, password: str) -> None:
        """Hash and set user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Girilen şifrenin kayıtlı hash ile eşleşmesini doğrular."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Kullanıcı nesnesini güvenli JSON sözlüğü formatına dönüştürür."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'handle': self.handle,
            'badge': self.badge,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email})>"


@login_manager.user_loader
def load_user(user_id: str) -> User:
    """Flask-Login oturum kullanıcısını ID üzerinden veritabanından yükler."""
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None
