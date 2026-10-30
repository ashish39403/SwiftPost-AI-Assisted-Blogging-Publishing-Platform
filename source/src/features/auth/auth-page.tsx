"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowRight, Check, ShieldCheck, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Logo } from "@/features/public-blog/logo"
import { accountHome, api, readError, type Account } from "@/lib/api"

type AuthMode = "login" | "signup"

const steps = [
  { label: "Research", detail: "Sources stay attached to the draft." },
  { label: "Write", detail: "Suggestions stay separate until you accept them." },
  { label: "Publish", detail: "Nothing goes live without your action." },
]

export function AuthPage({ mode }: { mode: AuthMode }) {
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const router = useRouter()
  const signingUp = mode === "signup"

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const password = String(form.get("password") ?? "")
    const email = String(form.get("email") ?? "").trim()
    if (signingUp && password !== String(form.get("password_confirm") ?? "")) {
      setNotice("The two passwords do not match.")
      return
    }
    setPending(true)
    setNotice(null)
    try {
      if (signingUp) {
        const registered = await api("/api/v1/auth/register/", {
          method: "POST",
          body: JSON.stringify({
            username: String(form.get("username") ?? "").trim(),
            email,
            password,
            first_name: String(form.get("first_name") ?? "").trim(),
            last_name: String(form.get("last_name") ?? "").trim(),
          }),
        })
        if (!registered.ok) {
          setNotice(await readError(registered, "Could not create the account."))
          return
        }
      }
      const loggedIn = await api("/api/v1/auth/login/", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      })
      if (!loggedIn.ok) {
        setNotice(await readError(loggedIn, "Could not sign in."))
        return
      }
      const account = ((await loggedIn.json()) as { user: Account }).user
      router.push(accountHome(account.role))
    } catch {
      setNotice("The API is not reachable. Start Django on port 8000 and try again.")
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-background">
      {/* Futuristic background */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 left-1/2 size-[42rem] -translate-x-1/2 rounded-full bg-primary/20 blur-3xl" />
        <div className="absolute top-1/3 -left-24 size-72 rounded-full bg-highlight/20 blur-3xl" />
        <div className="absolute bottom-0 right-0 size-96 rounded-full bg-success/10 blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{
            backgroundImage:
              "linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)",
            backgroundSize: "48px 48px",
            color: "var(--foreground)",
          }}
        />
      </div>

      <div className="relative mx-auto grid min-h-screen w-full max-w-6xl items-center gap-10 px-5 py-10 md:px-8 lg:grid-cols-[minmax(0,26rem)_1fr]">
        <section className="mx-auto w-full max-w-md">
          <div className="mb-8 flex items-center gap-2">
            <Link href="/" className="brand-link inline-flex text-foreground" aria-label="Back to SwiftPost home">
              <Logo />
            </Link>
            <span className="rounded-full border border-primary/30 bg-primary/10 px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-primary">
              Beta
            </span>
          </div>

          <div className="rounded-3xl border border-border/60 bg-card/70 p-6 shadow-[0_24px_80px_color-mix(in_oklch,var(--foreground)_12%,transparent)] backdrop-blur-xl sm:p-8">
            <p className="text-xs font-medium tracking-[0.16em] text-primary uppercase">
              {signingUp ? "Create your account" : "Welcome back"}
            </p>
            <h1 className="mt-3 font-heading text-3xl leading-tight tracking-tight sm:text-4xl">
              {signingUp ? "Start your publishing desk." : "Sign in to your desk."}
            </h1>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              {signingUp
                ? "A new account starts as a writer. Composer, Anna, and publishing are ready after you sign in."
                : "Use the email address on your account. Your session stays on this browser."}
            </p>

            <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
              {signingUp ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="First name" name="first_name" autoComplete="given-name" />
                  <Field label="Last name" name="last_name" autoComplete="family-name" />
                </div>
              ) : null}
              <Field label="Email" name="email" type="email" autoComplete="email" />
              {signingUp ? <Field label="Username" name="username" autoComplete="username" /> : null}
              <Field label="Password" name="password" type="password" autoComplete={signingUp ? "new-password" : "current-password"} />
              {signingUp ? <Field label="Confirm password" name="password_confirm" type="password" autoComplete="new-password" /> : null}
              <Button type="submit" className="mt-2 h-12 w-full rounded-xl text-base" disabled={pending}>
                {pending ? "Please wait…" : signingUp ? "Create account" : "Sign in"}
                <ArrowRight data-icon="inline-end" />
              </Button>
            </form>

            {notice ? (
              <p role="alert" className="mt-4 rounded-xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm leading-6 text-foreground">
                {notice}
              </p>
            ) : null}

            <p className="mt-6 text-sm text-muted-foreground">
              {signingUp ? "Already have an account?" : "New to SwiftPost?"}{" "}
              <Link className="interactive-link font-medium text-primary" href={signingUp ? "/login" : "/signup"}>
                {signingUp ? "Sign in" : "Create an account"}
              </Link>
            </p>
            <p className="mt-6 flex items-center gap-2 text-xs leading-5 text-muted-foreground">
              <ShieldCheck className="size-3.5 shrink-0 text-primary" aria-hidden="true" />
              Passwords stay on the server. Publishing still needs a person.
            </p>
          </div>
        </section>

        <aside className="relative hidden lg:block">
          <div className="relative overflow-hidden rounded-[2rem] border border-border/60 bg-card/60 p-8 backdrop-blur-xl">
            <div className="absolute -right-12 -top-12 size-48 rounded-full bg-primary/20 blur-3xl" />
            <div className="absolute -bottom-16 -left-10 size-56 rounded-full bg-highlight/20 blur-3xl" />
            <div className="relative">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium tracking-[0.14em] text-muted-foreground uppercase">Author desk</p>
                <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary">
                  <Sparkles className="size-3" />
                  Draft
                </span>
              </div>
              <h2 className="mt-6 font-heading text-4xl leading-tight tracking-tight">
                The future of clean energy is already local.
              </h2>
              <p className="mt-3 max-w-md text-sm leading-6 text-muted-foreground">
                A working story with sources beside it. Anna can suggest. You decide what stays.
              </p>
              <ol className="mt-8 space-y-3">
                {steps.map((step, index) => (
                  <li key={step.label} className="flex gap-3 rounded-2xl border border-border/60 bg-background/60 px-4 py-3 backdrop-blur">
                    <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                      {index + 1}
                    </span>
                    <span>
                      <span className="block text-sm font-medium">{step.label}</span>
                      <span className="mt-0.5 block text-xs leading-5 text-muted-foreground">{step.detail}</span>
                    </span>
                  </li>
                ))}
              </ol>
              <p className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">
                <Check className="size-3.5 text-primary" aria-hidden="true" />
                Visible sources. Explicit publish. No silent posts.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </main>
  )
}

function Field({ label, name, type = "text", autoComplete }: { label: string; name: string; type?: string; autoComplete: string }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium">{label}</span>
      <input className="auth-input" name={name} type={type} autoComplete={autoComplete} required />
    </label>
  )
}
