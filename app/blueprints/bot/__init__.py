"""
Bot blueprint.
"""

from flask import Blueprint

bot_bp = Blueprint('bot', __name__, url_prefix='/api/bot')

from app.blueprints.bot import routes
