// Friendly aliases over the generated OpenAPI types (npm run gen:api). Never edit schema.d.ts.
import type { components } from './schema'

type Schemas = components['schemas']

export type UserView = Schemas['UserView']
export type ConfigResponse = Schemas['ConfigResponse']
export type DemoAccount = Schemas['DemoAccount']
export type LoginRequest = Schemas['LoginRequest']

export type WorldResponse = Schemas['WorldResponse']
export type MissionCard = Schemas['MissionCard']
export type Greeting = Schemas['Greeting']
export type Snapshot = Schemas['Snapshot']
export type Profile = Schemas['Profile']

export type StateView = Schemas['StateView']
export type NodeView = Schemas['NodeView']
export type SceneLine = Schemas['SceneLine']
export type CheckpointView = Schemas['CheckpointView']
export type OptionView = Schemas['OptionView']
export type AudioStimulus = Schemas['AudioStimulus']
export type TextStimulus = Schemas['TextStimulus']
export type Stimulus = AudioStimulus | TextStimulus
export type MayaView = Schemas['MayaView']
export type Clock = Schemas['Clock']
export type AdvanceRequest = Schemas['AdvanceRequest']
export type AnswerRequest = Schemas['AnswerRequest']
export type AnswerResponse = Schemas['AnswerResponse']

export type Report = Schemas['Report']
export type SkillScore = Schemas['SkillScore']
export type DiaryEntry = Schemas['DiaryEntryView']
export type MissedCheckpoint = Schemas['MissedCheckpoint']
export type NextMission = Schemas['NextMission']

export type ProgressResponse = Schemas['ProgressResponse']
export type HistoryRow = Schemas['HistoryRow']

export type ClassesResponse = Schemas['ClassesResponse']
export type ClassSummary = Schemas['ClassSummary']

export type SimulationResponse = Schemas['SimulationResponse']
export type SimulationStep = Schemas['SimulationStep']
export type SimulationProfile = SimulationResponse['profile']
export type ClassProgressResponse = Schemas['ClassProgressResponse']

export type Mood = MayaView['mood']
export type Skill = SkillScore['skill']
export type Cefr = Schemas['SuggestedLevel']['cefr']
export type ItemType = CheckpointView['type']
export type CardState = MissionCard['state']
