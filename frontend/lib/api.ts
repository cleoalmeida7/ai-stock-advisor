const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL ?? "http://localhost:8000";

/**
 * Every call attaches the caller's own Supabase access token. The backend
 * verifies it independently on every request (see backend/app/core/auth.py)
 * - this helper does not imply any trust boundary on its own.
 */
export async function apiFetch(path: string, accessToken: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
      Authorization: `Bearer ${accessToken}`,
    },
  });
}
