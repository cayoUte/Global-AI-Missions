import { expect, test } from '@playwright/test'

import {
  checkIn,
  DEMO_PASSWORD,
  expectNoHorizontalScroll,
  openTheLastTrain,
  playToEnding,
  tabTo,
  type Answer,
} from './helpers'

// The brief's whole flow for the new student, keyboard only, with a fixed answer sequence.
// Runs in two projects: desktop (1280×800) and mobile-360 (360×740).
//
// Checkpoints arrive in the same order on every path (q01…q10). Two deliberate misses:
// q02 (listening, A1) and q05 (fill-blank grammar, A2). Expected, by ASSESSMENT_SPEC:
// 8 correct / 2 incorrect → 80% → base B1; B1 needs 2 of 3 B1 checkpoints (q06–q08, all right)
// → suggested B1. Grammar 3 of 4 (75%), Listening 1 of 2 (50%), Reading 100%, Vocabulary 100%.
const ANSWERS: Answer[] = [
  { key: '1' }, // q01 "Is"
  { key: '1' }, // q02 "Platform 5" — deliberate miss (the announcer says 7)
  { key: '2' }, // q03 the machines next to the main entrance
  { key: '1' }, // q04 a single
  { text: "don't see" }, // q05 — deliberate miss (past simple: "didn't see")
  { text: 'have been looking' }, // q06
  { key: '1' }, // q07 show tickets at the side gate
  { key: '1' }, // q08 wait for a moment
  { key: '1' }, // q09 had left
  { key: '2' }, // q10 the café on George Street
]
const LABEL = 'B1 · The Last Train — 80%'

test('new student: check-in → full mission by keyboard → report → progress', async ({
  page,
}, testInfo) => {
  const mobile = testInfo.project.name === 'mobile-360'

  // Check-in and the English World.
  await checkIn(page, 'new@globalai.test')
  await expect(page.getByText('Welcome, Ana.')).toBeVisible()
  await expect(page.getByRole('article').filter({ hasText: 'Night Radio' })).toBeVisible()
  if (mobile) await expectNoHorizontalScroll(page)

  // The mission: 10 checkpoints, never a question counter or a verdict on screen.
  await openTheLastTrain(page)
  const log = await playToEnding(page, ANSWERS)
  expect(log.checkpoints).toBe(10)
  for (const text of log.missionTexts) {
    expect(text).not.toMatch(/\bQuestion \d+ of 10\b|\bincorrect\b|\bcorrect\b|\d+%/i)
  }
  if (mobile) await expectNoHorizontalScroll(page)

  // The Ending shows no numbers; Submit mission with the keyboard.
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('body')).not.toContainText('%')
  await tabTo(page, page.getByRole('button', { name: 'Submit mission' }))
  await page.keyboard.press('Enter')

  // The Mission Report: the brief's result block, first and without clicks.
  await expect(page).toHaveURL(/\/attempts\/[0-9a-f-]{36}\/report$/)
  await expect(page.getByRole('heading', { level: 1, name: LABEL })).toBeVisible()
  const tile = (name: string) =>
    page
      .locator('dt', { hasText: new RegExp(`^${name}$`) })
      .locator('xpath=following-sibling::dd[1]')
  await expect(tile('Global score')).toHaveText('80%')
  await expect(tile('Correct')).toHaveText('8')
  await expect(tile('Incorrect')).toHaveText('2')
  await expect(page.getByRole('heading', { name: 'Result per skill' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Suggested level' })).toBeVisible()
  await expect(page.getByText(/^80% points to B1\./)).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Attempt record' })).toBeVisible()
  await expect(page.getByText("Speaking isn't measured in this mission yet.")).toBeVisible()
  await expect(
    page.getByText('About this feedback: Written by Maya from her notebook (offline feedback).'),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Maya has prepared your next mission' }),
  ).toBeVisible()
  // Two missed checkpoints, with the correct answer only now that the attempt is closed.
  await expect(page.getByRole('heading', { name: 'Checkpoints to revisit' })).toBeVisible()
  await expect(page.getByText("didn't see", { exact: true })).toBeVisible()
  if (mobile) await expectNoHorizontalScroll(page)
  const attemptNumber = await tile('Attempt').innerText()

  // Progress: the profile and the new attempt on top of the history.
  await tabTo(page, page.getByRole('link', { name: 'See your progress' }).last())
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/progress$/)
  await expect(page.getByRole('heading', { name: 'Your English today' })).toBeVisible()
  await expect(page.getByText(/^Based on your last \d missions?\.$/)).toBeVisible()
  const newest = page.getByRole('row').nth(1)
  await expect(newest.getByRole('link', { name: `Attempt ${attemptNumber}` })).toBeVisible()
  await expect(newest).toContainText(mobile ? '80%' : LABEL)
  await expect(page.getByRole('heading', { name: "Maya's notes" })).toBeVisible()
  // The Progress width at 360 and 768 px is checked by the next test (BUG-001 regression).
})

test('Progress has no horizontal page scroll at 360 and 768 px', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-360', 'a small-screen check')
  // Regression check for BUG-001 (docs/qa/CHECKLIST.md): the Attempt history table scrolls inside
  // its card instead of widening the page.
  const login = await page.request.post('/api/auth/login', {
    data: { email: 'veteran@globalai.test', password: DEMO_PASSWORD },
  })
  expect(login.status()).toBe(200)
  for (const width of [360, 768]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/progress')
    await expect(page.getByRole('heading', { name: 'Attempt history' })).toBeVisible()
    await expectNoHorizontalScroll(page)
  }
})

