"use strict";
/**
 * InfinityAI.Pro - Cloud Functions Index
 *
 * Main entry point for all Firebase Cloud Functions
 * Exports: Authentication, Trading, Portfolio Analysis functions
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.fetchAccountData = exports.getUserCredentials = exports.storeUserCredentials = exports.verifyCoupon = exports.getDhanOverview = exports.getBatchAiSignals = exports.getGeminiAnalysis = exports.getVertexAiAnalysis = exports.getAiSignals = exports.analyzePortfolio = exports.stopTrading = exports.startTrading = void 0;
const admin = __importStar(require("firebase-admin"));
// Initialize Firebase Admin SDK
admin.initializeApp();
// Export all functions
var startTrading_1 = require("./startTrading");
Object.defineProperty(exports, "startTrading", { enumerable: true, get: function () { return startTrading_1.startTrading; } });
Object.defineProperty(exports, "stopTrading", { enumerable: true, get: function () { return startTrading_1.stopTrading; } });
var analyzePortfolio_1 = require("./analyzePortfolio");
Object.defineProperty(exports, "analyzePortfolio", { enumerable: true, get: function () { return analyzePortfolio_1.analyzePortfolio; } });
Object.defineProperty(exports, "getAiSignals", { enumerable: true, get: function () { return analyzePortfolio_1.getAiSignals; } });
Object.defineProperty(exports, "getVertexAiAnalysis", { enumerable: true, get: function () { return analyzePortfolio_1.getVertexAiAnalysis; } });
Object.defineProperty(exports, "getGeminiAnalysis", { enumerable: true, get: function () { return analyzePortfolio_1.getGeminiAnalysis; } });
Object.defineProperty(exports, "getBatchAiSignals", { enumerable: true, get: function () { return analyzePortfolio_1.getBatchAiSignals; } });
Object.defineProperty(exports, "getDhanOverview", { enumerable: true, get: function () { return analyzePortfolio_1.getDhanOverview; } });
// Export new trading setup functions
var verifyCoupon_1 = require("./verifyCoupon");
Object.defineProperty(exports, "verifyCoupon", { enumerable: true, get: function () { return verifyCoupon_1.verifyCoupon; } });
var userCredentials_1 = require("./userCredentials");
Object.defineProperty(exports, "storeUserCredentials", { enumerable: true, get: function () { return userCredentials_1.storeUserCredentials; } });
Object.defineProperty(exports, "getUserCredentials", { enumerable: true, get: function () { return userCredentials_1.getUserCredentials; } });
var accountData_1 = require("./accountData");
Object.defineProperty(exports, "fetchAccountData", { enumerable: true, get: function () { return accountData_1.fetchAccountData; } });
//# sourceMappingURL=index.js.map