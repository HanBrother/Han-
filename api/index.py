import json
from http.server import BaseHTTPRequestHandler
import yfinance as yf

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """處理 GET 請求"""
        if '/api/stock' in self.path:
            # 解析 query string
            query = self.path.split('?')[1] if '?' in self.path else ""
            params = {}
            for param in query.split('&'):
                if '=' in param:
                    key, value = param.split('=')
                    params[key] = value
            
            symbol = params.get('symbol', '').strip().upper()
            
            if not symbol:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing symbol"}).encode())
                return
            
            # 格式化股票代碼
            if symbol.isdigit():
                symbol = f"{symbol}.TW"
            elif not symbol.endswith(".TW"):
                symbol = f"{symbol}.TW"
            
            try:
                hist = yf.download(symbol, period="100d", progress=False, threads=False)
                
                if hist.empty:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Not found: {symbol}"}).encode())
                    return
                
                # 計算技術指標
                hist["MA5"] = hist["Close"].rolling(window=5).mean()
                hist["MA20"] = hist["Close"].rolling(window=20).mean()
                
                delta = hist["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                latest = hist.iloc[-1]
                
                # 獲取基本信息
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                response = {
                    "symbol": symbol.replace(".TW", ""),
                    "name": info.get("longName", symbol),
                    "price": float(latest["Close"]),
                    "change": float(info.get("regularMarketChange", 0) or 0),
                    "changePercent": float(info.get("regularMarketChangePercent", 0) or 0),
                    "ma5": float(latest["MA5"]) if pd.notna(latest["MA5"]) else None,
                    "ma20": float(latest["MA20"]) if pd.notna(latest["MA20"]) else None,
                    "rsi": float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None,
                    "volume": int(latest["Volume"]) if pd.notna(latest["Volume"]) else 0,
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """處理 CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
