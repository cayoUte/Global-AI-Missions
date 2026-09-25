import { defineConfig, devices } from '@playwright/test'

// E2E (qa-engineer): the real stack on one origin — FastAPI serves the built SPA (npm run build)
// over a throwaway database `gam_e2e` that e2e/serve.sh recreates, migrates and seeds on every
// run, so the demo database `gam` (and Ana's first meeting) is never touched.
// Needs PostgreSQL from docker compose on 127.0.0.1:5433 (`make up`). Run: `make e2e`.
const PORT = Number(process.env.E2E_PORT ?? 8765)
const BASE_URL = `http://127.0.0.1:${PORT}` // 127.0.0.1, not localhost (CR-005)

export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1, // one database, shared demo users: run serially
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
    {
      name: 'mobile-360',
      testMatch: /mission\.spec\.ts/,
      use: { ...devices['Desktop Chrome'], viewport: { width: 360, height: 740 } },
    },
  ],
  webServer: {
    command: 'sh e2e/serve.sh',
    url: `${BASE_URL}/api/health`,
    reuseExistingServer: false, // always a freshly seeded database
    timeout: 120_000,
    stdout: 'ignore',
    stderr: 'pipe',
    env: {
      E2E_PORT: String(PORT),
      DATABASE_URL: 'postgresql+psycopg://gam:gam@127.0.0.1:5433/gam_e2e',
      JWT_SECRET: 'e2e-only-secret-not-for-production-0123456789',
      COACH_PROVIDER: 'mock',
      DEMO_MODE: 'true',
      COOKIE_SECURE: 'false',
    },
  },
})
