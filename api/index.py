from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
from urllib.parse import parse_qs, urlparse
import warnings
warnings.filterwarnings('ignore')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            query_params = parse_qs(urlparse(self.path).query)
            symbol = query_params.get('symbol', ['2330'])[0].upper().strip()
            
            # 台灣股票對應表
            taiwan_stocks = {
                '2330': 'TSMC',      # 台積電
                '2454': '2454.TW',   # 聯發科
                '1216': '1216.TW',   # 統一超
                '0050': '0050.TW',   # 台灣50
                '0056': '0056.TW',   # 高股息
            }
            
            yahoo_symbol = taiwan_stocks.get(symbol, symbol)
            
            print(f"[DEBUG] User input: {symbol}, Yahoo symbol: {yahoo_symbol}")
            
            # 移除 quiet=True
            hist = yf.download(yahoo_symbol, period="100d", progress=False)
            
            if hist.empty:
                # 試試其他格式
                for fmt in [f"{symbol}.TW", f"{symbol}.TA", symbol]:
                    hist = yf.download(fmt, period="100d", progress=False)
                    if not hist.empty:
                        yahoo_symbol = fmt
                        break
            
            if hist.empty:
                self.wfile.write(json.dumps({
                    "error": f"Stock {symbol} not found",
                    "tip": "支援: 2330(台積電), 2454, 1216, 0050, AAPL, MSFT",
                    "symbol_requested": symbol
                }).encode())
                return
            
            close = hist['Close']
            
            # 計算指標
            ma5 = float(close.rolling(5).mean().iloc[-1])
            ma20 = float(close.rolling(20).mean().iloc[-1])
            rsi = self.calculate_rsi(close)
            
            response = {
                "symbol": symbol,
                "actual_symbol": yahoo_symbol,
                "price": round(float(close.iloc[-1]), 2),
                "ma5": round(ma5, 2),
                "ma20": round(ma20, 2),
                "rsi": round(rsi, 2),
                "change": round(float(close.iloc[-1] - close.iloc[-2]), 2),
                "currency": "USD" if not symbol.isdigit() else "TWD",
                "date": str(hist.index[-1].date())
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            import traceback
            self.wfile.write(json.dumps({
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }).encode())
    
    def calculate_rsi(self, prices, period=14):
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except:
            return 0.0
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
