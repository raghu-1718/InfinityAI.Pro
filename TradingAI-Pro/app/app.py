from flask import Flask, render_template
from core.trade_logger import get_trade_logs
from typing import List, Dict, Any

app = Flask(__name__, template_folder="dashboard/templates", static_folder="dashboard/static")

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/dashboard/<user_id>")
def dashboard(user_id: str):
	trades: List[Dict[str, Any]] = get_trade_logs(user_id)
	return render_template("dashboard.html", trades=trades)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5001)
