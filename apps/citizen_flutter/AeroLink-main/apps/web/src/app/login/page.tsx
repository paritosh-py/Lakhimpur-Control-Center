import { redirect } from "next/navigation";
import { checkAuth } from "@/lib/auth";
import LoginForm from "@/components/LoginForm";

export default async function LoginPage() {
  const isAuth = await checkAuth();
  if (isAuth) {
    redirect("/");
  }
  return <LoginForm />;
}
