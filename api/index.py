from flask import Flask, request, jsonify, send_from_directory
import yfinance as yf
import pandas as pd
import numpy as np
import os

app = Flask(__name__, static_folder='public', static_url_path='')

# CORS 中間件
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/stock', methods=['GET', 'OPTIONS'])
def get_stock():
    """股票資料 API"""
    if request.method == 'OPTIONS':
        return '', 204
    
    symbol = request.args.get('symbol', '').strip().upper()
    
    if not symbol:
        return jsonify({'error': 'Missing symbol parameter'}), 400
    
    # 確保符號格式
    if symbol.isdigit():
        symbol = symbol + '.TW'
    elif not symbol.endswith('.TW'):
        symbol = symbol + '.TW'
    
    try:
        # 下載歷史數據
        hist = yf.download(symbol, period='100d', progress=False, threads=False)
        
        if hist.empty:
            return jsonify({'error': f'Stock not found: {symbol}'}), 404
        
        # 計算移動平均線
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        
        # 計算 RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        latest = hist.iloc[-1]
        
        # 獲取基本面數據
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        response = {
            'symbol': symbol.replace('.TW', ''),
            'name': info.get('longName', symbol),
            'price': float(latest['Close']),
            'change': float(info.get('regularMarketChange', 0) or 0),
            'changePercent': float(info.get('regularMarketChangePercent', 0) or 0),
            'ma5': float(latest['MA5']) if pd.notna(latest['MA5']) else None,
            'ma20': float(latest['MA20']) if pd.notna(latest['MA20']) else None,
            'rsi': float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None,
            'volume': int(latest['Volume']) if pd.notna(latest['Volume']) else 0,
            'pe': float(info.get('trailingPE', 0) or 0),
            'roe': float(info.get('returnOnEquity', 0) or 0),
            'sector': info.get('sector', 'Unknown')
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Vercel 需要這個
def handler(request):
    return app(request)

if __name__ == '__main__':
    app.run(debug=True)
