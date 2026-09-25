// Mock-mode fixtures (dev only, never in the production bundle). A tiny placeholder story that
// exercises every renderer. It carries NO answer keys: the mock moves forward whatever the answer.
import type { NodeView, ProgressResponse, Report, WorldResponse } from '../types'

export const MOCK_MISSION = { id: 'the-last-train', title: 'The Last Train (mock)' }

type MockNode = { node: NodeView; next: string | null; minutes: number; mayaLine: string | null }

const scene = (location: string, backdrop: string, lines: [string, string][]) => ({
  location,
  backdrop,
  lines: lines.map(([speaker, text]) => ({ speaker, text })),
})

export const MOCK_NODES: Record<string, MockNode> = {
  intro: {
    node: {
      id: 'intro',
      kind: 'narrative',
      scene: scene('Station concourse', 'concourse_night', [
        ['narrator', 'Mock scene. The departures hall hums.'],
      ]),
      checkpoint: null,
      ending: null,
    },
    next: 'm1',
    minutes: 0,
    mayaLine: 'Mock mode: nothing here is real content.',
  },
  m1: {
    node: {
      id: 'm1',
      kind: 'checkpoint',
      scene: scene('Platform', 'platform', [['narrator', 'A mock announcement plays.']]),
      checkpoint: {
        item_id: 'mock1',
        type: 'multiple_choice',
        prompt: 'Mock listening prompt?',
        stimulus: {
          kind: 'audio',
          speaker: 'Mock announcer',
          audio_script: 'This is a mock announcement.',
          rate: 0.9,
          text: null,
        },
        options: [
          { id: 'a', text: 'Option one' },
          { id: 'b', text: 'Option two' },
          { id: 'c', text: 'Option three' },
        ],
      },
      ending: null,
    },
    next: 'm1_after',
    minutes: 2,
    mayaLine: 'Listen when you are ready.',
  },
  m1_after: {
    node: {
      id: 'm1_after',
      kind: 'consequence',
      scene: scene('Platform', 'platform', [['narrator', 'The story moves on.']]),
      checkpoint: null,
      ending: null,
    },
    next: 'm2',
    minutes: 0,
    mayaLine: null,
  },
  m2: {
    node: {
      id: 'm2',
      kind: 'checkpoint',
      scene: scene('Ticket hall', 'ticket_hall', [['narrator', 'A mock clerk waits.']]),
      checkpoint: {
        item_id: 'mock2',
        type: 'fill_blank',
        prompt: 'Could I ___ a mock ticket, please?',
        stimulus: { kind: 'dialogue', speaker: 'Clerk', text: 'What can I do for you?' },
        options: null,
      },
      ending: null,
    },
    next: 'm2_after',
    minutes: 2,
    mayaLine: null,
  },
  m2_after: {
    node: {
      id: 'm2_after',
      kind: 'consequence',
      scene: scene('Ticket hall', 'ticket_hall', [['narrator', 'Tickets in hand, more or less.']]),
      checkpoint: null,
      ending: null,
    },
    next: 'm3',
    minutes: 0,
    mayaLine: null,
  },
  m3: {
    node: {
      id: 'm3',
      kind: 'checkpoint',
      scene: scene('Concourse', 'concourse_night', [['narrator', 'A mock notice on the wall.']]),
      checkpoint: {
        item_id: 'mock3',
        type: 'comprehension',
        prompt: 'What does the mock notice say?',
        stimulus: {
          kind: 'notice',
          speaker: 'Station notice',
          text: 'MOCK NOTICE\nNothing to see here.',
        },
        options: [
          { id: 'a', text: 'Something' },
          { id: 'b', text: 'Nothing' },
        ],
      },
      ending: null,
    },
    next: 'end',
    minutes: 2,
    mayaLine: null,
  },
  end: {
    node: {
      id: 'end',
      kind: 'ending',
      scene: scene('On the train', 'train_carriage', [['narrator', 'The mock train pulls away.']]),
      checkpoint: null,
      ending: { key: 'made_it', title: 'Made It' },
    },
    next: null,
    minutes: 0,
    mayaLine: 'Mock ending. Submit to see a mock report.',
  },
}

const skills = [
  { skill: 'grammar' as const, correct: 3, total: 4, pct: 75 },
  { skill: 'listening' as const, correct: 1, total: 2, pct: 50 },
  { skill: 'reading' as const, correct: 2, total: 2, pct: 100 },
  { skill: 'vocabulary' as const, correct: 1, total: 2, pct: 50 },
]

