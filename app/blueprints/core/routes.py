"""
Core application routes.
"""

from datetime import datetime, timezone
from flask import render_template, jsonify, redirect
from flask_login import current_user
from app.blueprints.core import core_bp
from app.services.social_service import SocialService

_social_service = SocialService()


@core_bp.route('/', methods=['GET'])
@core_bp.route('/islemsonuclari', methods=['GET'])
@core_bp.route('/sosyal', methods=['GET'])
def index():
    """Main dashboard view."""
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('index.html', current_user=current_user)



@core_bp.route('/profil', defaults={'username': None}, methods=['GET'])
@core_bp.route('/profil/<string:username>', methods=['GET'])
def profile(username=None):
    """User profile view."""
    if not current_user.is_authenticated:
        return redirect('/auth/login')

    current_handle = getattr(current_user, 'handle', '@utku')
    target_identifier = username or current_handle

    profile_data = _social_service.get_user_profile(target_identifier, current_user_handle=current_handle)
    if not profile_data:
        return redirect('/')

    return render_template('profile.html', profile=profile_data, current_user=current_user)


@core_bp.route('/sisyphusbot', methods=['GET'])
def sisyphusbot():
    """Bot management panel view (admin)."""
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    if current_user.role != 'admin':
        return redirect('/')
    return render_template('sisyphusbot.html', user=current_user)


@core_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'sisyphus-social',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200
