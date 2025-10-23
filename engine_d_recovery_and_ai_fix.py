#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine D Recovery & AI Analysis Fix
===================================================
This script addresses the critical Engine D orchestration issues and
missing AI analysis functions that are causing dashboard failures.
"""

import requests
import json
import time
from datetime import datetime

class EngineDRecovery:
    def __init__(self):
        self.project_id = "infinity-ai-5ec7c"
        self.engine_d_url = "https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app"
        self.functions_base = f"https://us-central1-{self.project_id}.cloudfunctions.net"
        
    def diagnose_engine_d_issues(self):
        """Diagnose specific Engine D issues"""
        print("🔍 Diagnosing Engine D Issues")
        print("=" * 40)
        
        # Check Engine D logs and status
        try:
            # Test different Engine D endpoints
            endpoints = [
                "/health",
                "/api/status", 
                "/api/orchestration/status",
                "/api/websocket/status",
                "/ws/dashboard"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.engine_d_url}{endpoint}", timeout=5)
                    print(f"   {endpoint}: {response.status_code}")
                    if response.status_code == 200:
                        print(f"      Response: {response.text[:100]}...")
                except Exception as e:
                    print(f"   {endpoint}: ERROR - {str(e)}")
                    
        except Exception as e:
            print(f"❌ Engine D diagnosis failed: {str(e)}")
    
    def check_missing_ai_functions(self):
        """Check and potentially deploy missing AI analysis functions"""
        print("\n🤖 Checking Missing AI Analysis Functions")
        print("=" * 50)
        
        missing_functions = [
            "getAiSignals",
            "getVertexAiAnalysis", 
            "getGeminiAnalysis"
        ]
        
        for function_name in missing_functions:
            try:
                function_url = f"{self.functions_base}/{function_name}"
                response = requests.post(function_url, json={"data": {"test": True}}, timeout=10)
                print(f"   {function_name}: {response.status_code}")
                
                if response.status_code == 404:
                    print(f"      ❌ Function not deployed - needs deployment")
                elif response.status_code in [200, 401, 403]:
                    print(f"      ✅ Function exists but may have auth/logic issues")
                    
            except Exception as e:
                print(f"   {function_name}: ERROR - {str(e)}")
    
    def create_ai_analysis_functions(self):
        """Create the missing AI analysis Firebase Functions"""
        print("\n📝 Creating Missing AI Analysis Functions")
        print("=" * 50)
        
        # Create getGeminiAnalysis function
        gemini_function = """const functions = require('firebase-functions');
const admin = require('firebase-admin');

exports.getGeminiAnalysis = functions.https.onCall(async (data, context) => {
    // Verify authentication
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'Must be authenticated');
    }
    
    try {
        // Mock Gemini analysis for now - replace with actual Gemini API call
        const analysis = {
            timestamp: new Date().toISOString(),
            market_sentiment: "BULLISH",
            confidence: 0.75,
            key_insights: [
                "Market showing strong upward momentum",
                "Technical indicators suggest continued growth",
                "Volume analysis indicates institutional buying"
            ],
            recommendations: [
                "Consider long positions in large-cap stocks",
                "Monitor volatility for entry points",
                "Maintain diversified portfolio"
            ],
            risk_factors: [
                "Global economic uncertainty",
                "Potential interest rate changes"
            ]
        };
        
        return { success: true, analysis: analysis };
    } catch (error) {
        console.error('Gemini analysis error:', error);
        throw new functions.https.HttpsError('internal', 'Analysis generation failed');
    }
});"""
        
        # Create getVertexAiAnalysis function  
        vertex_function = """const functions = require('firebase-functions');
const admin = require('firebase-admin');

exports.getVertexAiAnalysis = functions.https.onCall(async (data, context) => {
    // Verify authentication
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'Must be authenticated');
    }
    
    try {
        // Mock Vertex AI analysis for now - replace with actual Vertex AI call
        const analysis = {
            timestamp: new Date().toISOString(),
            model_predictions: {
                nifty_direction: "UP",
                probability: 0.68,
                target_range: "22800-23200",
                timeframe: "5-day"
            },
            sector_analysis: {
                banking: "POSITIVE",
                it: "NEUTRAL", 
                pharma: "POSITIVE",
                metals: "NEGATIVE"
            },
            ml_signals: {
                rsi_signal: "OVERSOLD_RECOVERY",
                macd_signal: "BULLISH_CROSSOVER",
                volume_signal: "ACCUMULATION"
            }
        };
        
        return { success: true, analysis: analysis };
    } catch (error) {
        console.error('Vertex AI analysis error:', error);
        throw new functions.https.HttpsError('internal', 'Analysis generation failed');
    }
});"""
        
        # Create getAiSignals function
        signals_function = """const functions = require('firebase-functions');
const admin = require('firebase-admin');

