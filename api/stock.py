from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            symbol = self.path.split('symbol=')[1].split('&')[0] if 'symbol=' in self.path else None
            
            if not symbol:
                self.wfile.write(json.dumps({"error": "缺少股票代碼"}).encode())
                return
            
            if symbol.isdigit():
                symbol = f"{symbol}.TW"
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo")
            info = ticker.info
            
            if hist.empty:
                self.wfile.write(json.dumps({"error": f"找不到 {symbol}"}).encode())
                return
            
            last_30 = hist.tail(30)
            dates = last_30.index.strftime('%m-%d').tolist()
            prices = last_30['Close'].tolist()
            
            response = {
                "symbol": symbol.replace(".TW", ""),
                "name": info.get("longName", symbol),
                "currentPrice": float(hist['Close'].iloc[-1]),
                "previousPrice": float(hist['Close'].iloc[-2]) if len(hist) > 1 else 0,
                "change": float(hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) if len(hist) > 1 else 0,
                "changePercent": float((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0,
                "openPrice": float(hist['Open'].iloc[-1]),
                "highPrice": float(hist['High'].iloc[-1]),
                "lowPrice": float(hist['Low'].iloc[-1]),
                "volume": int(hist['Volume'].iloc[-1]),
                "dates": dates,
                "prices": prices
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
