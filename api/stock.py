#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import yfinance as yf

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Parse query string
        query_components = parse_qs(urlparse(self.path).query)
        symbol = query_components.get('symbol', [''])[0]
        
        if not symbol:
            self.wfile.write(json.dumps({'error': 'No symbol provided'}).encode())
            return
        
        try:
            # Add .TW for Taiwan stocks (numbers only)
            if symbol.isdigit():
                symbol = symbol + '.TW'
            
            # Fetch current data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            
            if data.empty:
                self.wfile.write(json.dumps({'error': 'Stock not found'}).encode())
                return
            
            # Get current price
            current_price = float(data['Close'].iloc[-1])
            
            # Get previous close for change calculation
            prev_data = ticker.history(period='5d')
            if len(prev_data) > 1:
                prev_close = float(prev_data['Close'].iloc[-2])
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
            else:
                change = 0
                change_percent = 0
            
            volume = int(data['Volume'].iloc[-1]) if 'Volume' in data else 0
            
            response = {
                'symbol': symbol,
                'currentPrice': round(current_price, 2),
                'change': round(change, 2),
                'changePercent': round(change_percent, 2),
                'volume': volume
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.wfile.write(json.dumps({'error': str(e)}).encode())
