#!/usr/bin/env python3
"""
Cloud Function Entry Point for Backtest Orchestrator
Wraps backtest_orchestrator.py for Google Cloud Functions deployment
"""

import functions_framework
from backtest_orchestrator import BacktestOrchestrator, run_backtest_pipeline


@functions_framework.http
def main(request):
    """
    HTTP Cloud Function for backtest orchestration
    
    Request parameters:
    - symbols: Comma-separated symbol list (default: NIFTY,BANKNIFTY,FINNIFTY)
    - data_source: Cloud Storage path (default: gs://infinityai-backtesting-data/)
    - output_bucket: Output bucket (default: infinityai-backtest-results)
    
    Returns:
        JSON response with backtest results
    """
    import json
    from flask import Request
    
    try:
        # Parse request
        request_json = request.get_json() or {}
        request_args = request.args or {}
        
        symbols = (request_json.get('symbols') or request_args.get('symbols') or 
                   'NIFTY,BANKNIFTY,FINNIFTY').split(',')
        data_source = request_json.get('data_source') or request_args.get('data_source') or \
                      'gs://infinityai-backtesting-data/'
        output_bucket = request_json.get('output_bucket') or request_args.get('output_bucket') or \
                        'infinityai-backtest-results'
        
        # Run pipeline
        orchestrator = BacktestOrchestrator(
            project_id='galvanic-pulsar-482815-h0',
            data_source=data_source,
            output_bucket=output_bucket
        )
        
        results = orchestrator.run_pipeline(symbols)
        
        return json.dumps({
            'status': 'success',
            'timestamp': str(__import__('datetime').datetime.now()),
            'results': results
        }), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    # For local testing
    from flask import Flask, Request
    
    app = Flask(__name__)
    
    @app.route('/', methods=['POST', 'GET'])
    def handler():
        return main(Request({}))
    
    app.run(debug=True, port=8080)
