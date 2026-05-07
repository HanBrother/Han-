from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # 解析 query string
            query_params = parse_qs(urlparse(self.path).query)
            symbol = query_params.get('symbol', ['2330'])[0].upper().strip()
            
            # 確保有 .TW 後綴（台灣股票）
            if not symbol.endswith('.TW'):
                symbol = f"{symbol}.TW"
            
            print(f"Fetching: {symbol}")  # Debug 用
            
            # 下載數據
            hist = yf.download(symbol, period="100d", progress=False)
            
            if hist.empty:
                self.wfile.write(json.dumps({
                    "error": f"Stock {symbol} not found",
                    "symbol_requested": symbol
                }).encode())
                return
            
            # 計算指標
            close_prices = hist['Close']
            ma5 = float(close_prices.rolling(5).mean().iloc[-1])
            ma20 = float(close_prices.rolling(20).mean().iloc[-1])
            rsi = self.calculate_rsi(close_prices)
            
            response = {
                "symbol": symbol,
                "price": float(close_prices.iloc[-1]),
                "ma5": round(ma5, 2),
                "ma20": round(ma20, 2),
                "rsi": round(rsi, 2),
                "change": round(float(close_prices.iloc[-1] - close_prices.iloc[-2]), 2)
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.wfile.write(json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }).encode())
    
    def calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()
