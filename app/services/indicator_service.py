"""
Technical indicators calculation module.
"""

from typing import Tuple
import numpy as np
import pandas as pd


class IndicatorService:
    """Quantitative technical indicator calculations."""

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 1.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bantlarını hesaplar.
        
        Args:
            series: Kapanış fiyatı serisi (pd.Series)
            period: Hareketli ortalama periyodu
            std_dev: Standart sapma katsayısı (Varsayılan: 1.0)
            
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (Orta Bant / Basis, Üst Bant, Alt Bant)
        """
        basis = series.rolling(window=period, min_periods=period).mean()
        std = series.rolling(window=period, min_periods=period).std(ddof=0)
        upper = basis + (std * std_dev)
        lower = basis - (std * std_dev)
        return basis, upper, lower

    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        """
        Günlük Çapalı (Daily-Anchored) Ağırlıklı Ortalama Fiyatı (VWAP) hesaplar.
        
        Args:
            df: 'timestamp', 'open', 'high', 'low', 'close', 'volume' sütunlarını içeren DataFrame.
            
        Returns:
            pd.Series: İlgili bara ait VWAP değerleri serisi.
        """
        if df.empty or 'volume' not in df.columns or 'timestamp' not in df.columns:
            return pd.Series(dtype=float)
            
        typical_price = (df['high'] + df['low'] + df['close']) / 3.0
        dates = pd.to_datetime(df['timestamp']).dt.date
        
        vwap_values = np.zeros(len(df), dtype=float)
        cum_tp_vol = 0.0
        cum_vol = 0.0
        prev_date = None
        
        for i in range(len(df)):
            current_date = dates.iloc[i]
            
            if current_date != prev_date:
                cum_tp_vol = 0.0
                cum_vol = 0.0
                prev_date = current_date
            
            vol = float(df['volume'].iloc[i])
            cum_tp_vol += float(typical_price.iloc[i]) * vol
            cum_vol += vol
            
            if cum_vol > 0:
                vwap_values[i] = cum_tp_vol / cum_vol
            else:
                vwap_values[i] = typical_price.iloc[i]
                
        return pd.Series(vwap_values, index=df.index)

    @staticmethod
    def poc(close: pd.Series, volume: pd.Series, range_length: int = 100) -> pd.Series:
        """
        Hacim Kontrol Noktası (Point of Control - POC).
        Geçmiş `range_length` barlık pencerede en yüksek hacmin gerçekleştiği fiyat seviyesini bulur.
        
        Args:
            close: Kapanış fiyat serisi
            volume: Hacim serisi
            range_length: Geriye dönük incelenecek bar uzunluğu
            
        Returns:
            pd.Series: POC seviyeleri serisi.
        """
        poc_values = pd.Series(np.nan, index=close.index, dtype=float)
        if len(close) < range_length:
            return poc_values
            
        for i in range(range_length, len(close)):
            window_vol = volume.iloc[i - range_length:i]
            window_close = close.iloc[i - range_length:i]
            max_vol_idx = window_vol.idxmax()
            poc_values.iloc[i] = window_close.loc[max_vol_idx]
            
        return poc_values

    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """
        Üstel Hareketli Ortalama (EMA) hesaplar.
        
        Args:
            series: Fiyat serisi
            period: EMA periyodu
            
        Returns:
            pd.Series: EMA değerleri serisi.
        """
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Göreceli Güç Endeksi (RSI - Wilder's Smoothing) hesaplar.
        
        Args:
            series: Fiyat serisi
            period: RSI periyodu (Varsayılan: 14)
            
        Returns:
            pd.Series: RSI değerleri serisi (0-100 aralığı).
        """
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0).fillna(0.0)
        loss = (-delta.where(delta < 0, 0.0)).fillna(0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        avg_gain_vals = avg_gain.to_numpy(copy=True)
        avg_loss_vals = avg_loss.to_numpy(copy=True)
        gain_vals = gain.to_numpy()
        loss_vals = loss.to_numpy()

        for i in range(period, len(series)):
            avg_gain_vals[i] = (avg_gain_vals[i - 1] * (period - 1) + gain_vals[i]) / period
            avg_loss_vals[i] = (avg_loss_vals[i - 1] * (period - 1) + loss_vals[i]) / period

        rs = np.divide(
            avg_gain_vals, 
            avg_loss_vals, 
            out=np.zeros_like(avg_gain_vals), 
            where=avg_loss_vals != 0
        )
        rsi_vals = 100.0 - (100.0 / (1.0 + rs))
        return pd.Series(rsi_vals, index=series.index)

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Ortalama Gerçek Aralık (ATR - Volatilite Göstergesi) hesaplar.
        
        Args:
            high: En yüksek fiyat serisi
            low: En düşük fiyat serisi
            close: Kapanış fiyat serisi
            period: Periyot (Varsayılan: 14)
            
        Returns:
            pd.Series: ATR değerleri serisi.
        """
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr_series = true_range.rolling(window=period, min_periods=period).mean()
        atr_vals = atr_series.to_numpy(copy=True)
        tr_vals = true_range.to_numpy()

        for i in range(period, len(true_range)):
            if not np.isnan(atr_vals[i - 1]):
                atr_vals[i] = (atr_vals[i - 1] * (period - 1) + tr_vals[i]) / period

        return pd.Series(atr_vals, index=high.index)

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Ortalama Yönsel Endeks (ADX - Trend Gücü) hesaplar.
        25 üzeri değerler güçlü trende işaret eder.
        
        Returns:
            pd.Series: ADX değerleri serisi.
        """
        prev_high = high.shift(1)
        prev_low = low.shift(1)

        plus_dm = np.where((high - prev_high) > (prev_low - low), np.maximum(high - prev_high, 0.0), 0.0)
        minus_dm = np.where((prev_low - low) > (high - prev_high), np.maximum(prev_low - low, 0.0), 0.0)

        plus_dm_series = pd.Series(plus_dm, index=high.index, dtype=float)
        minus_dm_series = pd.Series(minus_dm, index=high.index, dtype=float)

        atr_val = IndicatorService.atr(high, low, close, period)

        smooth_plus = plus_dm_series.rolling(window=period, min_periods=period).mean()
        smooth_minus = minus_dm_series.rolling(window=period, min_periods=period).mean()

        sp_vals = smooth_plus.to_numpy(copy=True)
        sm_vals = smooth_minus.to_numpy(copy=True)
        p_dm_vals = plus_dm_series.to_numpy()
        m_dm_vals = minus_dm_series.to_numpy()

        for i in range(period, len(plus_dm_series)):
            if not np.isnan(sp_vals[i - 1]):
                sp_vals[i] = (sp_vals[i - 1] * (period - 1) + p_dm_vals[i]) / period
                sm_vals[i] = (sm_vals[i - 1] * (period - 1) + m_dm_vals[i]) / period

        smooth_plus = pd.Series(sp_vals, index=high.index)
        smooth_minus = pd.Series(sm_vals, index=high.index)

        plus_di = 100.0 * (smooth_plus / atr_val.replace(0, np.nan))
        minus_di = 100.0 * (smooth_minus / atr_val.replace(0, np.nan))

        di_sum = plus_di + minus_di
        di_diff = (plus_di - minus_di).abs()
        dx = 100.0 * (di_diff / di_sum.replace(0, np.nan))

        adx_series = dx.rolling(window=period, min_periods=period).mean()
        adx_vals = adx_series.to_numpy(copy=True)
        dx_vals = dx.to_numpy()

        for i in range(2 * period - 1, len(dx)):
            if not np.isnan(adx_vals[i - 1]) and not np.isnan(dx_vals[i]):
                adx_vals[i] = (adx_vals[i - 1] * (period - 1) + dx_vals[i]) / period

        return pd.Series(adx_vals, index=high.index)

    @staticmethod
    def detect_fvg(high: pd.Series, low: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        Fair Value Gap (FVG - Fiyat Dengesizliği) formasyonlarını tespit eder.
        
        Boğa FVG (Bullish): low[i] > high[i-2]
        Ayı FVG (Bearish): high[i] < low[i-2]
        
        Returns:
            Tuple[pd.Series, pd.Series]: (bullish_fvg, bearish_fvg) boolean serileri.
        """
        bullish = pd.Series(False, index=high.index)
        bearish = pd.Series(False, index=high.index)

        for i in range(2, len(high)):
            if low.iloc[i] > high.iloc[i - 2]:
                bullish.iloc[i] = True
            if high.iloc[i] < low.iloc[i - 2]:
                bearish.iloc[i] = True

        return bullish, bearish

    @staticmethod
    def calculate_squeeze(df: pd.DataFrame, bb_window: int = 20, bb_std: float = 2.0, kc_window: int = 20, kc_mult: float = 1.5) -> pd.DataFrame:
        """
        Volatilite Sıkışması (TTM Squeeze) ve Momentum hesaplar.
        Bollinger Bantları Keltner Kanallarının içine girdiğinde Squeeze aktiftir.
        
        Returns:
            pd.DataFrame: 'squeeze_on' (bool) ve 'squeeze_mom' (float) sütunları eklenmiş df.
        """
        res_df = df.copy()
        
        # Bollinger Bantları
        bb_mid = res_df['close'].rolling(window=bb_window).mean()
        bb_sd = res_df['close'].rolling(window=bb_window).std(ddof=0)
        bb_upper = bb_mid + (bb_sd * bb_std)
        bb_lower = bb_mid - (bb_sd * bb_std)
        
        # Keltner Kanalları
        atr_val = IndicatorService.atr(res_df['high'], res_df['low'], res_df['close'], period=kc_window)
        kc_mid = res_df['close'].ewm(span=kc_window, adjust=False).mean()
        kc_upper = kc_mid + (atr_val * kc_mult)
        kc_lower = kc_mid - (atr_val * kc_mult)
        
        # Squeeze Durumu
        res_df['squeeze_on'] = (bb_upper < kc_upper) & (bb_lower > kc_lower)
        
        # Momentum
        highest_high = res_df['high'].rolling(window=kc_window).max()
        lowest_low = res_df['low'].rolling(window=kc_window).min()
        donchian_mid = (highest_high + lowest_low) / 2.0
        sma_close = res_df['close'].rolling(window=kc_window).mean()
        
        val = res_df['close'] - ((donchian_mid + sma_close) / 2.0)
        res_df['squeeze_mom'] = val.rolling(window=kc_window).mean()
        
        return res_df

    @staticmethod
    def macd(series: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Hareketli Ortalama Yakınsama/Iraksama) hesaplar.
        
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (macd_line, signal_line, histogram)
        """
        fast_ema = IndicatorService.ema(series, fast_period)
        slow_ema = IndicatorService.ema(series, slow_period)
        macd_line = fast_ema - slow_ema
        signal_line = IndicatorService.ema(macd_line, signal_period)
        macd_hist = macd_line - signal_line
        return macd_line, signal_line, macd_hist

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stokastik Osilatör (%K ve %D) hesaplar.
        
        Returns:
            Tuple[pd.Series, pd.Series]: (percent_k, percent_d)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        range_diff = highest_high - lowest_low
        fast_k = 100.0 * ((close - lowest_low) / range_diff.replace(0, np.nan))
        percent_k = fast_k.rolling(window=smooth_k).mean()
        percent_d = percent_k.rolling(window=d_period).mean()
        return percent_k, percent_d
