import { AuthPage } from "@/features/auth/auth-page"

export const metadata = { title: "Sign in" }

export default function LoginPage() {
  return <AuthPage mode="login" />
}
