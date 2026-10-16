import { redirect } from "next/navigation";
import { checkAuth } from "@/lib/auth";
import AdminDashboard from "@/components/AdminDashboard";

export default async function Home() {
  const isAuth = await checkAuth();
  if (!isAuth) {
    redirect("/login");
  }
  return <AdminDashboard />;
}
