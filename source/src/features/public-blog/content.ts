export const previewPanels = [
  { id: "write", label: "Write" },
  { id: "research", label: "Research" },
  { id: "anna", label: "Anna AI" },
  { id: "sources", label: "Sources" },
  { id: "review", label: "Review" },
] as const

export type PreviewPanelId = (typeof previewPanels)[number]["id"]

export const draftSeed = {
  kicker: "Draft / The future of clean energy",
  title: "The future of clean energy",
  lede: "Clean energy is no longer a distant idea — it is a practical, rapidly advancing reality. From next-generation solar cells to smarter grids, innovation is reshaping how we power our lives and protect our planet.",
}

export const annaSuggestion = {
  body: "Try adding a real-world example to illustrate the impact, such as a city or company leading the transition to clean energy.",
  additionTitle: "Suggested addition",
  addition:
    "Case study: How Copenhagen became a model clean-energy city. This example shows practical progress and can strengthen your argument.",
}

export const demoReplies: { match: string; reply: string }[] = [
  {
    match: "title",
    reply:
      "A tighter title: “The future of clean energy is already local.” Keep it as a suggestion until you accept it.",
  },
  {
    match: "source",
    reply:
      "I can keep the IEA update and the solar piece in the working set. Remove any source you do not trust before you review.",
  },
  {
    match: "shorten",
    reply:
      "Opening, shortened: Clean energy is no longer distant. Grids, solar, and city policy are already changing how we power daily life.",
  },
  {
    match: "publish",
    reply:
      "I cannot publish this. Check the review list, then use Publish yourself. A suggestion is not approval.",
  },
]

export const fallbackReply =
  "I can suggest a tighter opening, a title, or another source. Insert what you accept. Nothing here is published until you confirm it."

export const annaPromptExamples = [
  "Find a stronger opening",
  "Suggest three precise titles",
  "Turn these notes into an outline",
  "Flag claims that need a source",
] as const

export const heroStoryWords = ["stories", "sharp drafts", "new perspectives", "a point of view"] as const

export const sources = [
  {
    id: "iea",
    title: "The next wave of renewable energy",
    host: "iea.org",
    retrieved: "Retrieved today",
    image: "/landing/turbines.jpg",
    imageAlt: "Wind turbines on a field at sunset",
  },
  {
    id: "solar",
    title: "How solar innovation is changing the game",
    host: "nature.com",
    retrieved: "Retrieved today",
    image: "/landing/solar.jpg",
    imageAlt: "Rows of solar panels catching daylight",
  },
  {
    id: "grid",
    title: "A global shift toward cleaner grids",
    host: "reuters.com",
    retrieved: "Retrieved yesterday",
    image: "/landing/grid.jpg",
    imageAlt: "High-voltage power lines against a dusk sky",
  },
]

export const reviewItems = [
  { id: "content", label: "Content reviewed" },
  { id: "sources", label: "Sources attached" },
  { id: "ready", label: "Ready to publish" },
] as const

export const stories = [
  {
    category: "Technology",
    title: "The craft of making tools people trust",
    excerpt:
      "The details that make a tool dependable are often the same details that make it feel human.",
    author: "Noah Williams",
    initials: "NW",
    readingTime: "8 min read",
    image: "/landing/workspace.jpg",
    imageAlt: "A focused writing workspace with a laptop and notebook",
  },
  {
    category: "Sports",
    title: "The new generation redefining greatness",
    excerpt:
      "How today’s athletes are changing the game on and off the field.",
    author: "Marcus Lee",
    initials: "ML",
    readingTime: "6 min read",
    image: "/landing/tennis.jpg",
    imageAlt: "A tennis player preparing to return a ball on a clay court",
  },
  {
    category: "Culture",
    title: "The cities that keep culture alive",
    excerpt:
      "A journey through the places where history, creativity, and community meet.",
    author: "Elena Rossi",
    initials: "ER",
    readingTime: "7 min read",
    image: "/landing/flowers.jpg",
    imageAlt: "A narrow street with flowering vines and warm evening light",
  },
] as const

export const storyShelves = [
  {
    category: "Technology",
    note: "Tools, systems, and the human choices inside them.",
    stories: [
      { title: "The quiet craft behind dependable tools", author: "Noah Williams", readingTime: "5 min read", image: "/landing/workspace.jpg", imageAlt: "A focused writing workspace with a laptop and notebook" },
      { title: "A cleaner grid starts with better questions", author: "Priya Shah", readingTime: "9 min read", image: "/landing/grid.jpg", imageAlt: "Power lines stretching across an evening landscape" },
    ],
  },
  {
    category: "Sports",
    note: "The routines, risks, and resilience behind the result.",
    stories: [
      { title: "The long run is a practice in attention", author: "Aisha Grant", readingTime: "6 min read", image: "/landing/runner.jpg", imageAlt: "A runner moving along a road in warm daylight" },
      { title: "What a comeback teaches before the final set", author: "Marcus Lee", readingTime: "7 min read", image: "/landing/tennis.jpg", imageAlt: "A tennis player preparing to return a ball on a clay court" },
    ],
  },
  {
    category: "Culture",
    note: "Places and rituals that make a city feel lived in.",
    stories: [
      { title: "The streets that make us slow down", author: "Elena Rossi", readingTime: "6 min read", image: "/landing/street.jpg", imageAlt: "A sunlit street with textured building facades" },
      { title: "Small rituals, shared at the table", author: "Tara Banerjee", readingTime: "4 min read", image: "/landing/flowers.jpg", imageAlt: "Flowering vines along a narrow street" },
    ],
  },
] as const

export const capabilities = [
  {
    title: "Live research, real insights",
    body: "Bring trusted sources, links, and retrieval times into the draft you are already writing.",
    tone: "research" as const,
  },
  {
    title: "Writing assistance, on your terms",
    body: "Anna helps you brainstorm, draft, and refine, while keeping your voice front and center.",
    tone: "writing" as const,
  },
  {
    title: "Author-controlled publishing",
    body: "Review, cite, and publish when you are ready. Your content, your standards, your audience.",
    tone: "publish" as const,
  },
]

export const steps = [
  {
    number: "01",
    title: "Research",
    body: "Start from a brief. Anna collects sources with URLs and retrieval times. You keep or discard them.",
  },
  {
    number: "02",
    title: "Shape",
    body: "Ask for a title, an outline, or a revision. Generated text stays a suggestion until you insert it.",
  },
  {
    number: "03",
    title: "Publish",
    body: "Review the draft yourself. Publishing is a separate action. A finished suggestion is not approval.",
  },
]
