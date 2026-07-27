"use client";

import { useEffect, useState, useSyncExternalStore } from "react";

const AUTH_STORAGE_KEY = "joyon-review-auth";
const AUTH_USER = "admin";
const AUTH_PASSWORD = "123";

function subscribeToAuthState(callback: () => void) {
  const handleChange = () => callback();

  window.addEventListener("storage", handleChange);
  window.addEventListener("joyon-auth-change", handleChange);

  return () => {
    window.removeEventListener("storage", handleChange);
    window.removeEventListener("joyon-auth-change", handleChange);
  };
}

function getAuthSnapshot() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.localStorage.getItem(AUTH_STORAGE_KEY) === "true";
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useSyncExternalStore(
    subscribeToAuthState,
    getAuthSnapshot,
    () => false,
  );
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    function handleLogout() {
      window.localStorage.removeItem(AUTH_STORAGE_KEY);
      setUsername("");
      setPassword("");
      setError("");
      window.dispatchEvent(new Event("joyon-auth-change"));
    }

    window.addEventListener("joyon-logout", handleLogout);
    return () => {
      window.removeEventListener("joyon-logout", handleLogout);
    };
  }, []);

  if (isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f5f6f8] px-4">
      <div className="w-full max-w-md rounded-[22px] border border-slate-200 bg-white p-6 shadow-[0_24px_56px_rgba(15,23,42,0.08)] sm:p-8">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-[16px] bg-slate-900 text-[24px] font-bold text-white">
          J
        </div>

        <div className="mt-5 text-center">
          <h1 className="font-display text-[28px] font-semibold text-[#111827]">
            JoyON
          </h1>
          <p className="mt-2 text-[14px] text-[#667085]">
            Sign in to access the workspace.
          </p>
        </div>

        <form
          className="mt-7 space-y-4"
          onSubmit={(event) => {
            event.preventDefault();

            if (username.trim() === AUTH_USER && password === AUTH_PASSWORD) {
              window.localStorage.setItem(AUTH_STORAGE_KEY, "true");
              setError("");
              window.dispatchEvent(new Event("joyon-auth-change"));
              return;
            }

            setError("Incorrect username or password.");
          }}
        >
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            className="h-12 w-full rounded-[14px] border border-slate-200 bg-white px-4 text-[15px] font-medium text-[#111827] outline-none transition placeholder:text-slate-400 focus:border-[var(--accent)] focus:ring-4 focus:ring-[rgba(37,99,235,0.10)]"
            placeholder="Username"
          />

          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            className="h-12 w-full rounded-[14px] border border-slate-200 bg-white px-4 text-[15px] font-medium text-[#111827] outline-none transition placeholder:text-slate-400 focus:border-[var(--accent)] focus:ring-4 focus:ring-[rgba(37,99,235,0.10)]"
            placeholder="Password"
          />

          {error ? (
            <div className="rounded-[14px] border border-red-200 bg-red-50 px-4 py-3 text-[14px] font-medium text-red-700">
              {error}
            </div>
          ) : null}

          <button
            type="submit"
            className="h-12 w-full rounded-[14px] bg-slate-900 text-[15px] font-semibold text-white transition hover:bg-slate-800"
          >
            Login
          </button>
        </form>
      </div>
    </main>
  );
}
