"""
Market data routes.
"""

from flask import jsonify, request
from app.blueprints.market import market_bp
from app.services.market_data_service import MarketDataService

# Servis örneği (Singleton pattern)
market_service = MarketDataService()


@market_bp.route('/symbols', methods=['GET'])
def get_symbols():
    """
    Aktif Binance USDT Perpetual Futures sembol listesini döndürür.
    
    Query Params:
        quote (str): Karşıt para birimi (Varsayılan: 'USDT')
        
    Returns:
        JSON: Sembol dizisi ve toplam sayı.
    """
    quote = request.args.get('quote', 'USDT')
    symbols = market_service.get_all_symbols(quote_currency=quote)
    return jsonify({
        'status': 'success',
        'symbols': symbols,
        'count': len(symbols)
    }), 200


@market_bp.route('/ohlcv/<path:symbol>', methods=['GET'])
def get_ohlcv(symbol: str):
    """
    Belirli bir sembol ve zaman dilimi için OHLCV mum verilerini döndürür.
    
    Args:
        symbol: Kripto çifti sembolü (ör. BTC/USDT:USDT)
        
    Query Params:
        timeframe (str): Zaman dilimi (ör. 5m, 15m, 1h, 4h, 1d)
        days (int): Geçmiş gün sayısı
        refresh (bool): Önbelleği atlayıp borsadan zorla yenileme
        
    Returns:
        JSON: OHLCV mum verileri listesi.
    """
    timeframe = request.args.get('timeframe', '1h')
    days = int(request.args.get('days', 30))
    force_refresh = request.args.get('refresh', 'false').lower() in ('true', '1')
    
    df = market_service.fetch_ohlcv(symbol=symbol, timeframe=timeframe, days=days, force_refresh=force_refresh)
    
    if df.empty:
        return jsonify({
            'status': 'error',
            'message': f'{symbol} ({timeframe}) için mum verisi bulunamadı',
            'candles': []
        }), 404
        
    candles = df.to_dict(orient='records')
    # Tarih nesnelerini string formatına çevirme
    for c in candles:
        c['timestamp'] = str(c['timestamp'])
        
    return jsonify({
        'status': 'success',
        'symbol': symbol,
        'timeframe': timeframe,
        'days': days,
        'count': len(candles),
        'candles': candles
    }), 200
