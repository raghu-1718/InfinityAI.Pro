"use strict";
/**
 * Centralized Configuration for Backend Engines
 *
 * This file exports the URLs for all backend microservices,
 * sourcing them from environment variables for security and flexibility.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ENGINE_URLS = void 0;
exports.ENGINE_URLS = {
    // Engine A: Market data ingestion
    A: process.env.ENGINE_A_URL || "https://infinityai-engine-a-26140490557.us-central1.run.app",
    // Engine B: AI/ML processing
    B: process.env.ENGINE_B_URL || "https://infinityai-engine-b-26140490557.us-central1.run.app",
    // Engine C: Secure trade execution (using custom domain)
    C: process.env.ENGINE_C_URL || "https://api.infinityai.pro",
    // Engine D: AI chatbot and orchestration
    D: process.env.ENGINE_D_URL || "https://infinityai-engine-d-26140490557.us-central1.run.app",
};
//# sourceMappingURL=config.js.map