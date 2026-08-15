/**
 * The frontend's only network surface. Everything goes through server.ts's
 * /api/* proxy to the gateway — components never call services directly
 * (.claude/architecture.md §1). The wire shape is camelCase; the gateway
 * translates to snake_case for the Python services.
 */

import { Grade, Language, UserProfile } from '../types';

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

/**
 * Register, falling back to login when the account already exists (409 makes
 * the register call return null; login covers the returning child). Returns a
 * partial UserProfile on success, null when the backend is unreachable — the
 * caller proceeds with local state so the demo keeps working offline.
 */
export async function registerOrLogin(
  payload: RegisterPayload,
): Promise<Partial<UserProfile> | null> {
  const auth =
    (await postJson<TokenResponse>('/api/auth/register', payload)) ??
    (await postJson<TokenResponse>('/api/auth/login', {
      studentName: payload.studentName,
      schoolCode: payload.schoolCode,
      pin: payload.pin,
    }));
  if (!auth) return null;

  setToken(auth.accessToken);
  return {
    name: auth.profile.name,
    grade: auth.profile.grade,
    language: auth.profile.language,
  };
}

export function signOut(): void {
  setToken(null);
}
