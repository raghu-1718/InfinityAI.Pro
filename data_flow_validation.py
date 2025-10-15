#!/usr/bin/env python3
"""
InfinityAI.Pro - Real-time Data Flow Validation
End-to-end validation of market data → AI predictions → trading signals → dashboard rendering
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List

class DataFlowValidator:
    def __init__(self):
        self.services = {
            'Engine A': 'https://engine-a-573866363639-573866363639.us-central1.run.app',
            'Engine B': 'https://engine-b-573866363639-573866363639.us-central1.run.app', 
            'Engine C': 'https://engine-c-573866363639-573866363639.us-central1.run.app',
            'Engine D': 'https://engine-d-573866363639-573866363639.us-central1.run.app',
            'Frontend': 'https://infinityai-pro-frontend-573866363639.us-central1.run.app'
        }
        
    async def test_market_data_ingestion(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test real-time market data ingestion and processing"""
        print("📈 Testing Market Data Ingestion (Engine A)...")
        
        results = {
            'market_signals': {'status': 'failed', 'data': None},
            'specific_symbols': {'status': 'failed', 'data': None},
            'technical_indicators': {'status': 'failed', 'data': None},
            'real_time_updates': {'status': 'failed', 'data': None}
        }
        
        base_url = self.services['Engine A']
        
        # Test market signals endpoint
        try:
            async with session.get(f"{base_url}/api/signals") as response:
                if response.status == 200:
                    data = await response.json()
                    results['market_signals'] = {
                        'status': 'success',
                        'data': data,
                        'signal_count': len(data.get('signals', [])) if 'signals' in data else 0,
                        'symbols_covered': list(data.get('signals', {}).keys()) if isinstance(data.get('signals'), dict) else []
                    }
                    print("   ✅ Market signals: ACTIVE")
                else:
                    print(f"   ❌ Market signals: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Market signals: {str(e)}")
        
        # Test specific symbol data
        symbols = ['NIFTY', 'BANKNIFTY', 'TCS', 'RELIANCE']
        symbol_results = {}
        
        for symbol in symbols:
            try:
                async with session.get(f"{base_url}/api/market-data/{symbol}") as response:
                    if response.status == 200:
                        symbol_data = await response.json()
                        symbol_results[symbol] = {
                            'status': 'success',
                            'last_price': symbol_data.get('price', 'N/A'),
                            'indicators': list(symbol_data.keys()) if isinstance(symbol_data, dict) else []
                        }
                        print(f"   ✅ {symbol}: Live data available")
                    else:
                        symbol_results[symbol] = {'status': 'failed', 'http_code': response.status}
                        print(f"   ⚠️ {symbol}: HTTP {response.status}")
            except Exception as e:
                symbol_results[symbol] = {'status': 'error', 'error': str(e)}
                print(f"   ❌ {symbol}: {str(e)}")
        
        results['specific_symbols'] = {
            'status': 'success' if any(s['status'] == 'success' for s in symbol_results.values()) else 'failed',
            'data': symbol_results
        }
        
        return results

    async def test_ai_predictions(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test AI prediction generation and model inference"""
        print("🧠 Testing AI Prediction Generation (Engine B)...")
        
        results = {
            'prediction_signals': {'status': 'failed', 'data': None},
            'model_status': {'status': 'failed', 'data': None},
            'feature_processing': {'status': 'failed', 'data': None},
            'confidence_scoring': {'status': 'failed', 'data': None}
        }
        
        base_url = self.services['Engine B']
        
        # Test AI prediction signals
        try:
            async with session.get(f"{base_url}/api/ai-signals") as response:
                if response.status == 200:
                    data = await response.json()
                    results['prediction_signals'] = {
                        'status': 'success',
                        'data': data,
                        'signals_count': len(data.get('signals', [])),
                        'models_active': data.get('models_active', False),
                        'sample_prediction': data.get('signals', [{}])[0] if data.get('signals') else None
                    }
                    
                    # Extract confidence scoring info
                    if data.get('signals') and len(data['signals']) > 0:
                        sample = data['signals'][0]
                        if 'confidence' in sample:
                            results['confidence_scoring'] = {
                                'status': 'success',
                                'avg_confidence': sample.get('confidence', 0),
                                'confidence_range': 'Available'
                            }
                            
                        if 'features_used' in sample:
                            results['feature_processing'] = {
                                'status': 'success',
                                'features_count': len(sample['features_used']),
                                'features': sample['features_used']
                            }
                            
                    print("   ✅ AI predictions: GENERATING")
                else:
                    print(f"   ❌ AI predictions: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ AI predictions: {str(e)}")
        
        # Test model status
        try:
            async with session.get(f"{base_url}/api/models/status") as response:
                if response.status == 200:
                    model_data = await response.json()
                    results['model_status'] = {
                        'status': 'success',
                        'data': model_data,
                        'models_loaded': model_data.get('models_loaded', 0),
                        'inference_active': model_data.get('inference_active', False)
                    }
                    print("   ✅ Model status: LOADED")
                else:
                    print(f"   ⚠️ Model status: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Model status: {str(e)}")
            
        return results

    async def test_trading_signals(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test trading signal processing and order execution"""
        print("💼 Testing Trading Signal Processing (Engine C)...")
        
        results = {
            'order_placement': {'status': 'failed', 'data': None},
            'order_status': {'status': 'failed', 'data': None},
            'demo_mode': {'status': 'failed', 'data': None},
            'risk_management': {'status': 'failed', 'data': None}
        }
        
        base_url = self.services['Engine C']
        
        # Test demo order placement
        try:
            order_data = {
                'symbol': 'NIFTY',
                'quantity': 1,
                'order_type': 'BUY',
                'demo': True
            }
            
            async with session.post(f"{base_url}/api/orders/place", json=order_data) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    results['order_placement'] = {
                        'status': 'success',
                        'data': data,
                        'order_id': data.get('order_id'),
                        'demo_mode': data.get('demo_mode', True)
                    }
                    
                    if data.get('demo_mode'):
                        results['demo_mode'] = {
                            'status': 'success',
                            'message': 'Demo mode active - safe for testing'
                        }
                        
                    print("   ✅ Order placement: FUNCTIONAL")
                else:
                    print(f"   ❌ Order placement: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Order placement: {str(e)}")
        
        # Test order status retrieval
        try:
            async with session.get(f"{base_url}/api/orders/demo") as response:
                if response.status == 200:
                    order_status = await response.json()
                    results['order_status'] = {
                        'status': 'success',
                        'data': order_status,
                        'active_orders': len(order_status.get('orders', [])) if isinstance(order_status.get('orders'), list) else 0
                    }
                    print("   ✅ Order status: ACCESSIBLE")
                else:
                    print(f"   ⚠️ Order status: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Order status: {str(e)}")
            
        return results

    async def test_chatbot_orchestration(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test chatbot multi-engine orchestration"""
        print("🤖 Testing Chatbot Multi-engine Orchestration (Engine D)...")
        
        results = {
            'system_coordination': {'status': 'failed', 'data': None},
            'data_integration': {'status': 'failed', 'data': None},
            'response_quality': {'status': 'failed', 'data': None}
        }
        
        base_url = self.services['Engine D']
        
        # Test system coordination query
        try:
            query_data = {
                'message': 'Give me a complete system status with market data, AI predictions, and trading status',
                'user_id': 'data_flow_test',
                'require_all_engines': True
            }
            
            async with session.post(f"{base_url}/api/chat", json=query_data) as response:
                if response.status == 200:
                    chat_response = await response.json()
                    response_text = chat_response.get('response', '')
                    
                    results['system_coordination'] = {
                        'status': 'success',
                        'data': chat_response,
                        'response_length': len(response_text),
                        'engines_mentioned': sum(1 for engine in ['market', 'ai', 'trading', 'prediction'] if engine.lower() in response_text.lower())
                    }
                    
                    # Check data integration quality
                    if len(response_text) > 100 and any(keyword in response_text.lower() for keyword in ['nifty', 'signal', 'prediction', 'price']):
                        results['data_integration'] = {
                            'status': 'success',
                            'message': 'Multi-engine data successfully integrated in response'
                        }
                        
                    results['response_quality'] = {
                        'status': 'success',
                        'coherent': len(response_text) > 50,
                        'contextual': 'market' in response_text.lower() or 'trading' in response_text.lower()
                    }
                    
                    print("   ✅ System coordination: ACTIVE")
                else:
                    print(f"   ❌ System coordination: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ System coordination: {str(e)}")
            
        return results

    async def test_dashboard_rendering(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test frontend dashboard data rendering"""
        print("🖥️ Testing Dashboard Data Rendering (Frontend)...")
        
        results = {
            'dashboard_api': {'status': 'failed', 'data': None},
            'data_aggregation': {'status': 'failed', 'data': None},
            'ui_integration': {'status': 'failed', 'data': None}
        }
        
        base_url = self.services['Frontend']
        
        # Test dashboard data API
        try:
            async with session.get(f"{base_url}/api/dashboard/data") as response:
                if response.status == 200:
                    dashboard_data = await response.json()
                    results['dashboard_api'] = {
                        'status': 'success',
                        'data': dashboard_data,
                        'data_sections': list(dashboard_data.keys()) if isinstance(dashboard_data, dict) else []
                    }
                    
                    # Check data aggregation
                    expected_sections = ['market_data', 'ai_predictions', 'trading_signals', 'system_status']
                    available_sections = [s for s in expected_sections if s in dashboard_data] if isinstance(dashboard_data, dict) else []
                    
                    results['data_aggregation'] = {
                        'status': 'success' if len(available_sections) > 0 else 'partial',
                        'available_sections': available_sections,
                        'integration_score': len(available_sections) / len(expected_sections) * 100
                    }
                    
                    results['ui_integration'] = {
                        'status': 'success',
                        'message': 'Dashboard API responding with structured data'
                    }
                    
                    print("   ✅ Dashboard rendering: FUNCTIONAL")
                else:
                    print(f"   ⚠️ Dashboard API: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Dashboard rendering: {str(e)}")
            
        return results

    async def run_end_to_end_validation(self) -> Dict[str, Any]:
        """Run complete end-to-end data flow validation"""
        print("🔄 Starting End-to-End Data Flow Validation")
        print("=" * 70)
        
        connector = aiohttp.TCPConnector(limit=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            
            # Execute all validation tests
            market_data_results = await self.test_market_data_ingestion(session)
            await asyncio.sleep(1)
            
            ai_prediction_results = await self.test_ai_predictions(session)  
            await asyncio.sleep(1)
            
            trading_results = await self.test_trading_signals(session)
            await asyncio.sleep(1)
            
            chatbot_results = await self.test_chatbot_orchestration(session)
            await asyncio.sleep(1)
            
            dashboard_results = await self.test_dashboard_rendering(session)
            
        # Compile comprehensive results
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'validation_type': 'End-to-End Data Flow Validation',
            'pipeline_stages': {
                'market_data_ingestion': market_data_results,
                'ai_prediction_generation': ai_prediction_results,
                'trading_signal_processing': trading_results,
                'chatbot_orchestration': chatbot_results,
                'dashboard_rendering': dashboard_results
            }
        }
        
        return validation_results

    def calculate_data_flow_health(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall data flow health metrics"""
        
        total_tests = 0
        passed_tests = 0
        
        for stage_name, stage_results in results['pipeline_stages'].items():
            for test_name, test_result in stage_results.items():
                total_tests += 1
                if test_result.get('status') == 'success':
                    passed_tests += 1
        
        health_percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Assess pipeline integrity
        pipeline_stages = ['market_data_ingestion', 'ai_prediction_generation', 'trading_signal_processing', 'chatbot_orchestration']
        
        critical_flows = []
        for stage in pipeline_stages:
            stage_health = sum(1 for test in results['pipeline_stages'][stage].values() if test.get('status') == 'success')
            stage_total = len(results['pipeline_stages'][stage])
            stage_percentage = (stage_health / stage_total * 100) if stage_total > 0 else 0
            
            critical_flows.append({
                'stage': stage,
                'health_percentage': stage_percentage,
                'status': '✅ OPERATIONAL' if stage_percentage >= 70 else '⚠️ DEGRADED' if stage_percentage >= 40 else '❌ CRITICAL'
            })
        
        return {
            'overall_data_flow_health': round(health_percentage, 2),
            'tests_passed': f"{passed_tests}/{total_tests}",
            'pipeline_integrity': critical_flows,
            'production_ready': health_percentage >= 75 and all(flow['health_percentage'] >= 60 for flow in critical_flows)
        }

async def main():
    validator = DataFlowValidator()
    
    print("🔄 InfinityAI.Pro - Real-time Data Flow Validation")
    print("Testing complete pipeline: Market Data → AI → Trading → Dashboard")
    
    # Run comprehensive validation
    results = await validator.run_end_to_end_validation()
    
    # Calculate health metrics
    health_metrics = validator.calculate_data_flow_health(results)
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("📊 DATA FLOW VALIDATION RESULTS")
    print("=" * 70)
    
    print(f"Overall Data Flow Health: {health_metrics['overall_data_flow_health']}%")
    print(f"Tests Passed: {health_metrics['tests_passed']}")
    print(f"Production Ready: {'✅ YES' if health_metrics['production_ready'] else '⚠️ NEEDS ATTENTION'}")
    
    print("\n🔍 Pipeline Stage Health:")
    for flow in health_metrics['pipeline_integrity']:
        print(f"   {flow['status']} {flow['stage']}: {flow['health_percentage']}%")
    
    # Save detailed results
    results['health_assessment'] = health_metrics
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data_flow_validation_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📋 Detailed validation report saved: {filename}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())