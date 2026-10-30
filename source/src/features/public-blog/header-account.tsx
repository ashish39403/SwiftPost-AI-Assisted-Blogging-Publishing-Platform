"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { accountHome, accountLabel, api, type Account } from "@/lib/api"

export function HeaderAccount() {
  const [account, setAccount] = useState<Account | null | undefined>(undefined)

  useEffect(() => {
    api("/api/v1/auth/me/")
      .then(async (response) => {
        if (!response.ok) {
          setAccount(null)
          return
        }
        setAccount(((await response.json()) as { user: Account }).user)
      })
      .catch(() => setAccount(null))
  }, [])

  if (account) {
    return (
      <>
        {account.role !== "reader" ? (
          <Button variant="ghost" asChild className="hidden sm:inline-flex">
            <Link href="/compose">Composer</Link>
          </Button>
        ) : null}
        <Button variant="ghost" asChild className="hidden sm:inline-flex">
          <Link href={accountHome(account.role)}>{accountLabel(account)}</Link>
        </Button>
        <Button asChild className="rounded-full">
          <Link href={accountHome(account.role)}>
            {account.role === "reader" ? "Discover stories" : "Open desk"}
            <ArrowRight data-icon="inline-end" />
          </Link>
        </Button>
      </>
    )
  }

  return (
    <>
      <Button variant="ghost" asChild className="inline-flex">
        <Link href="/login">Sign in</Link>
      </Button>
      <Button asChild className="rounded-full">
        <Link href="/signup">
          Start writing
          <ArrowRight data-icon="inline-end" />
        </Link>
      </Button>
    </>
  )
}
