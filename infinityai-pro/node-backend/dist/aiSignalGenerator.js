"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AISignalGenerator = void 0;
const axios_1 = __importDefault(require("axios"));
class AISignalGenerator {
    constructor(config = {}) {
        this.runpodUrl = config.runpodUrl;
        this.huggingFaceToken = config.huggingFaceToken;
        this.ollamaUrl = config.ollamaUrl || "http://localhost:11434";
    }
    /**
     * Generate comprehensive BTC trading signal using AI components
     */
    async generateBTCSignal(btcPrice, chartImage) {
        const timestamp = new Date();
        // Gather AI components in parallel
        const [yoloResult, whisperResult, llmResult] = await Promise.allSettled([
            this.analyzeChartWithYOLO(chartImage),
            this.analyzeNewsWithWhisper(),
            this.analyzeMarketWithLLM(btcPrice)
        ]);
        const components = {};
        // Extract YOLO analysis
        if (yoloResult.status === "fulfilled" && yoloResult.value) {
            components.yoloAnalysis = yoloResult.value;
        }
        // Extract Whisper sentiment
        if (whisperResult.status === "fulfilled" && whisperResult.value) {
            components.whisperSentiment = whisperResult.value;
        }
        // Extract LLM analysis
        if (llmResult.status === "fulfilled" && llmResult.value) {
            components.llmAnalysis = llmResult.value;
        }
        // Combine signals into final direction and confidence
        const { direction, confidence, reasoning } = this.combineAISignals(components);
        return {
            direction,
            confidence,
            btcPrice,
            timestamp,
            reasoning,
            components
        };
    }
    /**
     * Analyze BTC chart using YOLO for pattern recognition
     */
    async analyzeChartWithYOLO(chartImage) {
        if (!chartImage || !this.runpodUrl) {
            return undefined;
        }
        try {
            const response = await axios_1.default.post(`${this.runpodUrl}/yolo/analyze`, chartImage, {
                headers: { "Content-Type": "application/octet-stream" },
                timeout: 10000
            });
            const { pattern, confidence, direction } = response.data;
            return {
                pattern,
                confidence,
                direction
            };
        }
        catch (error) {
            console.error("YOLO analysis failed:", error);
            return undefined;
        }
    }
    /**
     * Analyze crypto news sentiment using Whisper
     */
    async analyzeNewsWithWhisper() {
        if (!this.runpodUrl) {
            return undefined;
        }
        try {
            // Get recent crypto news headlines (mock implementation)
            const newsHeadlines = await this.getCryptoNewsHeadlines();
            if (newsHeadlines.length === 0) {
                return undefined;
            }
            // Analyze sentiment using Whisper (mock implementation)
            const response = await axios_1.default.post(`${this.runpodUrl}/whisper/sentiment`, {
                text: newsHeadlines.join(" ")
            }, {
                timeout: 10000
            });
            const { sentiment, confidence, keyPhrases } = response.data;
            return {
                sentiment,
                confidence,
                keyPhrases
            };
        }
        catch (error) {
            console.error("Whisper sentiment analysis failed:", error);
            return undefined;
        }
    }
    /**
     * Analyze market conditions using LLM
     */
    async analyzeMarketWithLLM(btcPrice) {
        try {
            const marketData = await this.getMarketData();
            const prompt = this.buildLLMPrompt(btcPrice, marketData);
            let response;
            if (this.ollamaUrl) {
                // Use local Ollama LLM
                response = await axios_1.default.post(`${this.ollamaUrl}/api/generate`, {
                    model: "llama3.2",
                    prompt,
                    stream: false
                });
            }
            else if (this.huggingFaceToken) {
                // Use Hugging Face API
                response = await axios_1.default.post("https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium", { inputs: prompt }, {
                    headers: { Authorization: `Bearer ${this.huggingFaceToken}` }
                });
            }
            else {
                // Fallback mock analysis
                response = {
                    data: {
                        response: this.generateMockLLMAnalysis(btcPrice, marketData)
                    }
                };
            }
            const analysis = this.parseLLMResponse(response.data.response || response.data);
            return {
                summary: analysis.summary,
                direction: analysis.direction,
                confidence: analysis.confidence,
                reasoning: analysis.reasoning
            };
        }
        catch (error) {
            console.error("LLM analysis failed:", error);
            return undefined;
        }
    }
    /**
     * Combine all AI signals into final trading decision
     */
    combineAISignals(components) {
        let bullScore = 0;
        let bearScore = 0;
        const reasons = [];
        // YOLO pattern analysis (40% weight)
        if (components.yoloAnalysis) {
            const weight = 0.4;
            if (components.yoloAnalysis.direction === "bull") {
                bullScore += weight * components.yoloAnalysis.confidence;
                reasons.push(`YOLO detected bullish ${components.yoloAnalysis.pattern} pattern`);
            }
            else if (components.yoloAnalysis.direction === "bear") {
                bearScore += weight * components.yoloAnalysis.confidence;
                reasons.push(`YOLO detected bearish ${components.yoloAnalysis.pattern} pattern`);
            }
        }
        // Whisper sentiment analysis (30% weight)
        if (components.whisperSentiment) {
            const weight = 0.3;
            if (components.whisperSentiment.sentiment === "positive") {
                bullScore += weight * components.whisperSentiment.confidence;
                reasons.push(`News sentiment is positive: ${components.whisperSentiment.keyPhrases.join(", ")}`);
            }
            else if (components.whisperSentiment.sentiment === "negative") {
                bearScore += weight * components.whisperSentiment.confidence;
                reasons.push(`News sentiment is negative: ${components.whisperSentiment.keyPhrases.join(", ")}`);
            }
        }
        // LLM analysis (30% weight)
        if (components.llmAnalysis) {
            const weight = 0.3;
            if (components.llmAnalysis.direction === "bull") {
                bullScore += weight * components.llmAnalysis.confidence;
                reasons.push(components.llmAnalysis.reasoning);
            }
            else if (components.llmAnalysis.direction === "bear") {
                bearScore += weight * components.llmAnalysis.confidence;
                reasons.push(components.llmAnalysis.reasoning);
            }
        }
        // Determine final direction and confidence
        const totalScore = bullScore + bearScore;
        const confidence = totalScore > 0 ? Math.min(totalScore, 1) : 0.5;
        let direction;
        let finalReasoning;
        if (bullScore > bearScore) {
            direction = "bull";
            finalReasoning = `Bullish signal (Bull:${bullScore.toFixed(2)}, Bear:${bearScore.toFixed(2)}): ${reasons.join(". ")}`;
        }
        else if (bearScore > bullScore) {
            direction = "bear";
            finalReasoning = `Bearish signal (Bull:${bullScore.toFixed(2)}, Bear:${bearScore.toFixed(2)}): ${reasons.join(". ")}`;
        }
        else {
            // Neutral - default to current trend or hold
            direction = Math.random() > 0.5 ? "bull" : "bear";
            finalReasoning = `Neutral signals, taking ${direction} position: ${reasons.join(". ")}`;
        }
        return {
            direction,
            confidence,
            reasoning: finalReasoning
        };
    }
    /**
     * Get recent crypto news headlines
     */
    async getCryptoNewsHeadlines() {
        try {
            // Mock implementation - replace with actual news API
            const mockHeadlines = [
                "Bitcoin surges past $45,000 as institutional adoption grows",
                "Ethereum upgrades boost network efficiency",
                "Crypto market shows resilience despite regulatory concerns"
            ];
            return mockHeadlines;
        }
        catch (error) {
            console.error("Failed to fetch news headlines:", error);
            return [];
        }
    }
    /**
     * Get market data for LLM analysis
     */
    async getMarketData() {
        // Mock market data - replace with actual market data API
        return {
            btcPrice: 4500000,
            btcVolume24h: 1000000000,
            marketCap: 850000000000,
            fearGreedIndex: 65,
            dominance: 45.2
        };
    }
    /**
     * Build LLM prompt for market analysis
     */
    buildLLMPrompt(btcPrice, marketData) {
        return `Analyze the current Bitcoin market conditions and provide a trading recommendation.

Current BTC Price: ₹${btcPrice.toLocaleString()}
24h Volume: ₹${marketData.btcVolume24h.toLocaleString()}
Market Cap: ₹${marketData.marketCap.toLocaleString()}
Fear & Greed Index: ${marketData.fearGreedIndex}/100
BTC Dominance: ${marketData.dominance}%

Based on this data, should we expect BTC to go UP (bullish) or DOWN (bearish) in the next 1-2 weeks?
Provide your analysis in the following format:
DIRECTION: [BULL/BEAR]
CONFIDENCE: [0-1]
REASONING: [brief explanation]
SUMMARY: [one sentence summary]`;
    }
    /**
     * Parse LLM response
     */
    parseLLMResponse(response) {
        // Mock parsing - replace with actual LLM response parsing
        const isBullish = response.toLowerCase().includes("bull") ||
            response.toLowerCase().includes("up") ||
            Math.random() > 0.4;
        return {
            direction: isBullish ? "bull" : "bear",
            confidence: 0.7 + Math.random() * 0.2,
            reasoning: "AI analysis based on market conditions and technical factors",
            summary: isBullish ? "BTC showing bullish momentum" : "BTC facing bearish pressure"
        };
    }
    /**
     * Generate mock LLM analysis for fallback
     */
    generateMockLLMAnalysis(btcPrice, marketData) {
        const isBullish = Math.random() > 0.5;
        return `DIRECTION: ${isBullish ? "BULL" : "BEAR"}
CONFIDENCE: ${0.6 + Math.random() * 0.3}
REASONING: Based on current market conditions and technical analysis
SUMMARY: ${isBullish ? "Bullish momentum detected" : "Bearish signals present"}`;
    }
}
exports.AISignalGenerator = AISignalGenerator;
