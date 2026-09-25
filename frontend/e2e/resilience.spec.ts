import { expect, test, type Page } from '@playwright/test'

import {
  checkIn,
  currentScreen,
  openTheLastTrain,
  playToEnding,
  pressAndWait,
  pressContinue,
  tabTo,
  type Answer,
} from './helpers'

// Resilience and Maya, with the returning student Leo (desktop project only). Serial: each test
// starts from where the previous one left Leo's run.
test.describe.configure({ mode: 'serial' })

// Misses on q01–q04 spend the slack; the miss on q07 would lose the train, so Maya rescues
// (found with the engine: app.engine enumerates all 1,024 paths; this is a cheapest rescue path).
// 5 of 10 → 50% → base A2; A2 needs 2 of 3 (had 1), A1 needs 1 of 2 (had 0) → Pre-A1.
const RESCUE_RUN: Answer[] = [
  { key: '2' }, // q01 miss
  { key: '1' }, // q02 miss
  { key: '1' }, // q03 miss
  { key: '2' }, // q04 miss
  { text: "didn't see" }, // q05
  { text: 'have been looking' }, // q06
  { key: '2' }, // q07 miss → Maya's rescue
  { key: '1' }, // q08
  { key: '1' }, // q09
  { key: '2' }, // q10
]

test("Maya's rescue: a shortcut, the ending Made It Together, and the report records it", async ({
  page,
}) => {
  await checkIn(page, 'veteran@globalai.test')
  await expect(page.getByText('Welcome, Leo.')).toBeVisible()
  await openTheLastTrain(page)
  const log = await playToEnding(page, RESCUE_RUN)
  expect(log.rescue).toBe(true)
  await expect(page.getByRole('heading', { level: 1, name: 'Made It Together' })).toBeVisible()
  await tabTo(page, page.getByRole('button', { name: 'Submit mission' }))
  await page.keyboard.press('Enter')
  await expect(
    page.getByRole('heading', { level: 1, name: 'Pre-A1 · The Last Train — 50%' }),
  ).toBeVisible()
  const record = page.locator('dt', { hasText: /^Maya's shortcut$/ })
  await expect(record.locator('xpath=following-sibling::dd[1]')).toHaveText('Used')
})

/** The attempt id in the player URL. */
function attemptOf(page: Page): string {
  const id = new URL(page.url()).searchParams.get('attempt')
  if (!id) throw new Error(`no attempt in ${page.url()}`)
  return id
}

test('two tabs, a reload and no speech: the server state wins, nothing breaks', async ({
  browser,
}) => {
  // No speechSynthesis at all (as on some browsers/devices): the listening checkpoint must stay
  // usable with the written announcement (PD-014).
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } })
  await context.addInitScript(() => {
    // @ts-expect-error -- removing the API on purpose
    delete window.speechSynthesis
  })
  const a = await context.newPage()
  await checkIn(a, 'veteran@globalai.test')
  await openTheLastTrain(a) // Play again: a new run at the intro
  expect(await currentScreen(a)).toBe('continue')

  // Tab B opens the same run.
  const b = await context.newPage()
  await b.goto(a.url())
  expect(await currentScreen(b)).toBe('continue')

  // A continues to the first checkpoint; B's stale Continue gets a 409 and silently resyncs.
  expect(await pressContinue(a)).toBe(200)
  expect(await currentScreen(a)).toBe('choice')
  expect(await pressContinue(b)).toBe(409)
  expect(await currentScreen(b)).toBe('choice')
  await expect(b.getByText('The signal dropped')).toHaveCount(0)

  // A answers; B answers the same checkpoint → 409 CHECKPOINT_LOCKED, B shows A's outcome scene.
  await a.keyboard.press('1')
  expect(await pressAndWait(a, () => a.keyboard.press('Enter'))).toBe(200)
  expect(await currentScreen(a)).toBe('continue')
  await b.keyboard.press('2')
  const locked = b.waitForResponse((r) => r.url().endsWith('/answer'))
  await b.keyboard.press('Enter')
  const lockedResponse = await locked
  expect(lockedResponse.status()).toBe(409)
  expect((await lockedResponse.json()).error.code).toBe('CHECKPOINT_LOCKED')
  expect(await currentScreen(b)).toBe('continue')
  await expect(b.getByText('The signal dropped')).toHaveCount(0)
  const server = await (await a.request.get(`/api/attempts/${attemptOf(a)}`)).json()
  await expect(b.locator('h1')).toHaveText(`The Last Train — ${server.node.scene.location}`)

  // A reload resumes exactly: same node, same clock.
  await a.reload()
  expect(await currentScreen(a)).toBe('continue')
  await expect(a.locator('h1')).toHaveText(`The Last Train — ${server.node.scene.location}`)
  await expect(a.getByLabel(server.clock.label)).toBeVisible()

  // On to the listening checkpoint (q02) without speech: the transcript replaces Listen.
  expect(await pressContinue(a)).toBe(200)
  expect(await currentScreen(a)).toBe('choice')
  await expect(a.getByText("Audio isn't available on this device")).toBeVisible()
  await expect(a.getByRole('button', { name: /^Listen/ })).toHaveCount(0)
  await a.keyboard.press('2')
  expect(await pressAndWait(a, () => a.keyboard.press('Enter'))).toBe(200)
  expect(await currentScreen(a)).toBe('continue')
  await context.close()
})

test.describe('reduced motion', () => {
  test.use({ contextOptions: { reducedMotion: 'reduce' } })

  test('the motion tokens drop to the reduced values and the run still works', async ({ page }) => {
    await checkIn(page, 'veteran@globalai.test')
    // tokens.css (UI_SPEC §3.5): quick 180 → 0 ms, scene 400 → 120 ms, consequence 500 → 120 ms.
    const tokens = await page.evaluate(() => {
      const css = getComputedStyle(document.documentElement)
      const ms = (v: string) => (v.endsWith('ms') ? parseFloat(v) : parseFloat(v) * 1000)
      return ['--motion-quick', '--motion-scene', '--motion-consequence'].map((t) =>
        ms(css.getPropertyValue(t).trim()),
      )
    })
    expect(tokens).toEqual([0, 120, 120])
    await openTheLastTrain(page) // Continue your mission (left open by the previous test)
    expect(await currentScreen(page)).toBe('continue')
    // No typewriter under reduced motion: the very first Enter advances.
    expect(await pressAndWait(page, () => page.keyboard.press('Enter'))).toBe(200)
    expect(await currentScreen(page)).toBe('choice')
  })
})
