import { useState, type FormEvent } from "react";
import "./Login.css";

import { API_BASE_URL } from "./api";

const DEMO_EMAIL =
  import.meta.env.VITE_DEMO_EMAIL || "admin123@example.com";

const DEMO_PASSWORD =
  import.meta.env.VITE_DEMO_PASSWORD || "admin@123";

type LoginResponse = {
  access_token?: string;
  token?: string;
  token_type?: string;
  detail?: string;
  message?: string;
  error?: string;
};

type LoginProps = {
  onLoginSuccess: () => void;
};

export default function Login({ onLoginSuccess }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDemoLogin = () => {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    setError("");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      let data: LoginResponse = {};

      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (!response.ok) {
        throw new Error(
          data.error ||
            data.detail ||
            data.message ||
            `Login failed with status ${response.status}`
        );
      }

      const token = data.access_token || data.token;

      if (!token) {
        throw new Error("Login succeeded but no access token was returned.");
      }

      if (rememberMe) {
        localStorage.setItem("access_token", token);
        sessionStorage.removeItem("access_token");
      } else {
        sessionStorage.setItem("access_token", token);
        localStorage.removeItem("access_token");
      }

      const meResponse = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      let meData: {
        is_admin?: boolean;
        is_active?: boolean;
        detail?: string;
      } = {};

      try {
        meData = await meResponse.json();
      } catch {
        meData = {};
      }

      if (!meResponse.ok) {
        localStorage.removeItem("access_token");
        sessionStorage.removeItem("access_token");

        throw new Error(
          meData.detail || "Unable to verify the logged-in account."
        );
      }

      if (!meData.is_admin) {
        localStorage.removeItem("access_token");
        sessionStorage.removeItem("access_token");

        throw new Error(
          "This account does not have administrator access."
        );
      }

      onLoginSuccess();
    } catch (err) {
      console.error("Login error:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to login. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">

      <div className="login-overlay" />

      {/* TOP RIGHT TAGLINE */}
      <div className="login-tagline">
        <span>Stronger Villages</span>
        <span>Brighter Tomorrow</span>
        <div className="tagline-line" />
      </div>

      <div className="login-container">

        {/* ================= LEFT ================= */}

        <section className="login-intro">

          {/* BRAND */}
          <div className="brand">
            <div className="brand-icon">
              <span>V</span>
            </div>

            <div className="brand-text">
              <h2>Village API</h2>
              <p>CONNECTING RURAL INDIA</p>
            </div>
          </div>

          {/* MAIN CONTENT */}
          <div className="intro-content">

            <h1>
              Empowering
              <br />
              Villages with Data
            </h1>

            <p className="intro-description">
              A unified API platform for States, Districts,
              <br />
              Sub-Districts and Villages across India.
            </p>

            <div className="features">

              <div className="feature">
                <div className="feature-icon">
                  <span>⌖</span>
                </div>

                <div className="feature-text">
                  <h3>Accurate</h3>
                  <h3>Location Data</h3>
                  <p>Reliable and up-to-date information</p>
                </div>
              </div>

              <div className="feature">
                <div className="feature-icon">
                  <span>♟</span>
                </div>

                <div className="feature-text">
                  <h3>Better</h3>
                  <h3>Governance</h3>
                  <p>Data-driven decision making</p>
                </div>
              </div>

              <div className="feature">
                <div className="feature-icon">
                  <span>▥</span>
                </div>

                <div className="feature-text">
                  <h3>Data for a</h3>
                  <h3>Brighter Tomorrow</h3>
                  <p>Empowering rural development</p>
                </div>
              </div>

            </div>
          </div>

          {/* BOTTOM LEFT */}
          <div className="bottom-slogan">
            <span>Rural Data.</span>
            <span>Real Impact.</span>
            <div />
          </div>

        </section>


        {/* ================= RIGHT ================= */}

        <section className="login-card">

          <div className="login-logo">
            <div className="login-logo-inner">
              V
            </div>
          </div>

          <h2>Administrator Login</h2>

          <p className="login-subtitle">
            Access the Village API Dashboard
          </p>

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>

            {/* EMAIL */}

            <div className="form-group">

              <label htmlFor="email">
                Email
              </label>

              <div className="input-wrapper">

                <span className="input-icon">
                  ✉
                </span>

                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="Enter your admin email"
                  disabled={loading}
                />

              </div>

            </div>


            {/* PASSWORD */}

            <div className="form-group">

              <label htmlFor="password">
                Password
              </label>

              <div className="input-wrapper">

                <span className="input-icon">
                  🔒
                </span>

                <input
                  id="password"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter your password"
                  disabled={loading}
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowPassword(
                      (current) => !current
                    )
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showPassword ? "◉" : "◌"}
                </button>

              </div>

            </div>


            {/* OPTIONS */}

            <div className="login-options">

              <label className="remember">

                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) =>
                    setRememberMe(
                      event.target.checked
                    )
                  }
                />

                <span className={`custom-checkbox ${rememberMe ? "checked" : ""}`} aria-hidden="true">
                  {rememberMe ? "✓" : ""}
                </span>

                <span>
                  Remember me
                </span>

              </label>

              <span className="secure-account">
                Secure account
              </span>

            </div>


            {/* BUTTON */}

            <button
              type="submit"
              className="signin-button"
              disabled={loading}
            >
              {loading
                ? "Signing in..."
                : "Sign In"}

              {!loading && (
                <span>→</span>
              )}
            </button>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                margin: "18px 0",
              }}
            >
              <div
                style={{
                  flex: 1,
                  height: "1px",
                  background: "rgba(0, 112, 91, 0.16)",
                }}
              />
              <span
                style={{
                  fontSize: "12px",
                  color: "#718096",
                  whiteSpace: "nowrap",
                }}
              >
                OR
              </span>
              <div
                style={{
                  flex: 1,
                  height: "1px",
                  background: "rgba(0, 112, 91, 0.16)",
                }}
              />
            </div>

            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={loading}
              style={{
                width: "100%",
                minHeight: "46px",
                borderRadius: "10px",
                border: "1px solid rgba(0, 128, 105, 0.35)",
                background: "#f0faf7",
                color: "#006b59",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(event) => {
                if (!loading) {
                  event.currentTarget.style.background = "#e2f5ef";
                }
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.background = "#f0faf7";
              }}
            >
              Use Demo Account
            </button>

          </form>


          {/* SECURE */}

          <div className="secure-section">

            <div className="secure-heading">

              <span />

              <div>
                <span className="lock">
                  🔒
                </span>

                SECURE ACCESS
              </div>

              <span />

            </div>

            <p>
              Authorized personnel only
            </p>

            <p>
              All activities are logged and monitored
            </p>

          </div>

        </section>

      </div>

    </main>
  );
}