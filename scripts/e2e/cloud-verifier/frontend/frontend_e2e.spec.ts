import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const OUT_DIR = path.join(__dirname, '../output/frontend');
const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-');
const REPORT_FILE = path.join(OUT_DIR, `frontend_e2e_report_${TIMESTAMP}.json`);
const SUMMARY_FILE = path.join(OUT_DIR, `summary_${TIMESTAMP}.md`);

function ensureOutDir() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

function writeReport(report: any) {
  ensureOutDir();
  fs.writeFileSync(REPORT_FILE, JSON.stringify(report, null, 2));
  const summary = `# Frontend E2E Report - ${new Date().toISOString()}\n\n` +
    `Environment: BASE_URL=${process.env.BASE_URL}\n\n` +
    `Steps:\n` +
    report.steps.map((s: any) => `- ${s.name}: ${s.status}${s.reason ? ' - ' + s.reason : ''}`).join('\n');
  fs.writeFileSync(SUMMARY_FILE, summary);
}

// Helper to capture network events
const networkEvents = [] as any[];

// Selectors heuristics for login and dashboard
const selectors = {
  email: 'input[type="email"]',
  password: 'input[type="password"]',
  submit: 'button:has-text("Sign in"), button:has-text("Sign In"), button:has-text("Login"), button:has-text("Log in"), button[type="submit"]',
  dashboardMarker: 'text=AI Auto Trading, text=Dashboard, [data-testid="dashboard"], #dashboard, text=Start Auto Trading'
};

