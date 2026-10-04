import { useEffect, useState } from "react";
import App from "./App";
import Login from "./Login.tsx";

import { API_BASE_URL } from "./api";

export default function AuthGate() {
  const [authenticated, setAuthenticated] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const verifyExistingToken = async () => {
      const token =
        localStorage.getItem("access_token") ||
        sessionStorage.getItem("access_token");

      if (!token) {
        setAuthenticated(false);
        setChecking(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          localStorage.removeItem("access_token");
          sessionStorage.removeItem("access_token");
          setAuthenticated(false);
          return;
        }

        const user = await response.json();

        if (!user.is_admin || user.is_active === false) {
          localStorage.removeItem("access_token");
          sessionStorage.removeItem("access_token");
          setAuthenticated(false);
          return;
        }

        setAuthenticated(true);
      } catch (error) {
        console.error("Authentication check failed:", error);
        setAuthenticated(false);
      } finally {
        setChecking(false);
      }
    };

    verifyExistingToken();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    sessionStorage.removeItem("access_token");
    setAuthenticated(false);
  };

  if (checking) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="text-slate-600">
          Checking administrator session...
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <Login
        onLoginSuccess={() => setAuthenticated(true)}
      />
    );
  }

  return <App onLogout={handleLogout} />;
}
