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
            
            # 試多種格式
            formats = [
                symbol,           # 直接用
                f"{symbol}.TW",   # 加 .TW
                f"{symbol}.TA",   # 加 .TA
                f"0{symbol}.TW" if len(symbol) == 4 else symbol  # 4碼加 0
            ]
            
            hist = None
            used_symbol = None
            
            for fmt in formats:
                try:
                    hist = yf.download(fmt, period="100d", progress=False)
                    if not hist.empty:
                        used_symbol = fmt
                        break
                except:
                    continue
            
            if hist is None or hist.empty:
                self.wfile.write(json.dumps({
                    "error": f"Stock {symbol} not found. Try: 2330, AAPL, MSFT",
                    "symbol_requested": symbol
                }).encode())
                return
            
            # 計算指標
            close_prices = hist['Close']
            ma5 = float(close_prices.rolling(5).mean().iloc[-1])
            ma20 = float(close_prices.rolling(20).mean().iloc[-1])
            rsi = self.calculate_rsi(close_prices)
            
            response = {
                "symbol": used_symbol,
                "price": round(float(close_prices.iloc[-1]), 2),
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
