"""
Flask extensions initialization.
"""

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# CORS extension
cors = CORS()

# Database ORM
db = SQLAlchemy()

# Session management
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bu sayfaya veya işleme erişmek için lütfen giriş yapınız.'
login_manager.login_message_category = 'info'

try:
    from flask_migrate import Migrate
    migrate = Migrate()
except ImportError:
    class DummyMigrate:
        def init_app(self, app, db=None):
            pass
    migrate = DummyMigrate()
