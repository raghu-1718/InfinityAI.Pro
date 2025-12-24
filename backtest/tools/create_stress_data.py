import pandas as pd
import numpy as np
import os

def create_stress_dataset():
    # Load original
    base_path = "backtest/data/crudeoil_5m_sample.csv"
    if not os.path.exists(base_path):
        print(f"Error: {base_path} not found.")
        return

    df = pd.read_csv(base_path)
    
    # Simulate Volatility Spike: Double the High-Low range, random noise on Close
    # We keep the trend roughly similar but much noisier/wider, triggering stops?
    
    # Widen High/Low
    df['high'] = df['high'] + (df['high'] * 0.002) # +0.2%
    df['low'] = df['low'] - (df['low'] * 0.002)   # -0.2%
    
    # Add noise to close, ensuring it stays within high/low
    noise = np.random.normal(0, 5, len(df))
    df['close'] = df['close'] + noise
    
    # Clamp close
    df['close'] = np.minimum(df['high'], np.maximum(df['low'], df['close']))
    
    target_path = "backtest/data/crudeoil_stress_volatility.csv"
    df.to_csv(target_path, index=False)
    print(f"Created Stress Dataset: {target_path}")

if __name__ == "__main__":
    create_stress_dataset()
