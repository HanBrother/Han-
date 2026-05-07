from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify(success=True)
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        return response, 200

@app.route("/api/stock", methods=["GET", "OPTIONS"])
def get_stock():
    """Stock data endpoint"""
    symbol = request.args.get("symbol", "").strip().upper()
    
    if not symbol:
        return jsonify({"error": "Missing symbol"}), 400
    
    # Format symbol
    if symbol.isdigit():
        symbol = f"{symbol}.TW"
    elif not symbol.endswith(".TW"):
        symbol = f"{symbol}.TW"
    
    try:
        hist = yf.download(symbol, period="100d", progress=False, threads=False)
        
        if hist.empty:
            return jsonify({"error": f"Not found: {symbol}"}), 404
        
        # Calculate indicators
        hist["MA5"] = hist["Close"].rolling(window=5).mean()
        hist["MA20"] = hist["Close"].rolling(window=20).mean()
        
        delta = hist["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        latest = hist.iloc[-1]
        
        # Get ticker info
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
            "pe": float(info.get("trailingPE", 0) or 0),
            "roe": float(info.get("returnOnEquity", 0) or 0),
            "sector": info.get("sector", "Unknown")
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
