"""
Backtest and scan results routes.
"""

import gzip
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from flask import jsonify, request, current_app
from app.blueprints.backtest import backtest_bp

# Proje kök dizini (Taşınabilir / Relatif)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCAN_JSON_FILENAME = 'sisyphus_scan_2026-03-23.json'
SCAN_GZ_FILENAME = 'sisyphus_scan_2026-03-23.json.gz'

# Bellek içi önbellek
_CACHED_DATA: Dict[str, List[Dict[str, Any]]] = {
    'results_a': [],
    'results_b': [],
    'results_c': [],
    'results_d': [],
    'results_e': []
}
_IS_LOADED = False


def _find_scan_json_path() -> Optional[Path]:
    """Resolve path to scan results file."""

    env_path = os.getenv('SCAN_DATA_PATH')
    if env_path and Path(env_path).exists():
        return Path(env_path)


    gz_local = PROJECT_ROOT / SCAN_GZ_FILENAME
    if gz_local.exists():
        return gz_local

    for p in PROJECT_ROOT.glob("sisyphus_scan*.json.gz"):
        if p.exists():
            return p


    json_local = PROJECT_ROOT / SCAN_JSON_FILENAME
    if json_local.exists():
        return json_local

    for p in PROJECT_ROOT.glob("sisyphus_scan*.json"):
        if p.exists() and p.suffix == '.json':
            return p


    static_data_dir = PROJECT_ROOT / 'app' / 'static' / 'data'
    if static_data_dir.exists():
        for p in static_data_dir.glob("sisyphus_scan*.json.gz"):
            if p.exists():
                return p
        for p in static_data_dir.glob("sisyphus_scan*.json"):
            if p.exists() and p.suffix == '.json':
                return p


    for p in Path.cwd().glob("sisyphus_scan*.json.gz"):
        if p.exists():
            return p
    for p in Path.cwd().glob("sisyphus_scan*.json"):
        if p.exists() and p.suffix == '.json':
            return p


    scanner_sibling = PROJECT_ROOT.parent / 'sisyphus-scanner'
    if scanner_sibling.exists():
        if (scanner_sibling / SCAN_GZ_FILENAME).exists():
            return scanner_sibling / SCAN_GZ_FILENAME
        if (scanner_sibling / SCAN_JSON_FILENAME).exists():
            return scanner_sibling / SCAN_JSON_FILENAME

    try:
        if current_app:
            app_parent = Path(current_app.root_path).parent
            if (app_parent / SCAN_GZ_FILENAME).exists():
                return app_parent / SCAN_GZ_FILENAME
            if (app_parent / SCAN_JSON_FILENAME).exists():
                return app_parent / SCAN_JSON_FILENAME
    except Exception:
        pass

    return None


