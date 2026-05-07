from flask import Flask, request, jsonify
import yfinance as yf
from datetime import datetime
import pandas as pd

app = Flask(__name__)

def calculate_technical_indicators(df):
    """計算技術指標"""
    if df is None or df.empty:
        return {}
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    
    indicators = {}
    indicators['Current_Price'] = float(close.iloc[-1])
    indicators['Prev_Close'] = float(close.iloc[-2]) if len(close) > 1 else float(close.iloc[-1])
    indicators['Change'] = indicators['Current_Price'] - indicators['Prev_Close']
    indicators['Change_Pct'] = (indicators['Change'] / indicators['Prev_Close']) * 100
    
    # MA5, MA20
    if len(close) >= 20:
        indicators['MA5'] = float(close.rolling(5).mean().iloc[-1])
        indicators['MA20'] = float(close.rolling(20).mean().iloc[-1])
    
    # RSI
    if len(close) >= 15:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators['RSI'] = float(rsi.iloc[-1])
    
    return indicators

@app.route('/api/stock', methods=['GET'])
def get_stock():
    symbol = request.args.get('symbol', '').upper().strip()
    
    if not symbol:
        return jsonify({'error': '請提供股票代碼'}), 400
    
    try:
        # 自動為數字代碼加 .TW
        if symbol.isdigit():
            symbol = symbol + '.TW'
        
        print(f"[LOG] 查詢股票: {symbol}")
        
        # 獲取數據
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='6mo')
        
        if hist.empty:
            return jsonify({'error': f'找不到股票: {symbol}'}), 404
        
        # 計算指標
        indicators = calculate_technical_indicators(hist)
        
        # 基本面
        info = ticker.info
        pe = info.get('trailingPE') or info.get('forwardPE') or 0
        roe = (info.get('returnOnEquity', 0) * 100) if info.get('returnOnEquity') else 0
        
        response = {
            'symbol': symbol.replace('.TW', ''),
            'name': info.get('longName', symbol),
            'price': indicators.get('Current_Price', 0),
            'change': indicators.get('Change', 0),
            'changePercent': indicators.get('Change_Pct', 0),
            'volume': int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0,
            'ma5': indicators.get('MA5', 0),
            'ma20': indicators.get('MA20', 0),
            'rsi': indicators.get('RSI', 0),
            'pe': float(pe) if pe else 0,
            'roe': float(roe) if roe else 0,
            'sector': info.get('sector', 'N/A'),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({'error': f'查詢失敗: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'}), 200

if __name__ == '__main__':
    app.run(debug=False)
