"use client";

import React, { useState } from "react";
import { login } from "@/app/actions/auth";
import { Shield, User, Lock, AlertCircle, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Please fill in all fields.");
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const result = await login(username, password);
      if (result.success) {
        window.location.href = "/";
      } else {
        setError(result.error || "Authentication failed");
        setIsLoading(false);
      }
    } catch (err) {
      setError("An unexpected error occurred. Please try again.");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] flex items-center justify-center p-6 font-[Inter,system-ui,sans-serif]">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-[420px]"
      >
        {/* Brand/Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-[var(--mint)] flex items-center justify-center mb-3 shadow-md">
            <Shield size={20} className="text-[var(--bg)]" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text)] tracking-wider">
            AEROLINK
          </h1>
          <p className="text-[12px] text-[var(--text-3)] uppercase tracking-[3px] mt-1">
            Basecamp Command Center
          </p>
        </div>

        {/* Card */}
        <div className="bento-card p-8 shadow-xl border border-[var(--border)] relative overflow-hidden bg-[var(--surface)]">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-[var(--mint)]" />

          <h2 className="text-lg font-bold text-[var(--text)] mb-2">
            Administrator Access
          </h2>
          <p className="text-[13px] text-[var(--text-3)] mb-6">
            Provide authorized security credentials to access the command
            center.
          </p>
          <p className="text-[13px] text-[var(--text-3)] mb-6">
            Demo: Username: basecamp / Password: Aerolink2026
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-3.5 rounded-lg bg-[rgba(229,71,90,0.06)] border border-[var(--danger)] text-[13px] text-[var(--danger)] flex items-start gap-2.5"
              >
                <AlertCircle size={15} className="shrink-0 mt-0.5" />
                <span>{error}</span>
              </motion.div>
            )}

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-wider block">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)] w-4 h-4" />
                <input
                  type="text"
                  placeholder="admin"
                  className="bc-input w-full py-2.5 pl-10 pr-3 text-[14px]"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={isLoading}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-[var(--text-3)] uppercase tracking-wider block">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)] w-4 h-4" />
                <input
                  type="password"
                  placeholder="••••••••••••"
                  className="bc-input w-full py-2.5 pl-10 pr-3 text-[14px]"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="current-password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="sleek-btn sleek-btn-primary w-full py-2.5 mt-2 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 size={13} className="animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>Authenticate Access</>
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-[var(--text-3)] mt-8">
          Aerolink Basecamp v1.0 · Secured Endpoint
        </p>
      </motion.div>
    </div>
  );
}
