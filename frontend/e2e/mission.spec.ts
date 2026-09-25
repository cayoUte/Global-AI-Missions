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
  // The Progress width at 360 px is checked by the next test (known bug BUG-001).
})

test('Progress has no horizontal page scroll at 360 px', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-360', 'a 360 px check')
  // BUG-001 (docs/qa/CHECKLIST.md): the Attempt history table is ~25 px wider than 360 px.
  // Expected to fail until the fix lands; Playwright then reports an unexpected pass, and this
  // line must be removed.
  test.fail(true, 'BUG-001: Attempt history table overflows at 360 px')
  const login = await page.request.post('/api/auth/login', {
    data: { email: 'veteran@globalai.test', password: DEMO_PASSWORD },
  })
  expect(login.status()).toBe(200)
  await page.goto('/progress')
  await expect(page.getByRole('heading', { name: 'Attempt history' })).toBeVisible()
  await expectNoHorizontalScroll(page)
})
