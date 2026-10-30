"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import * as DropdownMenu from "@radix-ui/react-dropdown-menu"
import { ChevronDown, LogOut, Settings as SettingsIcon, User } from "lucide-react"
import { accountLabel, api, type Account } from "@/lib/api"

export function AccountMenu() {
  const router = useRouter()
  const [account, setAccount] = useState<Account | null>(null)

  useEffect(() => {
    let active = true
    api("/api/v1/auth/me/")
      .then(async (response) => {
        if (!response.ok) return null
        const body = (await response.json()) as { user: Account }
        return body.user
      })
      .then((user) => {
        if (active) setAccount(user)
      })
      .catch(() => {
        if (active) setAccount(null)
      })
    return () => {
      active = false
    }
  }, [])

  async function logout() {
    await api("/api/v1/auth/logout/", { method: "POST", body: "{}" })
    router.push("/login")
    router.refresh()
  }

  if (!account) {
    return <span className="text-xs text-muted-foreground">Not signed in</span>
  }

  const label = accountLabel(account)

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button className="app-profile" type="button" aria-label="Account menu">
          <span className="flex size-7 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
            {label.slice(0, 1).toUpperCase()}
          </span>
          <span className="hidden text-sm font-medium sm:inline">{label}</span>
          <ChevronDown className="size-3.5 text-muted-foreground" />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className="z-50 min-w-[12rem] overflow-hidden rounded-xl border border-border bg-card p-1 shadow-lg"
        >
          <div className="px-3 py-2">
            <p className="text-sm font-medium">{label}</p>
            <p className="text-xs text-muted-foreground">{account.email}</p>
          </div>
          <DropdownMenu.Separator className="my-1 h-px bg-border" />
          <DropdownMenu.Item asChild>
            <Link
              href="/settings"
              className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm outline-none hover:bg-muted"
            >
              <SettingsIcon className="size-4" />
              Settings
            </Link>
          </DropdownMenu.Item>
          <DropdownMenu.Item asChild>
            <Link
              href="/dashboard"
              className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm outline-none hover:bg-muted"
            >
              <User className="size-4" />
              Your desk
            </Link>
          </DropdownMenu.Item>
          <DropdownMenu.Separator className="my-1 h-px bg-border" />
          <DropdownMenu.Item
            onSelect={(event) => {
              event.preventDefault()
              void logout()
            }}
            className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm text-destructive outline-none hover:bg-destructive/10"
          >
            <LogOut className="size-4" />
            Sign out
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}