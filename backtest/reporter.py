def generate_report(tradebook):
    df = tradebook.to_df()
    
    if df.empty:
         return {
            "total_trades": 0,
            "total_pnl": 0,
            "max_drawdown": 0,
            "win_rate": 0
        }

    # Calculate pnl column first ensuring it exists
    df["pnl"] = df["price"].diff().fillna(0) * df["qty"]

    report = {
        "total_trades": len(df),
        "total_pnl": df["pnl"].sum(),
        "max_drawdown": tradebook.max_drawdown(),
        "win_rate": (df["pnl"] > 0).mean() * 100
    }

    return report
