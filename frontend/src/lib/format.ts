// Display helpers. Only presentation: the client never computes scores, levels or correctness.
import type { Cefr, ItemType, Skill } from '../api/types'

export const SCORED_SKILLS: Skill[] = ['grammar', 'listening', 'reading', 'vocabulary']

const SKILL_NAMES: Record<Skill, string> = {
  grammar: 'Grammar',
  listening: 'Listening',
  reading: 'Reading',
  vocabulary: 'Vocabulary',
  speaking: 'Speaking',
}

const SKILL_ABBR: Record<Skill, string> = {
  grammar: 'Gr',
  listening: 'Li',
  reading: 'Re',
  vocabulary: 'Vo',
  speaking: 'Sp',
}

const TYPE_NAMES: Record<ItemType, string> = {
  multiple_choice: 'Multiple choice',
  fill_blank: 'Fill in the blank',
  comprehension: 'Comprehension',
  vocabulary: 'Vocabulary',
}

export const skillName = (skill: Skill) => SKILL_NAMES[skill]
export const skillAbbr = (skill: Skill) => SKILL_ABBR[skill]
export const typeName = (type: ItemType) => TYPE_NAMES[type]
export const cefrLabel = (cefr: Cefr) => (cefr === 'PRE_A1' ? 'Pre-A1' : cefr)

/** "Multiple choice · Grammar · A2" (report only, PD-029). */
export const checkpointTag = (type: ItemType, skill: Skill, cefr: Cefr) =>
  `${typeName(type)} · ${skillName(skill)} · ${cefrLabel(cefr)}`

/** "the-station" → "The Station" (PD-032). */
export const zoneName = (slug: string) =>
  slug
    .split('-')
    .filter(Boolean)
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(' ')

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const pad = (n: number) => String(n).padStart(2, '0')

/** Local "24 Sep 2026 · 21:58". */
export function dateTime(iso: string): string {
  const d = new Date(iso)
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()} · ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** Local "24 Sep". */
export function shortDate(iso: string): string {
  const d = new Date(iso)
  return `${d.getDate()} ${MONTHS[d.getMonth()]}`
}

export const plural = (n: number, one: string, many: string) => (n === 1 ? one : many)

/** Split the server's clock label on the first " · " for layout only (F-06: never rebuilt). */
export function splitClockLabel(label: string): [string, string | null] {
  const at = label.indexOf(' · ')
  return at === -1 ? [label, null] : [label.slice(0, at), label.slice(at + 3)]
}
