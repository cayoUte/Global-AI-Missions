/** Speaker label and tone for scene lines and dialogue stimuli (UI_SPEC §5 DialogueBox). */
export function speakerLabel(speaker: string): { label: string | null; tone: string } {
  const key = speaker.trim().toLowerCase()
  if (key === 'narrator') return { label: null, tone: '' }
  if (key === 'maya') return { label: 'Maya', tone: 'text-maya-300' }
  if (key === 'you') return { label: 'You', tone: 'text-amber-400' }
  return { label: speaker, tone: 'text-fog-200' }
}
