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
exports.syncHoldings = exports.analyzePortfolio = exports.stopTrading = exports.startTrading = exports.saveDhanCredentials = exports.submitDhanCredentialsV2 = void 0;
const admin = __importStar(require("firebase-admin"));
// Initialize Firebase Admin SDK
admin.initializeApp();
// Export all functions
var storeCredentials_1 = require("./storeCredentials");
Object.defineProperty(exports, "submitDhanCredentialsV2", { enumerable: true, get: function () { return storeCredentials_1.submitDhanCredentialsV2; } });
Object.defineProperty(exports, "saveDhanCredentials", { enumerable: true, get: function () { return storeCredentials_1.saveDhanCredentials; } });
var startTrading_1 = require("./startTrading");
Object.defineProperty(exports, "startTrading", { enumerable: true, get: function () { return startTrading_1.startTrading; } });
Object.defineProperty(exports, "stopTrading", { enumerable: true, get: function () { return startTrading_1.stopTrading; } });
var analyzePortfolio_1 = require("./analyzePortfolio");
Object.defineProperty(exports, "analyzePortfolio", { enumerable: true, get: function () { return analyzePortfolio_1.analyzePortfolio; } });
Object.defineProperty(exports, "syncHoldings", { enumerable: true, get: function () { return analyzePortfolio_1.syncHoldings; } });
//# sourceMappingURL=index.js.map