export function mockReport(attemptId: string): Report {
  return {
    attempt_id: attemptId,
    mission_id: MOCK_MISSION.id,
    mission_title: MOCK_MISSION.title,
    label: 'A2 · Mock Mission — 70%',
    result: {
      score_pct: 70,
      correct: 7,
      incorrect: 3,
      total: 10,
      skills,
      unmeasured_skills: ['speaking'],
      suggested_level: {
        cefr: 'A2',
        base_cefr: 'B1',
        reason: 'Mock reason sentence from the server.',
        evidence: [],
      },
    },
    attempt_record: {
      attempt_number: 1,
      started_at: '2026-09-24T21:41:10Z',
      submitted_at: '2026-09-24T21:58:03Z',
      ending: { key: 'made_it', title: 'Made It' },
      story_minutes_used: 6,
      rescue_used: false,
      hints_received: 1,
    },
    interpretation: {
      summary: 'Mock summary.',
      strength: 'reading',
      challenge: 'listening',
      recommendation: 'Mock recommendation.',
    },
    feedback_source: { status: 'fallback', provider_label: 'Mock' },
    next_mission: {
      mission_id: 'night-radio',
      title: 'Mock Next Mission',
      skill_focus: ['listening'],
      reason: 'Mock reason.',
      state: 'in_preparation',
      unlock_hint: 'Mock hint.',
    },
    diary: [
      {
        seq: 1,
        clock: '21:47',
        node_id: 'intro',
        kind: 'narrative',
        location: 'Station concourse',
        text: 'Mock diary line.',
        checkpoint: null,
        maya_decision: 'quiet',
      },
      {
        seq: 2,
        clock: '21:47',
        node_id: 'm1',
        kind: 'checkpoint',
        location: 'Platform',
        text: 'Mock checkpoint line.',
        checkpoint: {
          item_id: 'mock1',
          type: 'multiple_choice',
          skill: 'listening',
          cefr: 'A1',
          outcome: 'missed',
        },
        maya_decision: 'hint',
      },
    ],
    missed: [],
  }
}

export function mockWorld(
  openAttemptId: string | null,
  submittedAttemptId: string | null,
): WorldResponse {
  return {
    student: { display_name: 'Mock' },
    greeting: { text: 'Mock greeting from Maya.', source: 'first_meeting', mood: 'curious' },
    cards: [
      {
        mission_id: MOCK_MISSION.id,
        title: MOCK_MISSION.title,
        world_zone: 'the-station',
        teaser: 'Mock teaser.',
        sort_order: 1,
        skill_focus: ['grammar', 'listening', 'reading', 'vocabulary'],
        cefr_range: { min: 'A1', max: 'B2' },
        playable: true,
        state: openAttemptId ? 'in_progress' : submittedAttemptId ? 'completed' : 'available',
        is_maya_pick: false,
        unlock_hint: 'Always open.',
        open_attempt: openAttemptId
          ? {
              attempt_id: openAttemptId,
              status: 'in_progress',
              clock: {
                time: '21:49',
                minutes_left: 16,
                train_departed: false,
                label: '21:49 · 16 min to departure',
              },
              location: 'Platform',
              ending: null,
            }
          : null,
        latest_result: submittedAttemptId
          ? {
              attempt_id: submittedAttemptId,
              label: 'A2 · Mock Mission — 70%',
              submitted_at: '2026-09-24T21:58:03Z',
            }
          : null,
        attempts_submitted: submittedAttemptId ? 1 : 0,
      },
      {
        mission_id: 'night-radio',
        title: 'Mock Locked Mission',
        world_zone: 'the-radio-tower',
        teaser: 'Mock teaser.',
        sort_order: 2,
        skill_focus: ['listening'],
        cefr_range: { min: 'A2', max: 'B2' },
        playable: false,
        state: 'locked',
        is_maya_pick: false,
        unlock_hint: 'Mock unlock hint.',
        open_attempt: null,
        latest_result: null,
        attempts_submitted: 0,
      },
    ],
    snapshot: { missions_played: 0, latest_label: null, profile: null },
  }
}

export const MOCK_EMPTY_PROGRESS: ProgressResponse = {
  profile: null,
  history: [],
  level_history: [],
  notes: [],
  open_attempt: null,
}
