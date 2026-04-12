import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Only protect dashboard routes
  if (!pathname.startsWith("/dashboard")) {
    return NextResponse.next();
  }

  // Get token from cookies
  const token = request.cookies.get("token")?.value;

  // No token → redirect to login
  if (!token) {
    return NextResponse.redirect(
      new URL("/login?expired=true", request.url)
    );
  }

  // Decode token to get role and expiry
  let decodedToken: any = null;
  try {
    const parts = token.split(".");
    if (parts.length === 3) {
      const payload = JSON.parse(
        Buffer.from(parts[1], "base64").toString("utf-8")
      );
      decodedToken = payload;
    }
  } catch (error) {
    console.error("Failed to decode token");
    return NextResponse.redirect(new URL("/login?expired=true", request.url));
  }

  if (!decodedToken) {
    return NextResponse.redirect(new URL("/login?expired=true", request.url));
  }

  // Check token expiry
  const now = Math.floor(Date.now() / 1000);
  if (decodedToken.exp && decodedToken.exp < now) {
    return NextResponse.redirect(new URL("/login?expired=true", request.url));
  }

  // Get user role
  const userRole = decodedToken.role;

  // Check if route matches user role
  if (pathname === "/dashboard/developer" && userRole !== "developer") {
    // Redirect to correct dashboard
    const roleMap: Record<string, string> = {
      manager: "/dashboard/manager",
      ceo: "/dashboard/ceo",
    };
    return NextResponse.redirect(
      new URL(roleMap[userRole] || "/login", request.url)
    );
  }

  if (pathname === "/dashboard/manager" && userRole !== "manager") {
    const roleMap: Record<string, string> = {
      developer: "/dashboard/developer",
      ceo: "/dashboard/ceo",
    };
    return NextResponse.redirect(
      new URL(roleMap[userRole] || "/login", request.url)
    );
  }

  if (pathname === "/dashboard/ceo" && userRole !== "ceo") {
    const roleMap: Record<string, string> = {
      developer: "/dashboard/developer",
      manager: "/dashboard/manager",
    };
    return NextResponse.redirect(
      new URL(roleMap[userRole] || "/login", request.url)
    );
  }

  // Token valid and role matches route → allow access
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
