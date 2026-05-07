from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse

try:
    from twstock import Stock
except ImportError:
    Stock = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            if Stock is None:
                self.wfile.write(json.dumps({
                    "error": "twstock library not installed"
                }).encode())
                return
            
            query_params = parse_qs(urlparse(self.path).query)
            symbol = query_params.get('symbol', ['2330'])[0].strip()
            
            print(f"[DEBUG] Fetching Taiwan stock: {symbol}")
            
            # 使用 twstock 獲取台灣股票數據
            stock = Stock(symbol)
            
            # 獲取最新價格
            price_data = stock.fetch_from(2024, 1)  # 從 2024 年 1 月開始
            
            if not price_data:
                self.wfile.write(json.dumps({
                    "error": f"Stock {symbol} not found",
                    "tip": "Try: 2330, 2454, 1216, 0050, 0056"
                }).encode())
                return
            
            # 獲取最後一筆數據
            latest = price_data[-1]
            
            # 計算移動平均
            close_prices = [float(d.close) for d in price_data]
            ma5 = sum(close_prices[-5:]) / 5 if len(close_prices) >= 5 else float(latest.close)
            ma20 = sum(close_prices[-20:]) / 20 if len(close_prices) >= 20 else float(latest.close)
            rsi = self.calculate_rsi(close_prices)
            
            response = {
                "symbol": symbol,
                "price": float(latest.close),
                "ma5": round(ma5, 2),
                "ma20": round(ma20, 2),
                "rsi": round(rsi, 2),
                "change": float(latest.close) - float(latest.open),
                "high": float(latest.high),
                "low": float(latest.low),
                "volume": int(latest.transaction),
                "date": str(latest.date)
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            import traceback
            print(f"[ERROR] {traceback.format_exc()}")
            self.wfile.write(json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }).encode())
    
    def calculate_rsi(self, prices, period=14):
        try:
            if len(prices) < period:
                return 0.0
            
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas[-period:]]
            losses = [-d if d < 0 else 0 for d in deltas[-period:]]
            
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 0.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return 0.0
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
