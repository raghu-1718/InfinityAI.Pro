import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [['list'], ['json', { outputFile: './output/playwright-results.json' }]],
  use: {
    headless: true,
    viewport: { width: 1280, height: 800 },
    actionTimeout: 15_000,
    ignoreHTTPSErrors: true,
    // Trace / screenshot toggles are controlled by env var E2E_TRACE=1 to enable full tracing and screenshots
    trace: process.env.E2E_TRACE === '1' ? 'on' : 'on-first-retry',
    screenshot: process.env.E2E_TRACE === '1' ? 'on' : 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  testDir: '.',
});
