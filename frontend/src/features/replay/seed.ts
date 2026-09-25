const MAX_SEED = 1_000_000

/** "7" → 7; anything that is not a whole number in 0..1,000,000 → null (the API's bounds). */
export function parseSeed(text: string): number | null {
  const trimmed = text.trim()
  if (!/^\d{1,7}$/.test(trimmed)) return null
  const seed = Number(trimmed)
  return seed <= MAX_SEED ? seed : null
}
