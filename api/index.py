from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
import pandas as pd

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # 解析 query string
            query = self.path.split('?')[1] if '?' in self.path else ""
            params = {}
            for param in query.split('&'):
                if '=' in param:
                    key, val = param.split('=', 1)
                    params[key] = val.upper()
            
            symbol = params.get('symbol', '2330')
            
            # 格式化
            if not symbol.endswith('.TW'):
                symbol = f"{symbol}.TW"
            
            # 下載數據
            hist = yf.download(symbol, period="100d", progress=False)
            
            if hist.empty:
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
                return
            
            # 計算指標
            ma5 = float(hist['Close'].rolling(5).mean().iloc[-1])
            ma20 = float(hist['Close'].rolling(20).mean().iloc[-1])
            
            response = {
                "symbol": symbol,
                "price": float(hist['Close'].iloc[-1]),
                "ma5": ma5,
                "ma20": ma20,
            }
            
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()
