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
    // Engine A: Orchestration & Analytics
    ANALYTICS: process.env.ENGINE_ANALYTICS_URL || "https://engine-a.infinityai.pro",
    // Engine B: AI/ML & Market Data
    CORE: process.env.ENGINE_CORE_URL || "https://engine-b.infinityai.pro",
    // Engine C: Trade Execution
    EXECUTION: process.env.ENGINE_EXECUTION_URL || "https://engine-c.infinityai.pro",
};
//# sourceMappingURL=config.js.map