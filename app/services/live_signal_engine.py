"""
Live signal engine and automated position tracking.
"""

import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import ccxt
import pandas as pd
from flask import has_app_context
from app.extensions import db
from app.models.bot_rule import BotRule
from app.models.trade import Trade
from app.services.indicator_service import IndicatorService
from app.services.social_service import SocialService


class LiveSignalEngine:
    """Live signal generation and automated position tracking engine."""

    # Binance USDT Vadeli İşlemler Kapsamlı Parite Listesi (250+ Coin)
    DEFAULT_ALL_SYMBOLS = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'DOGE/USDT', 'AVAX/USDT', 'BNB/USDT', 'SUI/USDT',
        'LINK/USDT', 'NEAR/USDT', 'ADA/USDT', 'PEPE/USDT', 'SHIB/USDT', 'APT/USDT', 'ARB/USDT', 'OP/USDT',
        'INJ/USDT', 'TIA/USDT', 'FET/USDT', 'RENDER/USDT', 'WIF/USDT', 'FLOKI/USDT', 'BONK/USDT', 'ORDI/USDT',
        'KAS/USDT', 'TAO/USDT', 'SEI/USDT', 'RUNE/USDT', 'AAVE/USDT', 'UNI/USDT', 'LTC/USDT', 'BCH/USDT',
        'ATOM/USDT', 'FTM/USDT', 'POL/USDT', 'DOT/USDT', 'ICP/USDT', 'GALA/USDT', 'ENA/USDT', 'PENDLE/USDT',
        'JUP/USDT', 'TON/USDT', 'PYTH/USDT', 'WLD/USDT', 'BLUR/USDT', 'STRK/USDT', 'DYDX/USDT', 'IMX/USDT',
        'STX/USDT', 'BEAM/USDT', 'AXS/USDT', 'SAND/USDT', 'MANA/USDT', 'ENS/USDT', 'CRV/USDT', 'SNX/USDT',
        'MKR/USDT', 'LDO/USDT', 'COMP/USDT', 'ALGO/USDT', 'HBAR/USDT', 'EOS/USDT', 'THETA/USDT', 'CHZ/USDT',
        'VET/USDT', 'FIL/USDT', 'TRX/USDT', 'XLM/USDT', 'ETC/USDT', 'ZEC/USDT', 'DASH/USDT', 'NEO/USDT',
        'IOTA/USDT', 'ZIL/USDT', 'BAT/USDT', 'ENJ/USDT', 'KAVA/USDT', 'BAND/USDT', '1INCH/USDT', 'GMX/USDT',
        'CFX/USDT', 'ID/USDT', 'MAV/USDT', 'CYBER/USDT', 'ARK/USDT', 'BIGTIME/USDT', 'MEME/USDT', 'JTO/USDT',
        '1000SATS/USDT', 'NFP/USDT', 'AI/USDT', 'XAI/USDT', 'MANTA/USDT', 'ONDO/USDT', 'ALT/USDT', 'DYM/USDT',
        'PIXEL/USDT', 'PORTAL/USDT', 'AEVO/USDT', 'METIS/USDT', 'BOME/USDT', 'ETHFI/USDT', 'W/USDT', 'TNSR/USDT',
        'SAGA/USDT', 'OMNI/USDT', 'REZ/USDT', 'BB/USDT', 'NOT/USDT', 'IO/USDT', 'ZK/USDT', 'LISTA/USDT',
        'BLAST/USDT', 'DOGS/USDT', 'NEIRO/USDT', 'TURBO/USDT', 'CATI/USDT', 'HMSTR/USDT', 'EIGEN/USDT', 'SCR/USDT',
        'GRASS/USDT', 'PNUT/USDT', 'ACT/USDT', 'HIPPO/USDT', 'ME/USDT', 'MOVE/USDT', 'VIRTUAL/USDT', 'PENGU/USDT'
    ]

    STRATEGY_NAMES = {
        'A': 'Strateji A (Bollinger/POC)',
        'B': 'Strateji B (Aks. SL/TP)',
        'C': 'Strateji C (Rahat Sisyphus)',
        'D': 'Strateji D (Momentum EMA)',
        'E': 'Strateji E (Mean Reversion)'
    }

    TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h']

    def __init__(self, social_service: Optional[SocialService] = None):
        self.social_service = social_service or SocialService()
        self.is_running = False
        
        # Aktif İzleme Kuralları (List of Rule Objects)
        self.rules: List[Dict[str, Any]] = []
        self._init_default_rules()

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._exchange = None
        
        # Bot işlem havuzu
        self.tracked_trades: List[Dict[str, Any]] = []
        self.last_scan_time: Optional[str] = None
        self.total_signals_generated: int = 0
        self.scan_count: int = 0

        # Sosyal akıştan gelen güncellemeleri dinle
        if self.social_service:
            self.social_service.register_update_listener(self._on_social_trade_updated)

    def _on_social_trade_updated(self, trade_id: str, updates: Dict[str, Any], trade_data: Dict[str, Any]) -> None:
        """Sosyal akıştan bir işlem düzenlendiğinde / kapatıldığında bot havuzunu da günceller."""
        for t in self.tracked_trades:
            if t['id'] == trade_id:
                if 'status' in updates:
                    t['status'] = updates['status'].upper()
                    t['status_label'] = trade_data.get('status_label', t['status'])
                
                close_p = trade_data.get('close_price') or updates.get('close_price')
                if close_p:
                    t['close_price'] = float(close_p)
                    t['exit_price'] = float(close_p)
                elif 'target_tp' in updates and updates['target_tp']:
                    t['close_price'] = float(updates['target_tp'])
                    t['exit_price'] = float(updates['target_tp'])

                if trade_data.get('current_pnl_pct') is not None:
                    t['current_pnl_pct'] = trade_data.get('current_pnl_pct')
                if trade_data.get('closed_at'):
                    from app.utils.time_utils import format_tr_now
                    t['closed_at'] = trade_data.get('closed_display', format_tr_now())

    def _init_default_rules(self) -> None:
        """Varsayılan olarak veritabanındaki kuralları yükler, yoksa boş başlar."""
        if has_app_context():
            try:
                db_rules = BotRule.query.all()
                if db_rules:
                    self.rules = [
                        {
                            'id': f"rule-{r.id}",
                            'symbol': r.symbol,
                            'timeframe': r.timeframe,
                            'strategy_key': r.strategy_key,
                            'strategy_name': r.strategy_name,
                            'is_active': r.is_active,
                            'backtest_pnl': r.backtest_pnl,
                            'win_rate': r.win_rate
                        }
                        for r in db_rules
                    ]
                    return
            except Exception:
                pass
        self.rules = []

    def get_exchange(self):
        """Binance Futures exchange örneği."""
        if self._exchange is None:
            self._exchange = ccxt.binanceusdm({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
        return self._exchange

    def get_available_symbols(self) -> List[str]:
        """Tüm güncel Binance USDT vadeli işlem sembollerini dinamik olarak çeker."""
        if hasattr(self, '_cached_symbols') and self._cached_symbols and (time.time() - getattr(self, '_symbols_cache_time', 0)) < 3600:
            return self._cached_symbols

        try:
            exchange = self.get_exchange()
            exchange.load_markets()
            symbols = []
            for sym, market in exchange.markets.items():
                if (market.get('swap', False) and
                    market.get('active', False) and
                    market.get('quote') == 'USDT' and
                    market.get('linear', False)):
                    clean_sym = market['symbol'].split(':')[0]
                    symbols.append(clean_sym)
            symbols = sorted(list(set(symbols)))
            if symbols:
                self._cached_symbols = symbols
                self._symbols_cache_time = time.time()
                return symbols
        except Exception:
            pass

        return self.DEFAULT_ALL_SYMBOLS

    def get_rules(self) -> List[Dict[str, Any]]:
        """Mevcut bot kurallarını döndürür."""
        if not self.rules and has_app_context():
            self._init_default_rules()
        return self.rules

    def get_coin_configs(self) -> List[Dict[str, Any]]:
        """Kuralları coin bazında gruplanmış yapıya dönüştürür."""
        if not self.rules and has_app_context():
            self._init_default_rules()

        coin_map: Dict[str, Dict[str, Any]] = {}
        for r in self.rules:
            sym = r['symbol']
            if sym not in coin_map:
                coin_map[sym] = {
                    'coin': sym,
                    'timeframe_strategies': {},
                    'backtest_info': {}
                }
            tf = r['timeframe']
            strat = r['strategy_key']
            coin_map[sym]['timeframe_strategies'][tf] = strat
            if r.get('backtest_pnl'):
                coin_map[sym]['backtest_info'][f"{tf}_{strat}"] = {
                    'pnl': r.get('backtest_pnl', 0.0),
                    'win_rate': r.get('win_rate', 0.0)
                }
        return list(coin_map.values())

    def set_coin_configs(self, coin_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Coin bazlı konfigürasyonu kurallara dönüştürüp veritabanına kaydeder."""
        new_rules = []
        for cfg in coin_configs:
            sym = cfg.get('coin', '').strip().upper()
            if not sym.endswith('/USDT'):
                sym = f"{sym}/USDT"
            tf_strats = cfg.get('timeframe_strategies', {})
            for tf, strat_key in tf_strats.items():
                if tf in self.TIMEFRAMES and strat_key in self.STRATEGY_NAMES:
                    new_rules.append({
                        'id': f"rule-{str(uuid.uuid4())[:6]}",
                        'symbol': sym,
                        'timeframe': tf,
                        'strategy_key': strat_key,
                        'strategy_name': self.STRATEGY_NAMES.get(strat_key, f'Strateji {strat_key}'),
                        'is_active': True,
                        'backtest_pnl': 0.0,
                        'win_rate': 0.0
                    })
        self.rules = new_rules

        if has_app_context():
            try:
                BotRule.query.delete()
                for r in self.rules:
                    db_rule = BotRule(
                        symbol=r['symbol'],
                        timeframe=r['timeframe'],
                        strategy_key=r['strategy_key'],
                        strategy_name=r['strategy_name'],
                        is_active=r.get('is_active', True),
                        backtest_pnl=r.get('backtest_pnl', 0.0),
                        win_rate=r.get('win_rate', 0.0)
                    )
                    db.session.add(db_rule)
                db.session.commit()
            except Exception:
                db.session.rollback()

        return self.rules

    def add_rule(self, symbol: str, timeframe: str, strategy_key: str, pnl: float = 0.0, win_rate: float = 0.0) -> Dict[str, Any]:
        """Yeni bir tarama kuralı ekler ve veritabanına işler."""
        strat_key = strategy_key.upper()
        clean_sym = symbol.strip().upper()
        if not clean_sym.endswith('/USDT'):
            clean_sym = f"{clean_sym}/USDT"

        rule = {
            'id': f"rule-{str(uuid.uuid4())[:6]}",
            'symbol': clean_sym,
            'timeframe': timeframe if timeframe in self.TIMEFRAMES else '15m',
            'strategy_key': strat_key if strat_key in self.STRATEGY_NAMES else 'A',
            'strategy_name': self.STRATEGY_NAMES.get(strat_key, f'Strateji {strat_key}'),
            'is_active': True,
            'backtest_pnl': float(pnl),
            'win_rate': float(win_rate)
        }
        self.rules.insert(0, rule)

        if has_app_context():
            try:
                db_rule = BotRule(
                    symbol=rule['symbol'],
                    timeframe=rule['timeframe'],
                    strategy_key=rule['strategy_key'],
                    strategy_name=rule['strategy_name'],
                    is_active=rule['is_active'],
                    backtest_pnl=rule['backtest_pnl'],
                    win_rate=rule['win_rate']
                )
                db.session.add(db_rule)
                db.session.commit()
                rule['id'] = f"rule-{db_rule.id}"
            except Exception:
                db.session.rollback()

        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """Kuralı siler."""
        initial_len = len(self.rules)
        self.rules = [r for r in self.rules if r['id'] != rule_id]

        if has_app_context():
            try:
                numeric_id = rule_id.replace('rule-', '')
                if numeric_id.isdigit():
                    db_rule = BotRule.query.get(int(numeric_id))
                    if db_rule:
                        db.session.delete(db_rule)
                        db.session.commit()
            except Exception:
                db.session.rollback()

        return len(self.rules) < initial_len

    def toggle_rule(self, rule_id: str, is_active: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """Kuralın aktiflik durumunu açar/kapatır."""
        for r in self.rules:
            if r['id'] == rule_id:
                if is_active is None:
                    r['is_active'] = not r['is_active']
                else:
                    r['is_active'] = bool(is_active)

                if has_app_context():
                    try:
                        numeric_id = rule_id.replace('rule-', '')
                        if numeric_id.isdigit():
                            db_rule = BotRule.query.get(int(numeric_id))
                            if db_rule:
                                db_rule.is_active = r['is_active']
                                db.session.commit()
                    except Exception:
                        db.session.rollback()

                return r
        return None

    def load_top_backtest_rules(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Backtest verisindeki en kârlı sonuçları kurallara yükler."""
        from app.blueprints.backtest.routes import _CACHED_DATA, _ensure_data_loaded
        _ensure_data_loaded()

        all_results = []
        for strat_key, key_name in [('A', 'results_a'), ('B', 'results_b'), ('C', 'results_c'), ('D', 'results_d'), ('E', 'results_e')]:
            for item in _CACHED_DATA.get(key_name, []):
                sym = item.get('symbol', '').replace(':USDT', '')
                if sym.endswith('/USDT'):
                    all_results.append({
                        'symbol': sym,
                        'timeframe': item.get('timeframe', '15m'),
                        'strategy_key': strat_key,
                        'strategy_name': self.STRATEGY_NAMES.get(strat_key, f'Strateji {strat_key}'),
                        'backtest_pnl': float(item.get('total_pnl_pct', 0.0)),
                        'win_rate': float(item.get('win_rate', 0.0))
                    })

        # Kâra göre sırala ve benzersiz coin-tf-strat kombinasyonlarını al
        all_results.sort(key=lambda x: x['backtest_pnl'], reverse=True)
        
        seen = set()
        new_rules = []
        for item in all_results:
            key = (item['symbol'], item['timeframe'], item['strategy_key'])
            if key not in seen:
                seen.add(key)
                new_rules.append({
                    'id': f"rule-{str(uuid.uuid4())[:6]}",
                    'symbol': item['symbol'],
                    'timeframe': item['timeframe'],
                    'strategy_key': item['strategy_key'],
                    'strategy_name': item['strategy_name'],
                    'is_active': True,
                    'backtest_pnl': item['backtest_pnl'],
                    'win_rate': item['win_rate']
                })
                if len(new_rules) >= limit:
                    break

        if new_rules:
            self.rules = new_rules

        return self.rules

    def start(self, app=None) -> Dict[str, Any]:
        """Botu başlatır."""
        if self.is_running:
            return {'status': 'already_running', 'message': 'Bot zaten çalışıyor.'}

        active_rules = [r for r in self.rules if r.get('is_active', True)]
        if not active_rules:
            return {'status': 'error', 'message': 'Lütfen en az bir aktif kural belirleyiniz.'}

        self._app_ref = app
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, args=(app,), daemon=True)
        self._thread.start()

        return {
            'status': 'started',
            'is_running': True,
            'rules_count': len(active_rules),
            'message': f'Sisyphus Bot başlatıldı. ({len(active_rules)} aktif kural izleniyor - 20x Kaldıraç)'
        }

    def stop(self) -> Dict[str, Any]:
        """Botu durdurur."""
        if not self.is_running:
            return {'status': 'not_running', 'message': 'Bot şu an çalışmıyor.'}

        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

        return {
            'status': 'stopped',
            'is_running': False,
            'message': 'Sisyphus Bot güvenli bir şekilde durduruldu.'
        }

    def _sync_trades_from_db(self) -> None:
        """Veritabanındaki güncel bot işlemlerini hafıza ile tam senkronize eder."""
        if has_app_context():
            try:
                bot_db_trades = Trade.query.filter(
                    (Trade.notes.ilike('%Sisyphus Bot%')) |
                    (Trade.strategy_name.ilike('Strateji %')) |
                    (Trade.trader_name.ilike('Sisyphus Bot'))
                ).order_by(Trade.created_at.desc()).all()
                
                db_trades_list = [t.to_dict() for t in bot_db_trades]
                if db_trades_list:
                    # Mevcut hafıza ile birleştir
                    db_map = {t['id']: t for t in db_trades_list}
                    # Hafızadaki silinmemişleri koru, yenileri ekle
                    merged = []
                    seen_ids = set()
                    for t in self.tracked_trades:
                        if t['id'] in db_map:
                            # DB'deki güncel durumu koru
                            db_t = db_map[t['id']]
                            t['status'] = db_t.get('status', t.get('status'))
                            t['status_label'] = db_t.get('status_label', t.get('status_label'))
                            merged.append(t)
                            seen_ids.add(t['id'])
                        else:
                            merged.append(t)
                            seen_ids.add(t['id'])
                    
                    for t_dict in db_trades_list:
                        if t_dict['id'] not in seen_ids:
                            merged.append(t_dict)
                            seen_ids.add(t_dict['id'])
                    
                    self.tracked_trades = merged
            except Exception:
                pass

    def get_status(self) -> Dict[str, Any]:
        """Botun anlık durumunu, sayaçlarını ve kurallarını döndürür."""
        self._sync_trades_from_db()
        active_rules = [r for r in self.rules if r.get('is_active', True)]
        active_trades = [t for t in self.tracked_trades if t.get('status') == 'ACTIVE']
        completed_trades = [t for t in self.tracked_trades if t.get('status') != 'ACTIVE']

        return {
            'is_running': self.is_running,
            'rules': self.rules,
            'active_rules_count': len(active_rules),
            'total_rules_count': len(self.rules),
            'available_symbols_count': len(self.DEFAULT_ALL_SYMBOLS),
            'active_trades_count': len(active_trades),
            'completed_trades_count': len(completed_trades),
            'total_signals_generated': self.total_signals_generated,
            'last_scan_time': self.last_scan_time,
            'scan_count': self.scan_count
        }

    def get_trades(self) -> Dict[str, Any]:
        """Yalnızca otomatik tarama botunun açıp kapattığı işlemleri döndürür."""
        self._sync_trades_from_db()

        # Bot harici manuel kullanıcı işlemlerini bot tablosundan ayıkla
        bot_only_trades = [
            t for t in self.tracked_trades
            if 'Sisyphus Bot' in str(t.get('notes', '')) or
               str(t.get('strategy_name', '')).startswith('Strateji ') or
               str(t.get('trader_name', '')).lower() == 'sisyphus bot'
        ]
        self.tracked_trades = bot_only_trades

        for t in self.tracked_trades:
            if t.get('status') == 'ACTIVE':
                t['current_price'] = self._fetch_ticker_price(t['symbol']) or t.get('current_price') or t['entry_price']
            else:
                if not t.get('close_price') and t.get('exit_price'):
                    t['close_price'] = t['exit_price']
                elif not t.get('close_price') and t.get('current_price'):
                    t['close_price'] = t['current_price']
                if not t.get('exit_price') and t.get('close_price'):
                    t['exit_price'] = t['close_price']

        return {
            'status': 'success',
            'trades': self.tracked_trades,
            'active_trades': [t for t in self.tracked_trades if t.get('status') == 'ACTIVE'],
            'completed_trades': [t for t in self.tracked_trades if t.get('status') != 'ACTIVE']
        }

    def delete_trade(self, trade_id: str) -> bool:
        """Bot işlem havuzundan ve sosyal akıştan işlemi tamamen kaldırır."""
        initial_len = len(self.tracked_trades)
        self.tracked_trades = [t for t in self.tracked_trades if t['id'] != trade_id]
        if self.social_service:
            self.social_service.delete_trade(trade_id)
        return len(self.tracked_trades) < initial_len

    def trigger_test_signal(self, symbol: str = 'BTC/USDT', side: str = 'LONG', strategy_name: str = 'Strateji A (Bollinger/POC)', timeframe: str = '15m') -> Dict[str, Any]:
        """Test sinyali oluşturur."""
        current_price = self._fetch_ticker_price(symbol) or (96500.0 if 'BTC' in symbol else 200.0)
        
        trade = self._create_and_share_trade(
            symbol=symbol,
            side=side.upper(),
            strategy_name=strategy_name,
            timeframe=timeframe,
            entry_price=current_price
        )
        return {'status': 'success', 'message': f'{symbol} ({timeframe}) için {side} sinyali oluşturuldu!', 'trade': trade}

    def _worker_loop(self, app=None) -> None:
        """Arka plan periyodik kural tarama döngüsü."""
        app_to_use = app or getattr(self, '_app_ref', None)
        if app_to_use is None:
            try:
                from app import create_app
                app_to_use = create_app()
                self._app_ref = app_to_use
            except Exception:
                pass

        while not self._stop_event.is_set():
            try:
                if app_to_use:
                    with app_to_use.app_context():
                        self._do_scan_cycle()
                else:
                    self._do_scan_cycle()
            except Exception as e:
                time.sleep(1.0)

            # Tarama periyodu beklemesi (varsayılan 4 sn)
            time.sleep(4.0)

    def _do_scan_cycle(self) -> None:
        """Tek bir periyodik tarama adımı gerçekleştirir."""
        from app.utils.time_utils import format_tr_time_only
        self.scan_count += 1
        self.last_scan_time = format_tr_time_only()

        active_rules = [r for r in self.rules if r.get('is_active', True)]
        for rule in active_rules:
            if self._stop_event.is_set():
                break
            self._scan_rule(rule)
            time.sleep(0.2)

        self._update_open_positions()

    def _scan_rule(self, rule: Dict[str, Any]) -> None:
        """Belirtilen kural için Binance Futures OHLCV mumlarını çekip indikatör stratejisini test eder."""
        symbol = rule.get('symbol')
        timeframe = rule.get('timeframe', '15m')
        strategy_key = rule.get('strategy_key', 'A')

        if not symbol:
            return

        # Aynı paritede halihazırda aktif pozisyon varsa yeni sinyal açma
        has_active = any(t['symbol'] == symbol and t.get('status') == 'ACTIVE' for t in self.tracked_trades)
        if has_active:
            return

        df = self._fetch_recent_ohlcv(symbol, timeframe=timeframe, limit=60)
        if df is None or len(df) < 30:
            return

        signal = self._evaluate_strategy(df, strategy_key)
        if signal:
            side, price = signal
            strategy_name = self.STRATEGY_NAMES.get(strategy_key, f'Strateji {strategy_key}')
            self._create_and_share_trade(
                symbol=symbol,
                side=side,
                strategy_name=strategy_name,
                timeframe=timeframe,
                entry_price=price
            )

    def _evaluate_strategy(self, df: pd.DataFrame, strategy_key: str) -> Optional[Tuple[str, float]]:
        """Gerçek indikatörler ile strateji alım/satım sinyali üretir."""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        last_close = float(last_row['close'])

        if strategy_key == 'A':
            # Strateji A: Bollinger Bantları Kırılımı & Trend Sinyali
            basis, upper, lower = IndicatorService.bollinger_bands(df['close'], period=20, std_dev=1.0)
            if len(upper) < 2 or pd.isna(upper.iloc[-1]):
                return None
            
            if prev_row['close'] <= lower.iloc[-2] and last_close > lower.iloc[-1]:
                return ('LONG', last_close)
            elif prev_row['close'] >= upper.iloc[-2] and last_close < upper.iloc[-1]:
                return ('SHORT', last_close)

        elif strategy_key == 'B':
            # Strateji B: RSI Aşırı Alım/Satım & Dönüş
            rsi_series = IndicatorService.rsi(df['close'], period=14)
            if len(rsi_series) < 2 or pd.isna(rsi_series.iloc[-1]):
                return None
            last_rsi = float(rsi_series.iloc[-1])
            prev_rsi = float(rsi_series.iloc[-2])

            if prev_rsi <= 30.0 and last_rsi > 30.0:
                return ('LONG', last_close)
            elif prev_rsi >= 70.0 and last_rsi < 70.0:
                return ('SHORT', last_close)

        elif strategy_key == 'D':
            # Strateji D: Momentum EMA Hızlı/Yavaş Kesişimi
            ema9 = df['close'].ewm(span=9, adjust=False).mean()
            ema21 = df['close'].ewm(span=21, adjust=False).mean()
            if len(ema9) < 2:
                return None
            
            if ema9.iloc[-2] <= ema21.iloc[-2] and ema9.iloc[-1] > ema21.iloc[-1]:
                return ('LONG', last_close)
            elif ema9.iloc[-2] >= ema21.iloc[-2] and ema9.iloc[-1] < ema21.iloc[-1]:
                return ('SHORT', last_close)

        else:
            # Diğer Stratejiler için RSI / Pivot Temelli Filtre
            rsi_series = IndicatorService.rsi(df['close'], period=14)
            if len(rsi_series) < 2 or pd.isna(rsi_series.iloc[-1]):
                return None
            last_rsi = float(rsi_series.iloc[-1])
            prev_rsi = float(rsi_series.iloc[-2])

            if prev_rsi <= 32.0 and last_rsi > 32.0:
                return ('LONG', last_close)
            elif prev_rsi >= 68.0 and last_rsi < 68.0:
                return ('SHORT', last_close)

        return None

    def _create_and_share_trade(self, symbol: str, side: str, strategy_name: str, timeframe: str, entry_price: float) -> Dict[str, Any]:
        """Sinyali sosyal akışta paylaşır ve bota kaydeder."""
        from app.utils.time_utils import format_tr_now
        self.total_signals_generated += 1
        now_str = format_tr_now()

        # /sosyal akışında Utku adına otomatik paylaş
        shared_trade = self.social_service.share_trade(
            trader_name='Utku',
            trader_handle='@utku',
            symbol=symbol,
            side=side,
            leverage='20x',
            timeframe=timeframe,
            entry_price=entry_price,
            strategy_name=strategy_name,
            notes=f'⚡ Sisyphus Bot Canlı İndikatör Sinyali: {symbol} ({timeframe} — {strategy_name}) teyit edildi. 20x kaldıraçlı pozisyon açıldı.'
        )

        trade_record = {
            'id': shared_trade['id'],
            'symbol': symbol,
            'side': side,
            'leverage': '20x',
            'timeframe': timeframe,
            'strategy_name': strategy_name,
            'entry_price': entry_price,
            'current_price': entry_price,
            'close_price': None,
            'exit_price': None,
            'current_pnl_pct': 0.0,
            'raw_pnl_pct': 0.0,
            'status': 'ACTIVE',
            'status_label': '🟢 Aktif',
            'opened_at': now_str,
            'closed_at': None
        }

        self.tracked_trades.insert(0, trade_record)
        return trade_record

    def _update_open_positions(self) -> None:
        """Açık pozisyonların güncel fiyatını ve strateji kâr/kapanış durumunu izler."""
        from app.utils.time_utils import format_tr_now
        for trade in self.tracked_trades:
            if trade.get('status') != 'ACTIVE':
                continue

            current_price = self._fetch_ticker_price(trade['symbol'])
            if not current_price:
                continue

            trade['current_price'] = current_price
            entry = trade['entry_price']
            is_long = trade['side'] == 'LONG'

            if is_long:
                raw_diff = (current_price - entry) / entry
            else:
                raw_diff = (entry - current_price) / entry
            
            pnl_pct = round(raw_diff * 20 * 100, 2)
            trade['current_pnl_pct'] = pnl_pct

            # Strateji Kapanış Kriteri (Örn: %15+ kârda TP Al veya %20 stop)
            if pnl_pct >= 15.0:
                trade['status'] = 'TP_HIT'
                trade['status_label'] = '🎯 TP Alındı'
                trade['close_price'] = current_price
                trade['exit_price'] = current_price
                trade['closed_at'] = format_tr_now()
                self.social_service.update_trade(trade['id'], {
                    'status': 'TP_HIT',
                    'close_price': current_price
                })
            elif pnl_pct <= -20.0:
                trade['status'] = 'SL_HIT'
                trade['status_label'] = '🛑 Pozisyon Kapatıldı'
                trade['close_price'] = current_price
                trade['exit_price'] = current_price
                trade['closed_at'] = format_tr_now()
                self.social_service.update_trade(trade['id'], {
                    'status': 'CLOSED',
                    'close_price': current_price
                })

    def _fetch_recent_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 50) -> Optional[pd.DataFrame]:
        """Binance'ten son mumları çeker."""
        try:
            exchange = self.get_exchange()
            market_sym = symbol if ':' in symbol else f"{symbol}:USDT"
            ohlcv = exchange.fetch_ohlcv(market_sym, timeframe=timeframe, limit=limit)
            if not ohlcv:
                return None
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except Exception:
            return None

    def _fetch_ticker_price(self, symbol: str) -> Optional[float]:
        """Canlı fiyatı çeker."""
        try:
            exchange = self.get_exchange()
            market_sym = symbol if ':' in symbol else f"{symbol}:USDT"
            ticker = exchange.fetch_ticker(market_sym)
            return float(ticker.get('last', ticker.get('close', 0.0)))
        except Exception:
            return None
