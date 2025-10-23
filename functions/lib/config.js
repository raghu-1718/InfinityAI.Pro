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
    A: process.env.ENGINE_A_URL || "https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app",
    // Engine B: AI/ML processing
    B: process.env.ENGINE_B_URL || "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app",
    // Engine C: Secure trade execution
    C: process.env.ENGINE_C_URL || "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app",
    // Engine D: AI chatbot and orchestration
    D: process.env.ENGINE_D_URL || "https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app",
};
//# sourceMappingURL=config.js.map