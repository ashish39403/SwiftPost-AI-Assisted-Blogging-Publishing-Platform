import { AuthPage } from "@/features/auth/auth-page"

export const metadata = { title: "Create an account" }

export default function SignupPage() {
  return <AuthPage mode="signup" />
}
