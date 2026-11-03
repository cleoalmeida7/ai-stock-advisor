import { type NextRequest, NextResponse } from "next/server";

import { createMiddlewareClient } from "@/lib/supabase/middleware";

/**
 * UX convenience ONLY - this is NOT the security boundary. It just redirects
 * a logged-out browser to /login so they don't hit a confusing API error.
 * The backend independently verifies every request's Supabase access token
 * itself (backend/app/core/auth.py) and never trusts this redirect having
 * happened - a direct API call with no/invalid token is rejected regardless
 * of whether it ever passed through this middleware. See
 * docs/architecture-decisions.md ADR-007.
 */
export async function middleware(request: NextRequest) {
  const { supabase, response } = createMiddlewareClient(request);
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const isLoginPage = request.nextUrl.pathname.startsWith("/login");

  if (!user && !isLoginPage) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
