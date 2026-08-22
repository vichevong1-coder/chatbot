/// <reference types="vite/client" />

// Ambient Vite types. Absent until now, which is why nothing in src/ used
// `import.meta.env` — it would not have type-checked. Added for VITE_DEMO_MODE.

interface ImportMetaEnv {
  /**
   * Demo mode: skip landing + login and enter the tutor through a grade
   * picker instead. ON by default so a fresh clone demos immediately; set
   * VITE_DEMO_MODE=false to restore the real sign-in flow.
   *
   * This only changes which screens render. The backend still requires a JWT
   * on every /chat, /problems and /answers call, and demo mode still obtains
   * a real one — see App.tsx.
   */
  readonly VITE_DEMO_MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
