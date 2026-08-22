/**
 * The frontend's only network surface. Everything goes through server.ts's
 * /api/* proxy to the gateway — components never call services directly
 * (.claude/architecture.md §1). The wire shape is camelCase; the gateway
 * translates to snake_case for the Python services.
 */

import { Grade, Language, UserProfile } from '../types';
import { khmerToLatinDigits } from '../utils/language';

const TOKEN_KEY = 'tunsay_token';

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable (private mode) — session simply stays anonymous */
  }
}

export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

interface RegisterPayload {
  studentName: string;
  schoolCode?: string;
  className?: string;
  grade?: Grade;
  parentContact?: string;
  pin?: string;
  language?: Language;
}

interface TokenResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  profile: {
    name: string;
    grade: Grade;
    language: Language;
  };
}

export interface StudentProfileData {
  studentId: string;
  stars: number;
  completedProblemsCount: number;
  masteryLevels?: Record<string, number>;
}

export interface HintDeductionResult {
  success: boolean;
  remainingStars: number;
  starsRemaining?: number;
}

async function postJson<T>(path: string, body: unknown): Promise<T | null> {
  try {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(body),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(path, {
      method: 'GET',
      headers: { ...authHeaders() },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/**
 * Register, falling back to login when the account already exists (409 makes
 * the register call return null; login covers the returning child). Returns a
 * partial UserProfile on success, null when the backend is unreachable or
 * credentials fail.
 */
export async function registerOrLogin(
  payload: RegisterPayload,
): Promise<Partial<UserProfile> | null> {
  const normalizedPin = payload.pin ? khmerToLatinDigits(payload.pin.trim()) : undefined;
  const auth =
    (await postJson<TokenResponse>('/api/auth/register', { ...payload, pin: normalizedPin })) ??
    (await postJson<TokenResponse>('/api/auth/login', {
      studentName: payload.studentName,
      schoolCode: payload.schoolCode,
      pin: normalizedPin,
    }));
  if (!auth) return null;

  setToken(auth.accessToken);
  return {
    name: auth.profile.name,
    grade: auth.profile.grade,
    language: auth.profile.language,
  };
}

/**
 * Fetches the student profile from the student profile service via gateway.
 */
export async function fetchStudentProfile(
  studentId?: string,
): Promise<StudentProfileData | null> {
  const path = studentId ? `/api/profile/${encodeURIComponent(studentId)}` : '/api/profile';
  return getJson<StudentProfileData>(path);
}

/**
 * Deducts stars when a student requests a hint rung.
 */
export async function deductStars(
  hintLevel: number,
  problemId: string = 'general',
  stepId: string = 'step-1',
): Promise<HintDeductionResult | null> {
  const res = await postJson<{ success: boolean; remainingStars: number }>(
    '/api/profile/hints',
    {
      rung: hintLevel,
      problemId,
      stepId,
    },
  );
  if (!res) return null;
  return {
    ...res,
    starsRemaining: res.remainingStars,
  };
}

export function signOut(): void {
  setToken(null);
}

const LAST_IDENTITY_KEY = 'tunsay_last_identity';

export interface LastIdentity {
  studentName: string;
  schoolCode?: string;
}

export function saveLastIdentity(identity: LastIdentity): void {
  try { localStorage.setItem(LAST_IDENTITY_KEY, JSON.stringify(identity)); } catch { /* private mode */ }
}

export function getLastIdentity(): LastIdentity | null {
  try {
    const raw = localStorage.getItem(LAST_IDENTITY_KEY);
    return raw ? (JSON.parse(raw) as LastIdentity) : null;
  } catch { return null; }
}

export function clearLastIdentity(): void {
  try { localStorage.removeItem(LAST_IDENTITY_KEY); } catch { /* noop */ }
}
