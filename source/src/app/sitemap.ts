import type { MetadataRoute } from "next"

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"
  return [
    {
      url: siteUrl,
      lastModified: new Date("2026-10-27"),
      changeFrequency: "weekly",
      priority: 1,
    },
  ]
}
