import type { Metadata, Viewport } from "next"
import { Fraunces, Geist, Geist_Mono } from "next/font/google"
import { RouteChrome } from "@/features/app/route-chrome"
import "./globals.css"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
})

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "SwiftPost — Turn ideas into stories worth reading",
    template: "%s · SwiftPost",
  },
  description:
    "SwiftPost is a publishing desk where authors research with Anna, review sources, and publish only when they decide the story is ready.",
  applicationName: "SwiftPost",
  openGraph: {
    title: "SwiftPost — Turn ideas into stories worth reading",
    description:
      "Research smarter. Write better. Publish with confidence. Anna assists. Authors approve.",
    type: "website",
    url: "/",
    images: [{ url: "/landing/turbines.jpg", alt: "Wind turbines on a green ridge" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "SwiftPost",
    description: "Research smarter. Write better. Publish with confidence.",
    images: ["/landing/turbines.jpg"],
  },
  robots: { index: true, follow: true },
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  interactiveWidget: "resizes-content",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fffdf7" },
    { media: "(prefers-color-scheme: dark)", color: "#202236" },
  ],
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      data-scroll-behavior="smooth"
      className={`${geistSans.variable} ${geistMono.variable} ${fraunces.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-background text-foreground">
        <RouteChrome>{children}</RouteChrome>
      </body>
    </html>
  )
}
