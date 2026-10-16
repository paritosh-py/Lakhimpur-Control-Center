import { cookies, headers } from "next/headers";

export async function checkAuth(): Promise<boolean> {
  try {
    const cookieStore = await cookies();
    if (cookieStore.get("admin_session")?.value === "authenticated") {
      return true;
    }

    // Secure fallback for local bridge serial uplink connection
    const headerList = await headers();
    const bridgeAuth = headerList.get("x-bridge-auth");
    const adminPassword = process.env.ADMIN_PASSWORD || "Aerolink2026!";
    if (bridgeAuth === adminPassword) {
      return true;
    }

    return false;
  } catch {
    return false;
  }
}
