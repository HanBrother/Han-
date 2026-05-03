from flask import Flask, request, jsonify
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

@app.route('/api/stock', methods=['GET'])
def get_stock():
    symbol = request.args.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({'error': '請提供股票代碼'}), 400
    
    try:
        # 自動為數字代碼加上 .TW（台灣股票）
        if symbol.isdigit():
            symbol = symbol + '.TW'
        
        # 獲取當前數據
        stock = yf.Ticker(symbol)
        hist = stock.history(period='1d')
        
        if hist.empty:
            return jsonify({'error': f'找不到股票: {symbol}'}), 404
        
        current_price = hist['Close'].iloc[-1]
        
        # 獲取前一天數據計算漲跌
        hist_5d = stock.history(period='5d')
        
        if len(hist_5d) > 1:
            prev_close = hist_5d['Close'].iloc[-2]
        else:
            prev_close = current_price
        
        change = current_price - prev_close
        change_percent = (change / prev_close * 100) if prev_close != 0 else 0
        
        volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0
        
        return jsonify({
            'symbol': symbol.replace('.TW', ''),
            'price': float(current_price),
            'change': float(change),
            'changePercent': float(change_percent),
            'volume': volume,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': f'查詢失敗: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
