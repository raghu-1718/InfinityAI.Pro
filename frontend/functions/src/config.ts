/**
 * Centralized Configuration for Backend Engines
 *
 * This file exports the URLs for all backend microservices,
 * sourcing them from environment variables for security and flexibility.
 */

export const ENGINE_URLS = {
  // Engine A: Orchestration & Analytics
  // Engine A: Orchestration & Analytics
  ANALYTICS:
    process.env.ENGINE_ANALYTICS_URL ||
    "https://engine-a-mfvaq54jjq-uc.a.run.app",
  // Engine B: AI/ML & Market Data
  CORE:
    process.env.ENGINE_CORE_URL || "https://engine-b-mfvaq54jjq-uc.a.run.app",
  // Engine C: Trade Execution
  EXECUTION:
    process.env.ENGINE_EXECUTION_URL ||
    "https://engine-c-mfvaq54jjq-uc.a.run.app",
};