test('teacher: the seeded class with both students, read-only', async ({ page }, testInfo) => {
  // PRODUCT §5.7: Ms. Clarke teaches Evening B1 (seed), with Ana and Leo.
  await checkIn(page, 'teacher@globalai.test', 'teacher')
  await expect(page.getByRole('heading', { level: 1, name: 'Hello, Ms. Clarke.' })).toBeVisible()
  await expect(page.getByRole('heading', { level: 2, name: 'Evening B1' })).toBeVisible()
  const table = page.getByRole('table', { name: 'Students in Evening B1' })
  await expect(table.getByRole('rowheader', { name: 'Ana' })).toBeVisible()
  await expect(table.getByRole('rowheader', { name: 'Leo' })).toBeVisible()
  await expect(table.getByRole('link')).toHaveCount(0) // no drill-in (PD-030)
  if (testInfo.project.name === 'mobile-360') await expectNoHorizontalScroll(page)
})

test('simulated replay (demo mode): profile A2, seed 7 → 10 checkpoints and an ending', async ({
  page,
}, testInfo) => {
  // PRODUCT §5.8: a simulated student, never answer content. Keyboard only.
  await checkIn(page, 'new@globalai.test')
  await tabTo(page, page.getByRole('link', { name: 'Watch a simulated run' }))
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/replay\?mission=the-last-train$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Simulated run' })).toBeVisible()
  await expect(page.getByRole('radio', { name: 'A2', exact: true })).toBeChecked()
  await tabTo(page, page.getByLabel('Seed'))
  await page.keyboard.press('ControlOrMeta+a')
  await page.keyboard.type('7')
  const simulated = page.waitForResponse((r) => r.url().includes('/simulate?profile=A2&seed=7'))
  await tabTo(page, page.getByRole('button', { name: 'Run simulation' }))
  await page.keyboard.press('Enter')
  expect((await simulated).status()).toBe(200)
  await expect(page.getByRole('heading', { level: 2, name: /^Ending reached: / })).toBeVisible()
  await tabTo(page, page.getByRole('button', { name: 'Show all' }))
  await page.keyboard.press('Enter')
  const path = page.getByRole('list', { name: 'Simulated path' })
  await expect(path.getByText(/^(Understood|Missed)$/)).toHaveCount(10)
  await expect(path.getByRole('listitem').last()).toContainText('Ending')
  if (testInfo.project.name === 'mobile-360') await expectNoHorizontalScroll(page)
})
