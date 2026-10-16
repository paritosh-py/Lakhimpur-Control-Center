"use client";

import React from "react";
import { LayoutDashboard, Activity, LogOut, ClipboardList, Shield } from "lucide-react";
import { logout } from "@/app/actions/auth";

interface AdminSidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function AdminSidebar({ activeTab, setActiveTab }: AdminSidebarProps) {
  const navItems = [
    { id: "overview", icon: LayoutDashboard, label: "Overview" },
    { id: "requests", icon: ClipboardList, label: "Dispatcher" },
    { id: "intelligence", icon: Activity, label: "Intelligence" },
  ];

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = "/login";
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <aside className="sidebar flex flex-col">
      {/* Brand */}
      <div className="px-6 py-6 border-b border-[var(--border)]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[var(--mint)] flex items-center justify-center animate-pulse">
            <Shield size={14} className="text-[var(--bg)]" />
          </div>
          <div>
            <p className="text-[15px] font-bold text-[var(--text)] tracking-wide">Aerolink</p>
            <p className="text-[11px] text-[var(--text-3)] font-medium">Basecamp v1.0</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 pt-6 space-y-1">
        {navItems.map((item) => {
          const active = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 text-[14px] font-medium text-left rounded-lg transition-all ${
                active
                  ? "bg-[var(--surface-2)] text-[var(--mint)] shadow-sm font-semibold"
                  : "text-[var(--text-2)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]"
              }`}
            >
              <item.icon size={15} className={active ? "text-[var(--mint)]" : "text-[var(--text-3)]"} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 pb-5 space-y-1 border-t border-[var(--border)] pt-4 mt-4">
        <button 
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 w-full text-[var(--text-3)] hover:text-[var(--danger)] text-[13px] font-medium rounded-lg hover:bg-[var(--surface-2)] transition-all cursor-pointer"
        >
          <LogOut size={14} />
          Disconnect
        </button>
      </div>
    </aside>
  );
}