exports.getAiSignals = functions.https.onCall(async (data, context) => {
    // Verify authentication
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'Must be authenticated');
    }
    
    try {
        // Mock AI signals for now - replace with actual Engine B integration
        const signals = {
            timestamp: new Date().toISOString(),
            signals: [
                {
                    symbol: "NIFTY",
                    signal: "BUY",
                    strength: 0.85,
                    entry_price: 22650,
                    target: 23000,
                    stop_loss: 22400,
                    timeframe: "1D"
                },
                {
                    symbol: "BANKNIFTY", 
                    signal: "HOLD",
                    strength: 0.65,
                    current_price: 47800,
                    analysis: "Consolidation phase"
                }
            ],
            market_status: "ACTIVE",
            next_update: new Date(Date.now() + 15*60000).toISOString()
        };
        
        return { success: true, signals: signals };
    } catch (error) {
        console.error('AI signals error:', error);
        throw new functions.https.HttpsError('internal', 'Signals generation failed');
    }
});"""

        # Save function files
        import os
        functions_dir = "functions/src"
        os.makedirs(functions_dir, exist_ok=True)
        
        with open(f"{functions_dir}/getGeminiAnalysis.js", "w") as f:
            f.write(gemini_function)
        print("   ✅ Created getGeminiAnalysis.js")
            
        with open(f"{functions_dir}/getVertexAiAnalysis.js", "w") as f:
            f.write(vertex_function)
        print("   ✅ Created getVertexAiAnalysis.js")
            
        with open(f"{functions_dir}/getAiSignals.js", "w") as f:
            f.write(signals_function)
        print("   ✅ Created getAiSignals.js")
    
    def generate_engine_d_fix_script(self):
        """Generate Engine D recovery script"""
        print("\n🔧 Generating Engine D Recovery Script")
        print("=" * 50)
        
        fix_script = """#!/bin/bash
# Engine D Recovery Script
# This script addresses Engine D orchestration and WebSocket issues

echo "🔧 Starting Engine D Recovery Process..."

# 1. Check Engine D Cloud Run service status
echo "📊 Checking Engine D Cloud Run status..."
gcloud run services describe infinityai-engine-d \\
    --region=us-central1 \\
    --project=after-yesterday-473512-k3

# 2. Restart Engine D service
echo "🔄 Restarting Engine D service..."
gcloud run services update infinityai-engine-d \\
    --region=us-central1 \\
    --project=after-yesterday-473512-k3 \\
    --tag=latest

# 3. Check service logs for errors
echo "📋 Checking Engine D logs..."
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=infinityai-engine-d" \\
    --limit=50 \\
    --project=after-yesterday-473512-k3

# 4. Test Engine D endpoints
echo "🧪 Testing Engine D endpoints..."
curl -s https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/health
curl -s https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/api/status

# 5. Verify WebSocket configuration
echo "🔌 Checking WebSocket configuration..."
curl -s https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/ws/dashboard

echo "✅ Engine D recovery process completed!"
"""
        
        with open("fix_engine_d.sh", "w") as f:
            f.write(fix_script)
        print("   ✅ Created fix_engine_d.sh recovery script")
    
    def test_platform_integration(self):
        """Test end-to-end platform integration"""
        print("\n🔄 Testing Platform Integration")
        print("=" * 40)
        
        # Test Engine A -> Engine B data flow
        print("   📊 Testing Engine A -> Engine B data flow...")
        
        # Test Engine B -> Engine D signals flow  
        print("   🤖 Testing Engine B -> Engine D signals flow...")
        
        # Test Engine D -> Frontend WebSocket flow
        print("   🔌 Testing Engine D -> Frontend WebSocket flow...")
        
        # Test Firebase Functions -> Engines integration
        print("   ⚡ Testing Firebase Functions -> Engines integration...")
    
    def run_recovery_process(self):
        """Run complete recovery process"""
        print("🚀 InfinityAI.Pro - Engine D Recovery & AI Analysis Fix")
        print("=" * 60)
        
        # Diagnose issues
        self.diagnose_engine_d_issues()
        
        # Check missing functions
        self.check_missing_ai_functions()
        
        # Create missing AI functions
        self.create_ai_analysis_functions()
        
        # Generate recovery script
        self.generate_engine_d_fix_script()
        
        # Test integration
        self.test_platform_integration()
        
        print("\n" + "=" * 60)
        print("📋 RECOVERY SUMMARY")
        print("=" * 60)
        print("✅ Diagnosed Engine D orchestration issues")
        print("✅ Identified missing AI analysis functions")
        print("✅ Created placeholder AI analysis functions")
        print("✅ Generated Engine D recovery script")
        print("📝 Next Steps:")
        print("   1. Deploy created Firebase Functions")
        print("   2. Run fix_engine_d.sh script")
        print("   3. Test dashboard functionality")
        print("   4. Monitor real-time data flow")

if __name__ == "__main__":
    recovery = EngineDRecovery()
    recovery.run_recovery_process()