"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface AuthUser {
  userId: string;
  role: "developer" | "manager" | "ceo";
  orgId: string;
  displayName: string;
}

interface UseAuthReturn {
  user: AuthUser | null;
  role: string | null;
  orgId: string | null;
  displayName: string | null;
  isAuthenticated: boolean;
  logout: () => void;
}

export function useAuth(): UseAuthReturn {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Get token from localStorage
    const token = localStorage.getItem("access_token");

    if (!token) {
      setIsAuthenticated(false);
      return;
    }

    try {
      // Decode JWT payload
      const parts = token.split(".");
      if (parts.length !== 3) {
        throw new Error("Invalid token format");
      }

      const payload = JSON.parse(atob(parts[1]));

      // Check token expiry
      const now = Math.floor(Date.now() / 1000);
      if (payload.exp && payload.exp < now) {
        // Token expired
        logout();
        return;
      }

      // Token valid
      const authUser: AuthUser = {
        userId: payload.sub,
        role: payload.role,
        orgId: payload.org_id,
        displayName: payload.display_name,
      };

      setUser(authUser);
      setIsAuthenticated(true);

      // Also store org_id in localStorage for dashboard access
      localStorage.setItem("user_org_id", authUser.orgId);
    } catch (error) {
      console.error("Failed to decode token:", error);
      logout();
    }
  }, []);

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_org_id");

    // Clear cookies
    document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;";

    setUser(null);
    setIsAuthenticated(false);

    router.push("/login");
  };

  return {
    user,
    role: user?.role || null,
    orgId: user?.orgId || null,
    displayName: user?.displayName || null,
    isAuthenticated,
    logout,
  };
}
