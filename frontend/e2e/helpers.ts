import { expect, type Locator, type Page } from '@playwright/test'

export const DEMO_PASSWORD = 'LastTrain2026!'

/** Keyboard only: press Tab until `target` has focus (fails if it is not reachable). */
export async function tabTo(page: Page, target: Locator, maxTabs = 60): Promise<void> {
  await expect(target).toBeVisible()
  for (let i = 0; i < maxTabs; i++) {
    if (await target.evaluate((el) => el === document.activeElement)) return
    await page.keyboard.press('Tab')
  }
  throw new Error(`not reachable with Tab: ${target}`)
}

/** Check-in with the keyboard only (Tab, type, Enter) and land on the English World (students)
 * or the teacher view. */
export async function checkIn(
  page: Page,
  email: string,
  home: 'world' | 'teacher' = 'world',
): Promise<void> {
  await page.goto('/check-in')
  await tabTo(page, page.getByLabel('Email'))
  await page.keyboard.type(email)
  await tabTo(page, page.getByLabel('Password', { exact: true }))
  await page.keyboard.type(DEMO_PASSWORD)
  await page.keyboard.press('Enter')
  if (home === 'teacher') return expect(page).toHaveURL(/\/teacher$/)
  await expect(page).toHaveURL(/\/world$/)
  await expect(page.getByRole('heading', { name: 'Missions' })).toBeVisible()
}

/** From the English World: Start / Play again / Continue The Last Train with the keyboard. */
export async function openTheLastTrain(page: Page): Promise<void> {
  const card = page.getByRole('article').filter({ hasText: 'The Last Train' }).first()
  const action = card.getByRole('button', {
    name: /^(Start mission|Play again|Continue your mission)$/,
  })
  await tabTo(page, action)
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/missions\/the-last-train\/play\?attempt=/)
}

/** The answer for one checkpoint: an option number (1-4) or the words for a gap. */
export type Answer = { key: string } | { text: string }

export type Screen = 'choice' | 'gap' | 'continue' | 'ending'

/**
 * Waits until the player shows something the student can act on *now* and says what it is.
 * Only actionable controls count: a locked choice group (aria-disabled), a read-only gap or a
 * disabled Continue belong to a request still in flight, never to the next screen.
 */
export async function currentScreen(page: Page): Promise<Screen> {
  const ending = page.getByText('The end of the night')
  const choice = page.locator('[role="radiogroup"]:not([aria-disabled="true"])')
  const gap = page.locator('input[aria-label="Your words for the gap"]:not([readonly])')
  const next = page.getByRole('button', { name: 'Continue', exact: true, disabled: false })
  await expect(ending.or(choice).or(gap).or(next).first()).toBeVisible()
  if (await ending.isVisible()) return 'ending'
  if (await choice.isVisible()) return 'choice'
  if (await gap.isVisible()) return 'gap'
  return 'continue'
}

/** Presses `keys` and waits for the advance/answer call they trigger; returns its status. */
export async function pressAndWait(page: Page, keys: () => Promise<void>): Promise<number> {
  const response = page.waitForResponse(
    (r) =>
      /\/api\/attempts\/[^/]+\/(advance|answer)$/.test(r.url()) && r.request().method() === 'POST',
  )
  await keys()
  return (await response).status()
}

/**
 * Continue on a narrative node with the keyboard; returns the advance call's status. The scene
 * typewriter (UI_SPEC §7) makes the first Enter complete the text and the second advance. If the
 * text had already finished, the first Enter advances and the second lands on the busy (disabled)
 * Continue or on the next scene, where it only completes that scene's typewriter (Enter never
 * confirms an empty choice or gap), so the result is the same one advance either way.
 */
export async function pressContinue(page: Page): Promise<number> {
  return pressAndWait(page, async () => {
    await page.keyboard.press('Enter')
    await page.keyboard.press('Enter')
  })
}

export type PlayLog = { checkpoints: number; rescue: boolean; missionTexts: string[] }

/**
 * Plays from the current node to the Ending with the keyboard only: Enter on Continue, a digit +
 * Enter on choice checkpoints, typing + Enter on gaps, L on a listening checkpoint when speech is
 * available. `answers[i]` answers the i-th checkpoint (every path visits the same 10 in order).
 */
export async function playToEnding(page: Page, answers: Answer[]): Promise<PlayLog> {
  const log: PlayLog = { checkpoints: 0, rescue: false, missionTexts: [] }
  for (let step = 0; step < 120; step++) {
    const screen = await currentScreen(page)
    log.missionTexts.push(await page.locator('body').innerText())
    if (await page.getByText("Maya's shortcut", { exact: true }).first().isVisible())
      log.rescue = true
    if (screen === 'ending') return log
    if (screen === 'continue') {
      expect(await pressContinue(page)).toBe(200)
      continue
    }
    const answer = answers[log.checkpoints]
    if (!answer) throw new Error(`no answer for checkpoint ${log.checkpoints + 1}`)
    log.checkpoints += 1
    if (screen === 'choice') {
      if (!('key' in answer)) throw new Error(`checkpoint ${log.checkpoints} is a choice`)
      const listen = page.getByRole('button', { name: /^Listen/ })
      if (await listen.isVisible()) await page.keyboard.press('l') // L = Listen (UI_SPEC §8)
      await page.keyboard.press(answer.key)
      await expect(page.getByRole('radio', { checked: true })).toHaveCount(1)
      expect(await pressAndWait(page, () => page.keyboard.press('Enter'))).toBe(200)
    } else {
      if (!('text' in answer)) throw new Error(`checkpoint ${log.checkpoints} is a gap`)
      await expect(page.getByRole('textbox', { name: 'Your words for the gap' })).toBeFocused()
      await page.keyboard.type(answer.text)
      expect(await pressAndWait(page, () => page.keyboard.press('Enter'))).toBe(200)
    }
  }
  throw new Error('the mission did not reach an ending')
}

/** No horizontal page scroll (PRODUCT §5: every screen usable at 360 px). */
export async function expectNoHorizontalScroll(page: Page): Promise<void> {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(0)
}
