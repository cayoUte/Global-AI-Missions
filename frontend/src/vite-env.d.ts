/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** "true" in `npm run dev:mock` only (see .env.mock). Ignored by production builds. */
  readonly VITE_API_MOCK?: string
}
