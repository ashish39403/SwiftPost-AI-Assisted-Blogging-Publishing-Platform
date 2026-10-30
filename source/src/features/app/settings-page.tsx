"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { AppShell } from "@/features/app/app-shell"
import { Button } from "@/components/ui/button"
import { api, accountLabel, type Account } from "@/lib/api"
import { LogOut, Settings as SettingsIcon, User, ShieldCheck, Bell } from "lucide-react"

export function SettingsPage() {
  const router = useRouter()
  const [account, setAccount] = useState<Account | null>(null)
  const [ready, setReady] = useState(false)
  const [notifications, setNotifications] = useState(true)
  const [compact, setCompact] = useState(false)
  const [dark, setDark] = useState(false)
  const [themeReady, setThemeReady] = useState(false)

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setDark(window.localStorage.getItem("swiftpost-theme") === "dark")
      setThemeReady(true)
    })
    return () => window.cancelAnimationFrame(frame)
  }, [])

  useEffect(() => {
    if (!themeReady) return
    document.documentElement.classList.toggle("dark", dark)
    window.localStorage.setItem("swiftpost-theme", dark ? "dark" : "light")
  }, [dark, themeReady])

  useEffect(() => {
    api("/api/v1/auth/me/")
      .then(async (response) => {
        if (response.ok) setAccount(((await response.json()) as { user: Account }).user)
        setReady(true)
      })
      .catch(() => setReady(true))
  }, [])

  async function signOut() {
    await api("/api/v1/auth/logout/", { method: "POST", body: "{}" })
    router.push("/login")
    router.refresh()
  }

  return (
    <AppShell eyebrow="Settings" title="Account and preferences.">
      <div className="grid gap-6 lg:grid-cols-[1fr_18rem]">
        <div className="space-y-6">
          <section className="rounded-3xl border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="flex size-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <User className="size-4" />
              </span>
              <h2 className="font-heading text-xl tracking-tight">Profile</h2>
            </div>
            {ready && account ? (
              <dl className="mt-5 grid gap-4 sm:grid-cols-2">
                <Field label="Name" value={accountLabel(account)} />
                <Field label="Username" value={account.username} />
                <Field label="Email" value={account.email} />
                <Field label="Role" value={account.role} />
              </dl>
            ) : (
              <p className="mt-4 text-sm text-muted-foreground">Loading account.</p>
            )}
            <p className="mt-4 text-xs text-muted-foreground">
              New accounts start as writers. An admin can still disable an account if needed.
            </p>
          </section>

          <section className="rounded-3xl border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="flex size-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Bell className="size-4" />
              </span>
              <h2 className="font-heading text-xl tracking-tight">Preferences</h2>
            </div>
            <div className="mt-5 space-y-4">
              <Toggle
                label="Email notifications"
                description="Receive updates about reviews and publishing."
                checked={notifications}
                onChange={setNotifications}
              />
              <Toggle
                label="Compact layout"
                description="Tighter spacing across the workspace."
                checked={compact}
                onChange={setCompact}
              />
              <Toggle
                label="Dark theme"
                description="Switch the workspace to a darker palette."
                checked={dark}
                onChange={setDark}
              />
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              Preferences are saved on this device.
            </p>
          </section>

          <section className="rounded-3xl border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="flex size-9 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
                <ShieldCheck className="size-4" />
              </span>
              <h2 className="font-heading text-xl tracking-tight">Session</h2>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Sign out of your account on this browser. Your session cookie will be cleared.
            </p>
            <Button
              variant="destructive"
              className="mt-4 rounded-xl"
              onClick={signOut}
            >
              <LogOut data-icon="inline-start" />
              Sign out
            </Button>
          </section>
        </div>

        <aside className="space-y-4">
          <section className="rounded-3xl border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="flex size-9 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                <SettingsIcon className="size-4" />
              </span>
              <h3 className="font-medium">Shortcuts</h3>
            </div>
            <ul className="mt-4 space-y-2 text-sm">
              <li>
                <Link href="/dashboard" className="interactive-link text-primary">
                  Back to desk
                </Link>
              </li>
              <li>
                <Link href="/editor/new" className="interactive-link text-primary">
                  New story
                </Link>
              </li>
              <li>
                <Link href="/compose" className="interactive-link text-primary">
                  Composer
                </Link>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </AppShell>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium tracking-[0.14em] text-muted-foreground uppercase">{label}</dt>
      <dd className="mt-1 text-sm font-medium">{value}</dd>
    </div>
  )
}

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <label className="flex items-start justify-between gap-4">
      <span>
        <span className="block text-sm font-medium">{label}</span>
        <span className="mt-0.5 block text-xs text-muted-foreground">{description}</span>
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
          checked ? "bg-primary" : "bg-muted"
        }`}
      >
        <span
          className={`inline-block size-4 transform rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
    </label>
  )
}
