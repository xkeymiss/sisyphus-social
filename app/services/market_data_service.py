"""
Market data service with local CSV caching.
"""

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import ccxt
import pandas as pd
from app.config import BaseConfig


class MarketDataService:
    """Binance Futures piyasa verisi sağlayıcısı ve önbellek yöneticisi."""

    def __init__(self, cache_dir: Optional[str] = None, rate_limit_delay: float = 0.05):
        self.cache_dir = cache_dir or str(BaseConfig.DATA_CACHE_DIR)
        self.rate_limit_delay = rate_limit_delay
        os.makedirs(self.cache_dir, exist_ok=True)
        self._exchange = None

    def get_exchange(self) -> ccxt.binanceusdm:
        """İzole ve rate-limit korumalı ccxt Binance USD-M Futures örneği üretir."""
        if self._exchange is None:
            self._exchange = ccxt.binanceusdm({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
        return self._exchange

    def get_all_symbols(self, quote_currency: str = 'USDT') -> List[str]:
        """
        Aktif işlem gören tüm vadeli işlem sembollerini listeler.
        
        Args:
            quote_currency: Karşıt para birimi (Varsayılan: 'USDT')
            
        Returns:
            List[str]: Sıralı sembol listesi (Ör: ['BTC/USDT:USDT', 'ETH/USDT:USDT'])
        """
        exchange = self.get_exchange()
        try:
            exchange.load_markets()
            symbols = []
            for symbol, market in exchange.markets.items():
                if (market.get('swap', False) and
                    market.get('active', False) and
                    market.get('quote') == quote_currency and
                    market.get('linear', False)):
                    symbols.append(symbol)
            symbols.sort()
            return symbols
        except Exception as e:
            # Ağ veya API hatasında güvenli geri dönüş
            return [f"BTC/{quote_currency}:{quote_currency}", f"ETH/{quote_currency}:{quote_currency}"]

    def _get_cache_path(self, symbol: str, timeframe: str) -> str:
        """Sembol ve zaman dilimine özel güvenli önbellek dosya yolu üretir."""
        safe_symbol = symbol.replace('/', '_').replace(':', '_')
        return os.path.join(self.cache_dir, f"{safe_symbol}_{timeframe}.csv")

    def _is_cache_valid(self, cache_file: str, max_age_hours: float = 6.0) -> bool:
        """Önbelleğin geçerlilik ve tazelik süresini kontrol eder."""
        if not os.path.exists(cache_file):
            return False
        mtime = os.path.getmtime(cache_file)
        age_hours = (time.time() - mtime) / 3600.0
        return age_hours < max_age_hours

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', days: int = 90, force_refresh: bool = False) -> pd.DataFrame:
        """
        Belirtilen sembol ve zaman dilimi için OHLCV mum verilerini çeker.
        Önbellek geçerliyse doğrudan diskten okur, değilse borsadan indirip önbelleğe yazar.
        
        Returns:
            pd.DataFrame: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        cache_file = self._get_cache_path(symbol, timeframe)
        
        if not force_refresh and self._is_cache_valid(cache_file):
            try:
                df = pd.read_csv(cache_file, parse_dates=['timestamp'])
                if not df.empty and 'close' in df.columns:
                    return df
            except Exception:
                pass  # Önbellek bozulmuşsa yeniden indir
                
        exchange = self.get_exchange()
        since = exchange.parse8601(
            (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        )
        
        all_candles = []
        limit = 1500
        
        while True:
            try:
                candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            except Exception as e:
                break
                
            if not candles:
                break
                
            all_candles.extend(candles)
            since = candles[-1][0] + 1
            
            if len(candles) < limit:
                break
                
            time.sleep(self.rate_limit_delay)
            
        if not all_candles:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.drop_duplicates(subset=['timestamp'], keep='last', inplace=True)
        df.sort_values('timestamp', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        try:
            df.to_csv(cache_file, index=False)
        except Exception:
            pass
            
        return df

    def fetch_htf_data(self, symbol: str, days: int = 90) -> Dict[str, pd.DataFrame]:
        """
        Üst zaman dilimi verilerini (Daily, Weekly, Monthly) tek seferde toplar.
        
        Returns:
            Dict[str, pd.DataFrame]: {'daily': df, 'weekly': df, 'monthly': df}
        """
        extended_days = days + 60
        daily_df = self.fetch_ohlcv(symbol, '1d', days=extended_days)
        time.sleep(self.rate_limit_delay)
        weekly_df = self.fetch_ohlcv(symbol, '1w', days=extended_days)
        time.sleep(self.rate_limit_delay)
        monthly_df = self.fetch_ohlcv(symbol, '1M', days=extended_days * 2)
        
        return {
            'daily': daily_df,
            'weekly': weekly_df,
            'monthly': monthly_df
        }
