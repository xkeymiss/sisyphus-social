"""
Market blueprint.
"""

from flask import Blueprint

market_bp = Blueprint('market', __name__, url_prefix='/api/market')

from app.blueprints.market import routes  # noqa: E402, F401
