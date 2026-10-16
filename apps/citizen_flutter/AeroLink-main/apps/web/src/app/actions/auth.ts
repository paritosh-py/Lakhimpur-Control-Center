"use server";

import { cookies } from "next/headers";

export async function login(username: string, password: string): Promise<{ success: boolean; error?: string }> {
  const adminUsername = process.env.ADMIN_USERNAME || "admin";
  const adminPassword = process.env.ADMIN_PASSWORD || "Aerolink2026!";
  
  if (username === adminUsername && password === adminPassword) {
    const cookieStore = await cookies();
    cookieStore.set("admin_session", "authenticated", {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      maxAge: 60 * 60 * 24, // 1 day
      path: "/",
    });
    return { success: true };
  }
  
  return { success: false, error: "Invalid username or password" };
}

export async function logout(): Promise<{ success: boolean }> {
  const cookieStore = await cookies();
  cookieStore.delete("admin_session");
  return { success: true };
}
