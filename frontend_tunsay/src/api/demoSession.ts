/**
 * Demo-session persistence — DELETE THIS FILE when demo mode goes away.
 *
 * WHY IT EXISTS. dal/models/user.py puts the unique constraint on
 * (school_code, student_name), and demo accounts have no school code. SQL
 * treats NULLs as distinct in a unique constraint, so POST /auth/register
 * succeeds every single time for the same demo name — 201, never 409 — and
 * each grade pick silently creates ANOTHER user row with a new `sub`.
 *
 * Today that is invisible (App.tsx still holds stars in useState), but it
 * would reset a child's progress on every refresh the moment ProfileView
 * starts reading from student_profile_service (P2.3). Reusing the token we
 * already hold keeps one demo account per grade for the life of the JWT
 * (JWT_EXPIRE_MINUTES=60), which is far longer than any demo.
 *
 * Deliberately separate from api/client.ts so demo scaffolding never tangles
 * with the real auth surface.
 */

const DEMO_GRADE_KEY = 'tunsay_demo_grade';

/** The grade whose demo account the stored token belongs to, if any. */
export function getDemoGrade(): number | null {
  try {
    const raw = localStorage.getItem(DEMO_GRADE_KEY);
    if (!raw) return null;
    const grade = Number.parseInt(raw, 10);
    return Number.isInteger(grade) ? grade : null;
  } catch {
    return null; // private mode — the demo just re-registers each time
  }
}

export function setDemoGrade(grade: number): void {
  try {
    localStorage.setItem(DEMO_GRADE_KEY, String(grade));
  } catch {
    /* storage unavailable; harmless, see above */
  }
}

export function clearDemoGrade(): void {
  try {
    localStorage.removeItem(DEMO_GRADE_KEY);
  } catch {
    /* noop */
  }
}
