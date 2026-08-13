CREATE OR REPLACE MODEL `project-841b7f97-5ee3-4fbe-920.infinity_dataset.xgboost_live_model`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['signal_outcome'],
  max_iterations = 50,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT 
  rsi_14, 
  macd_crossover, 
  vwap_distance, 
  atr_volatility, 
  signal_outcome
FROM 
  `project-841b7f97-5ee3-4fbe-920.infinity_dataset.market_ticks_history`
WHERE 
  timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY);
