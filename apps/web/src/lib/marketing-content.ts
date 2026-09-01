export const SITE = {
  name: "AdzMate",
  tagline: "Campaign Auto-Pilot for Digital Agencies",
  description:
    "Multi-agent AI that decides LAUNCH, HOLD, or HALT — then drafts creatives, deploys landing pages, and publishes to Meta with human approval.",
  team: "Team SUDO · IDEALIZE 2026",
  email: "hello@adzmate.app",
  github: "https://github.com/itspasindu/adzmate-production-live",
};

export const NAV_LINKS = [
  { href: "/features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/about", label: "About" },
  { href: "/faq", label: "FAQ" },
  { href: "/contact", label: "Contact" },
];

export const FEATURES = [
  {
    title: "Multi-agent pipeline",
    description:
      "Creative, Sentiment, and Strategy agents run in parallel. One agent failing does not stop the whole campaign.",
    icon: "agents",
  },
  {
    title: "LAUNCH · HOLD · HALT",
    description:
      "A deterministic Signal Aggregator combines scores into one auditable recommendation — not a black-box chatbot.",
    icon: "decision",
  },
  {
    title: "Human-in-the-loop",
    description:
      "Managers approve every launch recommendation. Nothing goes live until you confirm in the review queue.",
    icon: "approve",
  },
  {
    title: "Meta Ads Manager publish",
    description:
      "OAuth connect, draft campaign structure, publish ad sets and creatives — starts PAUSED for safe review in Meta.",
    icon: "meta",
  },
  {
    title: "Creative generation",
    description:
      "Headlines, primary text, CTAs, and multi-format ad images from a product photo and brief.",
    icon: "creative",
  },
  {
    title: "Landing page deploy",
    description:
      "Auto-build branded landing previews linked to your ads — ready for CDN in production.",
    icon: "landing",
  },
  {
    title: "Auto-pause protection",
    description:
      "Spend spikes or negative comment floods can pause ads automatically when enabled.",
    icon: "shield",
  },
  {
    title: "Workspace isolation",
    description:
      "Multi-business workspaces, role-based approvals, and encrypted Meta token storage.",
    icon: "workspace",
  },
];

export const WORKFLOW_STEPS = [
  { step: "01", title: "Paste your brief", body: "Product photo, description, budget, and targeting in a simple wizard." },
  { step: "02", title: "Agents collaborate", body: "Creative, Sentiment, and Strategy run concurrently via the orchestrator." },
  { step: "03", title: "Get one decision", body: "Aggregator outputs LAUNCH, HOLD, or HALT with confidence and reasoning." },
  { step: "04", title: "Manager approves", body: "Review queue — approve or reject before any deploy or publish." },
  { step: "05", title: "Publish safely", body: "Landing page + Meta structure published PAUSED until you activate." },
  { step: "06", title: "Optimize & protect", body: "Rules boost winners; auto-pause guards spend and brand reputation." },
];

export const PRICING_TIERS = [
  {
    name: "Starter",
    price: "$49",
    period: "/ month",
    description: "Freelancers and solo media buyers getting started with agent-assisted launches.",
    features: [
      "1 workspace",
      "5 campaigns / month",
      "1 Meta ad account",
      "Creative + Sentiment + Strategy agents",
      "Review queue & timeline",
      "Email support",
    ],
    cta: "Start free trial",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$149",
    period: "/ month",
    description: "Growing agencies managing multiple clients with real Meta publish workflows.",
    features: [
      "3 workspaces",
      "30 campaigns / month",
      "3 Meta ad accounts",
      "Everything in Starter",
      "Optimization rules & auto-pause",
      "Priority support",
      "Team member invites",
    ],
    cta: "Start free trial",
    highlighted: true,
  },
  {
    name: "Agency",
    price: "Custom",
    period: "",
    description: "Large agencies needing white-label, unlimited scale, and dedicated onboarding.",
    features: [
      "Unlimited workspaces",
      "Unlimited campaigns",
      "Unlimited Meta accounts",
      "White-label option",
      "Slack / webhook alerts",
      "Dedicated success manager",
      "Custom SLA",
    ],
    cta: "Contact sales",
    highlighted: false,
  },
];

export const FAQ_ITEMS = [
  {
    q: "Is AdzMate a chatbot that runs my ads?",
    a: "No. AdzMate uses specialist agents (Creative, Sentiment, Strategy) plus a deterministic aggregator. You always approve before publish — it is automation with guardrails, not blind autopilot.",
  },
  {
    q: "Which ad platforms do you support?",
    a: "Meta (Facebook & Instagram) is fully integrated today. Google Ads and TikTok are on the roadmap — the Strategy agent already models multi-platform signals.",
  },
  {
    q: "Do ads go live automatically?",
    a: "Never without approval. Approved campaigns publish to Meta in PAUSED state. You activate them in Ads Manager when ready.",
  },
  {
    q: "What happens if an AI agent fails?",
    a: "The pipeline continues with warnings. Templates and fixtures fill gaps so you still get a recommendation instead of a hard failure.",
  },
  {
    q: "Can I use AdzMate without connecting Meta?",
    a: "Yes. Demo mode lets you run the full agent workflow with simulated publish IDs — ideal for testing and hackathon demos.",
  },
  {
    q: "How is my data secured?",
    a: "Supabase Auth for users, workspace-scoped API access, encrypted Meta tokens at rest, and CORS-restricted production API.",
  },
];

export const TEAM = [
  { name: "Pasindu Dewviman Pushpakumara", role: "Team Lead · Backend · Integrations" },
  { name: "Amasha Wijerathna", role: "Frontend · UX · Campaign flows" },
  { name: "Sandani Eshani Aramudale", role: "Integrations · QA · Meta & docs" },
];