def _ensure_data_loaded():
    """Load scan data into memory cache."""
    global _CACHED_DATA, _IS_LOADED
    if _IS_LOADED and _CACHED_DATA['results_a']:
        return

    target_path = _find_scan_json_path()

    if target_path and target_path.exists():
        try:
            print(f"[BILGI] Gercek tarama verisi yukleniyor: {target_path}...")
            if str(target_path).endswith('.gz'):
                with gzip.open(target_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(target_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            _CACHED_DATA['results_a'] = data.get('results_a', [])
            _CACHED_DATA['results_b'] = data.get('results_b', [])
            _CACHED_DATA['results_c'] = data.get('results_c', [])
            _CACHED_DATA['results_d'] = data.get('results_d', [])
            _CACHED_DATA['results_e'] = data.get('results_e', [])
            _IS_LOADED = True
            print(f"[BASARILI] {sum(len(v) for v in _CACHED_DATA.values())} adet gercek tarama sonucu yuklendi.")
        except Exception as e:
            print(f"[HATA] JSON dosyasi okunamadi: {e}")
    else:
        print(f"[UYARI] Tarama verisi ({SCAN_GZ_FILENAME} / {SCAN_JSON_FILENAME}) bulunamadi.")


@backtest_bp.route('/results', methods=['GET'])
def get_scan_results():
    """
    Strateji A, B, C, D, E'ye ait gerçek taranmış coin sonuçlarını döndürür.
    Performansı korumak için tablo özet listesini hızlıca döner.
    """
    _ensure_data_loaded()

    # Tablo görünümü için hafif özet veri listesi oluştur
    summary_results = {}
    for key in ['results_a', 'results_b', 'results_c', 'results_d', 'results_e']:
        items = _CACHED_DATA.get(key, [])
        summary_list = []
        for r in items:
            summary_list.append({
                'symbol': r.get('symbol', ''),
                'timeframe': r.get('timeframe', ''),
                'total_pnl_pct': r.get('total_pnl_pct', 0.0),
                'win_rate': r.get('win_rate', 0.0),
                'total_trades': r.get('total_trades', 0),
                'long_trades': r.get('long_trades', 0),
                'short_trades': r.get('short_trades', 0),
                'profit_factor': r.get('profit_factor', 0.0),
                'max_drawdown': r.get('max_drawdown', 0.0),
                'best_trade': r.get('best_trade', 0.0),
                'worst_trade': r.get('worst_trade', 0.0),
                'final_capital': r.get('final_capital', 1000.0)
            })
        summary_results[key] = summary_list

    return jsonify({
        'status': 'success',
        'results_a': summary_results['results_a'],
        'results_b': summary_results['results_b'],
        'results_c': summary_results['results_c'],
        'results_d': summary_results['results_d'],
        'results_e': summary_results['results_e'],
        'counts': {k: len(v) for k, v in summary_results.items()}
    }), 200


@backtest_bp.route('/details', methods=['GET'])
def get_coin_details():
    """
    Belirli bir coin, zaman dilimi ve stratejiye ait tam işlem geçmişini ve detayları döndürür.
    
    Query Params:
        strategy (str): 'A', 'B', 'C', 'D', 'E'
        symbol (str): Örn. 'BARD/USDT:USDT'
        timeframe (str): Örn. '2h'
    """
    _ensure_data_loaded()

    strategy = request.args.get('strategy', 'A').lower()
    symbol = request.args.get('symbol', '')
    timeframe = request.args.get('timeframe', '')

    key = f"results_{strategy}"
    items = _CACHED_DATA.get(key, [])

    found = None
    for r in items:
        if r.get('symbol') == symbol and r.get('timeframe') == timeframe:
            found = r
            break

    if not found:
        return jsonify({
            'status': 'error',
            'message': f'{symbol} ({timeframe}) Strateji {strategy.upper()} kaydı bulunamadı'
        }), 404

    # Trades ve equity curve verilerini hazırla
    trades = found.get('trades', [])
    equity_curve = []
    current_eq = 1000.0
    equity_curve.append({'timestamp': 'Başlangıç', 'equity': current_eq})
    for t in trades:
        current_eq += float(t.get('pnl_usd', 0.0))
        equity_curve.append({
            'timestamp': t.get('exit_time', t.get('entry_time', '')),
            'equity': round(current_eq, 2)
        })

    return jsonify({
        'status': 'success',
        'data': {
            'symbol': found.get('symbol'),
            'timeframe': found.get('timeframe'),
            'strategy': strategy.upper(),
            'total_pnl_pct': found.get('total_pnl_pct'),
            'win_rate': found.get('win_rate'),
            'total_trades': found.get('total_trades'),
            'long_trades': found.get('long_trades'),
            'short_trades': found.get('short_trades'),
            'profit_factor': found.get('profit_factor'),
            'max_drawdown': found.get('max_drawdown'),
            'best_trade': found.get('best_trade'),
            'worst_trade': found.get('worst_trade'),
            'final_capital': found.get('final_capital'),
            'trades': trades,
            'equity_curve': equity_curve
        }
    }), 200
