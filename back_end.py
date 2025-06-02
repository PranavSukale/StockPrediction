import yfinance as yf
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Store portfolio data in memory (no DB for simplicity)
portfolio = {}

@app.route('/api/stock/<ticker>', methods=['GET'])
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty or "Close" not in data:
            return jsonify({"error": f"No data found for {ticker}"}), 404

        last_price = data["Close"].iloc[-1]
        return jsonify({
            "ticker": ticker,
            "price": float(last_price),
            "timestamp": pd.Timestamp.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio', methods=['POST'])
def add_to_portfolio():
    try:
        data = request.json
        ticker = data.get("ticker").upper()
        quantity = int(data.get("quantity"))
        buy_price = float(data.get("buy_price"))

        if ticker in portfolio:
            portfolio[ticker]["quantity"] += quantity
            portfolio[ticker]["total_cost"] += quantity * buy_price
        else:
            portfolio[ticker] = {"quantity": quantity, "total_cost": quantity * buy_price}

        return jsonify({"message": f"{ticker} added to portfolio", "portfolio": portfolio})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    try:
        if not portfolio:
            return jsonify({"message": "Portfolio is empty", "portfolio": {}, "total_value": 0})

        portfolio_data = {}
        total_value = 0

        for ticker, data in portfolio.items():
            stock = yf.Ticker(ticker)
            history = stock.history(period="1d")
            if "Close" not in history or history["Close"].empty:
                return jsonify({"error": f"No market data available for {ticker}"}), 404
            
            price = history["Close"].iloc[-1]
            value = price * data["quantity"]
            gain_loss = value - data["total_cost"]
            portfolio_data[ticker] = {
                "quantity": data["quantity"],
                "buy_price": round(data["total_cost"] / data["quantity"], 2),
                "current_price": round(price, 2),
                "current_value": round(value, 2),
                "gain_loss": round(gain_loss, 2)
            }
            total_value += value

        return jsonify({"portfolio": portfolio_data, "total_value": round(total_value, 2)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/<ticker>', methods=['DELETE'])
def remove_from_portfolio(ticker):
    try:
        ticker = ticker.upper()
        if ticker in portfolio:
            del portfolio[ticker]
            return jsonify({"message": f"{ticker} removed from portfolio"})
        return jsonify({"error": f"{ticker} not found in portfolio"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