test('frontend E2E (safe, read-only)', async ({ page }) => {
  const steps: any[] = [];
  const baseUrl = process.env.BASE_URL;
  if (!baseUrl) {
    throw new Error('Missing required env: BASE_URL');
  }

  // Capture console errors
  const consoleErrors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  // Capture requests and responses
  page.on('requestfinished', async (request) => {
    try {
      const response = request.response();
      networkEvents.push({ url: request.url(), method: request.method(), status: response ? response.status() : null });
    } catch (e) {
      networkEvents.push({ url: request.url(), method: request.method(), status: 'ERROR' });
    }
  });

  // Step 1 - Load Homepage
  let step = { name: 'Load Homepage', status: 'FAIL', reason: '' };
  try {
    const resp = await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
    const status = resp ? resp.status() : null;
    if (status !== 200 && status !== 304) {
      step.reason = `Unexpected status ${status}`;
      throw new Error(step.reason);
    }
    // small wait to capture console errors
    await page.waitForTimeout(1000);
    if (consoleErrors.length > 0) {
      step.reason = `Console errors on load: ${consoleErrors.slice(0,3).join(' | ')}`;
      throw new Error(step.reason);
    }
    step.status = 'PASS';
  } catch (err: any) {
    step.status = 'FAIL';
    step.reason = err.message || String(err);
    // take screenshot
    const p = path.join(OUT_DIR, `homepage_fail_${TIMESTAMP}.png`);
    await page.screenshot({ path: p, fullPage: true });
  }
  steps.push(step);

  // Step 2 - Firebase Login
  step = { name: 'Firebase Login', status: 'FAIL', reason: '' };
  try {
    const email = process.env.FIREBASE_TEST_EMAIL;
    const password = process.env.FIREBASE_TEST_PASSWORD;
    if (!email || !password) throw new Error('Missing FIREBASE_TEST_EMAIL or FIREBASE_TEST_PASSWORD env vars');

    // Try to find login form fields (best-effort)
    const emailEl = await page.locator(selectors.email).first();
    await emailEl.fill(email);
    const passEl = await page.locator(selectors.password).first();
    await passEl.fill(password);
    const submit = page.locator(selectors.submit).first();
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30_000 }),
      submit.click()
    ]);

    // After auth, assert dashboard visible
    const dashboardVisible = await page.locator(selectors.dashboardMarker).first().isVisible().catch(() => false);
    if (!dashboardVisible) throw new Error('Dashboard not visible after login');
    step.status = 'PASS';
  } catch (err: any) {
    step.status = 'FAIL';
    step.reason = err.message || String(err);
    const p = path.join(OUT_DIR, `login_fail_${TIMESTAMP}.png`);
    await page.screenshot({ path: p, fullPage: true });
  }
  steps.push(step);

  // Step 3 - Dashboard Load & Network capture
  step = { name: 'Dashboard Load', status: 'FAIL', reason: '' };
  try {
    // try to ensure dashboard route is stable
    await page.waitForSelector(selectors.dashboardMarker, { timeout: 15_000 });
    // wait briefly for background requests
    await page.waitForTimeout(2000);
    if (consoleErrors.length > 0) throw new Error(`Console errors present: ${consoleErrors.slice(0,3).join(' | ')}`);

    step.status = 'PASS';
  } catch (err: any) {
    step.status = 'FAIL';
    step.reason = err.message || String(err);
    const p = path.join(OUT_DIR, `dashboard_fail_${TIMESTAMP}.png`);
    await page.screenshot({ path: p, fullPage: true });
  }
  steps.push(step);

  // Step 4 - Backend API Observation
  step = { name: 'Backend API Observation', status: 'FAIL', reason: '', details: [] };
  try {
    // examine collected network events for API endpoints and failures
    const apiCalls = networkEvents.filter(e => /api|function|cloudfunctions|run.app|/i.test(e.url));
    // ensure no 5xx statuses
    const serverErrors = apiCalls.filter(e => typeof e.status === 'number' && e.status >= 500);
    if (serverErrors.length > 0) {
      step.reason = `Found 5xx responses: ${serverErrors.map(s => `${s.url}(${s.status})`).slice(0,5).join(', ')}`;
      throw new Error(step.reason);
    }
    step.details = apiCalls.slice(0, 50);
    step.status = 'PASS';
  } catch (err: any) {
    step.status = 'FAIL';
    step.reason = err.message || String(err);
  }
  steps.push(step);

  // Step 5 - Engine Reachability (Indirect)
  step = { name: 'Engine Reachability (indirect)', status: 'FAIL', reason: '' };
  try {
    const hostsSeen = new Set<string>();
    for (const e of networkEvents) {
      try {
        const u = new URL(e.url);
        hostsSeen.add(u.hostname);
      } catch (e) { /* ignore */ }
    }

    const engineA = Array.from(hostsSeen).some(h => h.includes('engine-a') || h.includes('engine-a-'));
    const engineB = Array.from(hostsSeen).some(h => h.includes('engine-b') || h.includes('engine-b-'));

    if (engineA || engineB) {
      step.status = 'PASS';
      step.reason = `Detected hosts: ${Array.from(hostsSeen).filter(h=>h.includes('engine-a')||h.includes('engine-b')).join(', ')}`;
    } else {
      // Try to detect engine references in responses bodies? (best-effort) — not implemented to avoid reading large bodies
      step.status = 'FAIL';
      step.reason = 'Could not detect engine hostnames in frontend network requests. Confirm backend logs to verify engine reachability.';
    }
  } catch (err: any) {
    step.status = 'FAIL';
    step.reason = err.message || String(err);
  }
  steps.push(step);

  // Step 6 - UI State Validation
  step = { name: 'UI State Validation', status: 'FAIL', reason: '' };
  try {
    // No infinite loaders: check for [aria-busy=true]
    const busy = await page.locator('[aria-busy="true"]').elementHandle().catch(() => null);
    if (busy) {
      step.status = 'FAIL';
      step.reason = 'Found element with aria-busy=true (possible loader)';
    } else {
      // look for common 'Error' or 'Failed' text on page
      const hasErrors = await page.locator('text=Error, text=Failed, text=Unavailable').count();
      if (hasErrors > 0) {
        step.status = 'FAIL';
        step.reason = 'Detected visible error text on page';
      } else {
        step.status = 'PASS';
      }
    }
  } catch (err: any) {
    step.status = 'FAIL';
    step.reason = err.message || String(err);
  }
  steps.push(step);

  // Final report
  const report = {
    timestamp: new Date().toISOString(),
    environment: { BASE_URL: process.env.BASE_URL || null },
    steps,
    consoleErrors: consoleErrors.slice(0, 50),
    networkEvents: networkEvents.slice(0, 200),
  };

  // Ensure report is always written
  try {
    writeReport(report);
  } catch (e) {
    console.error('Failed to write report', e);
  }

  // Failing conditions: any step failed -> fail test explicitly
  const failed = steps.filter(s => s.status !== 'PASS');
  if (failed.length > 0) {
    throw new Error(`Frontend E2E failed on steps: ${failed.map(f => f.name + ': ' + f.reason).join('; ')}`);
  }
});
