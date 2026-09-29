"""
Social trade feed and interaction routes.
"""

from flask import jsonify, request
from flask_login import current_user
from app.blueprints.social import social_bp
from app.services.social_service import SocialService

social_service = SocialService()


@social_bp.route('/trades', methods=['GET'])
@social_bp.route('/feed', methods=['GET'])
def get_trades():
    """Get social trades feed."""
    tab = request.args.get('tab', request.args.get('filter', 'latest'))
    

    user_handle = current_user.handle if current_user.is_authenticated else request.args.get('user', '@utku')
    
    trades = social_service.get_trades(filter_tab=tab, current_user_handle=user_handle)
    followed = social_service.get_followed_list(current_user_handle=user_handle)
    
    for t in trades:
        t['is_following'] = t.get('trader_handle') in followed
        t['is_mine'] = current_user.is_authenticated and (t.get('trader_handle') == current_user.handle)

    return jsonify({
        'status': 'success',
        'tab': tab,
        'count': len(trades),
        'trades': trades,
        'posts': trades,
        'followed_traders': followed,
        'current_user': current_user.to_dict() if current_user.is_authenticated else None
    }), 200


@social_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard rankings."""
    period = request.args.get('period', 'today').lower()
    if period not in ['today', 'week', 'all']:
        period = 'today'

    limit = int(request.args.get('limit', 10))
    top_trades = social_service.get_leaderboard(period=period, limit=limit)

    return jsonify({
        'status': 'success',
        'period': period,
        'count': len(top_trades),
        'leaderboard': top_trades
    }), 200


@social_bp.route('/trades/share', methods=['POST'])
@social_bp.route('/posts', methods=['POST'])
def share_trade():
    """Share a new trade."""
    if not current_user.is_authenticated:
        return jsonify({
            'status': 'error',
            'code': 401,
            'message': 'İşlem paylaşabilmek için lütfen oturum açınız.'
        }), 401

    payload = request.get_json() or {}
    
    new_trade = social_service.share_trade(
        trader_name=current_user.name,
        trader_handle=current_user.handle,
        symbol=payload.get('symbol', 'BTC/USDT'),
        side=payload.get('side', 'LONG'),
        leverage=payload.get('leverage', '10'),
        timeframe=payload.get('timeframe', '15m'),
        entry_price=float(payload.get('entry_price', 0.0)),
        target_tp=float(payload.get('target_tp', 0.0)),
        stop_loss=float(payload.get('stop_loss', 0.0)),
        strategy_name=payload.get('strategy_name', 'Manuel İşlem'),
        notes=payload.get('notes', ''),
        status=payload.get('status', 'ACTIVE')
    )
    new_trade['is_mine'] = True
    
    return jsonify({
        'status': 'success',
        'message': 'İşlem başarıyla paylaşıldı ve profilinize eklendi',
        'trade': new_trade,
        'post': new_trade
    }), 201


@social_bp.route('/trades/<trade_id>/update', methods=['POST', 'PUT'])
def update_trade(trade_id: str):
    """Update an existing trade."""
    if not current_user.is_authenticated:
        return jsonify({
            'status': 'error',
            'code': 401,
            'message': 'Bu işlem için oturum açmalısınız.'
        }), 401

    payload = request.get_json() or {}
    updated = social_service.update_trade(trade_id, payload)
    
    if not updated:
        return jsonify({'status': 'error', 'message': 'İşlem bulunamadı'}), 404
        
    return jsonify({
        'status': 'success',
        'message': 'İşlem başarıyla güncellendi',
        'trade': updated
    }), 200


@social_bp.route('/trades/<trade_id>/delete', methods=['POST', 'DELETE'])
def delete_trade(trade_id: str):
    """Delete an existing trade."""
    if not current_user.is_authenticated:
        return jsonify({
            'status': 'error',
            'code': 401,
            'message': 'Bu işlem için oturum açmalısınız.'
        }), 401

    success = social_service.delete_trade(trade_id)
    if not success:
        return jsonify({'status': 'error', 'message': 'İşlem bulunamadı'}), 404
        
    return jsonify({
        'status': 'success',
        'message': 'İşlem silindi'
    }), 200


@social_bp.route('/follow/toggle', methods=['POST'])
@social_bp.route('/trader/<string:handle>/follow', methods=['POST'])
def toggle_follow(handle=None):
    """Toggle follow state for a trader."""
    payload = request.get_json(silent=True) or {}
    target_handle = handle or payload.get('trader_handle') or payload.get('handle') or ''
    user_handle = current_user.handle if current_user.is_authenticated else '@utku'
    
    is_now_following = social_service.toggle_follow(target_handle, current_user_handle=user_handle)
    
    # Güncel takipçi sayısını hesapla
    from app.models.social import Follow
    from flask import has_app_context
    followers_count = Follow.query.filter_by(followed_handle=target_handle).count() if has_app_context() else 0

    return jsonify({
        'status': 'success',
        'trader_handle': target_handle,
        'is_following': is_now_following,
        'followers_count': followers_count
    }), 200


@social_bp.route('/trade/<trade_id>/like', methods=['POST'])
def like_trade(trade_id: str):
    """Toggle like state for a trade."""
    user_handle = current_user.handle if current_user.is_authenticated else '@utku'
    res = social_service.toggle_like(trade_id, user_handle=user_handle)
    return jsonify({
        'status': 'success',
        'trade_id': trade_id,
        'likes_count': res['likes_count'],
        'is_liked': res['is_liked']
    }), 200


@social_bp.route('/trade/<trade_id>/comment', methods=['POST'])
def add_trade_comment(trade_id: str):
    """Add comment to a trade."""
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'code': 401, 'message': 'Lütfen giriş yapınız.'}), 401

    payload = request.get_json() or {}
    author = current_user.name
    text = payload.get('text', '')
    
    comment = social_service.add_comment(trade_id, author, text)
    if not comment:
        return jsonify({'status': 'error', 'message': 'İşlem bulunamadı'}), 404
        
    return jsonify({
        'status': 'success',
        'comment': comment
    }), 201


@social_bp.route('/users/search', methods=['GET'])
def search_users():
    """Search users by username or handle."""
    q = request.args.get('q', '')
    results = social_service.search_traders(q)
    return jsonify({
        'status': 'success',
        'query': q,
        'count': len(results),
        'results': results
    }), 200


@social_bp.route('/users/<string:identifier>/profile', methods=['GET'])
def get_user_profile_api(identifier: str):
    """Get user profile details and performance stats."""
    user_handle = current_user.handle if current_user.is_authenticated else '@utku'
    profile_data = social_service.get_user_profile(identifier, current_user_handle=user_handle)
    if not profile_data:
        return jsonify({'status': 'error', 'message': 'Kullanıcı bulunamadı'}), 404
    return jsonify({
        'status': 'success',
        'profile': profile_data
    }), 200
