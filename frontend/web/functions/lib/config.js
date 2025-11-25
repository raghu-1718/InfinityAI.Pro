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
    // Engine Analytics: AI/ML processing
    ANALYTICS: process.env.ENGINE_ANALYTICS_URL || "https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app",
    // Engine Core: Market data ingestion
    CORE: process.env.ENGINE_CORE_URL || "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app",
    // Engine Execution: Secure trade execution
    EXECUTION: process.env.ENGINE_EXECUTION_URL || "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app",
};
//# sourceMappingURL=config.js.map