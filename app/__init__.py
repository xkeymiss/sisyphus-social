"""
Application factory.
"""

from typing import Optional
from flask import Flask, jsonify, request
from app.config import BaseConfig, get_config
from app.extensions import cors, db, migrate, login_manager


def create_app(config_class: Optional[type[BaseConfig]] = None) -> Flask:
    """Initialize and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )
    

    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    

    init_extensions(app)
    

    register_blueprints(app)
    

    register_error_handlers(app)


    @app.template_filter('format_crypto_price')
    def format_crypto_price(val):
        if val is None or val == '' or val == 0:
            return '0.00'
        try:
            num = float(val)
            abs_num = abs(num)
            if abs_num >= 100:
                return f"{num:,.2f}"
            elif abs_num >= 1:
                return f"{num:,.4f}"
            elif abs_num >= 0.01:
                formatted = f"{num:,.6f}"
                return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
            else:
                formatted = f"{num:,.8f}"
                return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
        except Exception:
            return str(val)


    init_database(app)
    
    return app


def init_extensions(app: Flask) -> None:
    """Initialize extensions."""
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}, r"/auth/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)


def register_blueprints(app: Flask) -> None:
    """Register blueprints."""
    from app.blueprints.core import core_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.market import market_bp
    from app.blueprints.backtest import backtest_bp
    from app.blueprints.social import social_bp
    from app.blueprints.bot import bot_bp
    
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(backtest_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(bot_bp)


def init_database(app: Flask) -> None:
    """Initialize database and default admin."""
    with app.app_context():
        try:
            db.create_all()
            from app.models.user import User
            admin_user = User.query.filter((User.username == 'utku') | (User.username == 'utku_quant') | (User.email == 'utku@hotmail.com')).first()
            if not admin_user:
                admin_user = User(
                    name='Utku',
                    username='utku',
                    email='utku@hotmail.com',
                    handle='@utku',
                    badge='👑 Sistem Yöneticisi & Trader',
                    role='admin',
                    is_active=True
                )
                admin_user.set_password('utku')
                db.session.add(admin_user)
                db.session.commit()
            else:
    
                admin_user.name = 'Utku'
                admin_user.username = 'utku'
                admin_user.email = 'utku@hotmail.com'
                admin_user.handle = '@utku'
                admin_user.badge = '👑 Sistem Yöneticisi & Trader'
                admin_user.role = 'admin'
                admin_user.set_password('utku')
                db.session.commit()


            from app.blueprints.backtest.routes import _ensure_data_loaded
            _ensure_data_loaded()
        except Exception as e:

            app.logger.info(f"Veritabanı başlatma notu: {e}")


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Geçersiz istek parametresi (Bad Request)'
            }), 400
        return 'Geçersiz İstek', 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': 'Bu işlem için lütfen oturum açınız (Unauthorized)'
            }), 401
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': 'İstenen kaynak bulunamadı (Not Found)'
            }), 404
        return 'Sayfa Bulunamadı', 404

    @app.errorhandler(500)
    def internal_server_error(error):
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            return jsonify({
                'status': 'error',
                'code': 500,
                'message': 'Sunucu içi beklenmeyen hata (Internal Server Error)'
            }), 500
        return 'Sunucu Hatası', 500
