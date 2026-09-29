"""
Bot management and signal endpoints.
"""
from flask import jsonify, request, current_app
from flask_login import current_user
from app.blueprints.bot import bot_bp
from app.services.live_signal_engine import LiveSignalEngine
from app.blueprints.social.routes import social_service

# Singleton LiveSignalEngine örneği
live_signal_engine = LiveSignalEngine(social_service=social_service)


def _check_admin():
    """Verify admin privileges."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return False
    return True


@bot_bp.route('/status', methods=['GET'])
def get_bot_status():
    """Get bot status."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Bu alana erişim yetkiniz yok.'}), 403

    return jsonify({
        'status': 'success',
        'data': live_signal_engine.get_status()
    }), 200


@bot_bp.route('/available-symbols', methods=['GET'])
def get_available_symbols():
    """List available symbols."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    return jsonify({
        'status': 'success',
        'symbols': live_signal_engine.get_available_symbols()
    }), 200


@bot_bp.route('/coin-configs', methods=['GET', 'POST'])
def manage_coin_configs():
    """Manage coin configurations."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        coin_configs = payload.get('coin_configs', [])
        live_signal_engine.set_coin_configs(coin_configs)
        return jsonify({
            'status': 'success',
            'message': 'Konfigürasyon kaydedildi.',
            'coin_configs': live_signal_engine.get_coin_configs(),
            'rules': live_signal_engine.get_rules()
        }), 200

    return jsonify({
        'status': 'success',
        'coin_configs': live_signal_engine.get_coin_configs()
    }), 200


@bot_bp.route('/rules', methods=['GET', 'POST'])
def manage_rules():
    """Manage bot rules."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        rules = payload.get('rules', [])
        if isinstance(rules, list):
            live_signal_engine.rules = rules
            return jsonify({
                'status': 'success',
                'message': 'Kurallar başarıyla güncellendi.',
                'rules': live_signal_engine.get_rules()
            }), 200

    return jsonify({
        'status': 'success',
        'rules': live_signal_engine.get_rules()
    }), 200


@bot_bp.route('/rules/add', methods=['POST'])
def add_rule():
    """Add bot rule."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    payload = request.get_json(silent=True) or {}
    symbol = payload.get('symbol', 'BTC/USDT')
    timeframe = payload.get('timeframe', '15m')
    strat_key = payload.get('strategy_key', 'A')
    pnl = payload.get('backtest_pnl', 0.0)
    wr = payload.get('win_rate', 0.0)

    rule = live_signal_engine.add_rule(symbol, timeframe, strat_key, pnl, wr)
    return jsonify({
        'status': 'success',
        'message': f'{symbol} ({timeframe} — Strateji {strat_key}) kuralı eklendi.',
        'rule': rule
    }), 201


@bot_bp.route('/rules/<rule_id>/toggle', methods=['POST'])
def toggle_rule(rule_id):
    """Toggle rule active state."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    payload = request.get_json(silent=True) or {}
    is_active = payload.get('is_active', None)
    rule = live_signal_engine.toggle_rule(rule_id, is_active)
    if not rule:
        return jsonify({'status': 'error', 'message': 'Kural bulunamadı.'}), 404

    return jsonify({'status': 'success', 'rule': rule}), 200


@bot_bp.route('/rules/<rule_id>', methods=['DELETE', 'POST'])
def delete_rule(rule_id):
    """Delete rule."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    success = live_signal_engine.delete_rule(rule_id)
    return jsonify({'status': 'success' if success else 'error'}), 200 if success else 404


@bot_bp.route('/load-top-backtest', methods=['POST'])
def load_top_backtest():
    """Load top backtest rules."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    payload = request.get_json(silent=True) or {}
    limit = payload.get('limit', 15)
    rules = live_signal_engine.load_top_backtest_rules(limit=limit)

    return jsonify({
        'status': 'success',
        'message': f'En kârlı {len(rules)} backtest kuralı yüklendi.',
        'rules': rules
    }), 200


@bot_bp.route('/start', methods=['POST'])
def start_bot():
    """Start signal engine."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz işlem.'}), 403

    app = current_app._get_current_object()
    res = live_signal_engine.start(app=app)
    return jsonify(res), 200


@bot_bp.route('/stop', methods=['POST'])
def stop_bot():
    """Stop signal engine."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz işlem.'}), 403

    res = live_signal_engine.stop()
    return jsonify(res), 200


@bot_bp.route('/trades', methods=['GET'])
def get_bot_trades():
    """Get bot trades."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    return jsonify(live_signal_engine.get_trades()), 200


@bot_bp.route('/trades/<trade_id>/delete', methods=['POST', 'DELETE'])
def delete_bot_trade(trade_id):
    """Delete bot trade."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    success = live_signal_engine.delete_trade(trade_id)
    return jsonify({'status': 'success' if success else 'error'}), 200 if success else 404


@bot_bp.route('/test-signal', methods=['POST'])
def trigger_test_signal():
    """Trigger test signal."""
    if not _check_admin():
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz işlem.'}), 403

    payload = request.get_json(silent=True) or {}
    symbol = payload.get('symbol', 'BTC/USDT')
    side = payload.get('side', 'LONG')
    strat = payload.get('strategy_name', 'Strateji A (Bollinger/POC)')
    tf = payload.get('timeframe', '15m')

    res = live_signal_engine.trigger_test_signal(symbol=symbol, side=side, strategy_name=strat, timeframe=tf)
    return jsonify(res), 200
