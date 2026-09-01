export const SITE = {
  name: "AdzMate",
  tagline: "Campaign Auto-Pilot for Digital Agencies",
  description:
    "Multi-agent AI that decides LAUNCH, HOLD, or HALT — then drafts creatives, deploys landing pages, and publishes to Meta with human approval.",
  team: "Team SUDO · IDEALIZE 2026",
  email: "hello@adzmate.app",
  github: "https://github.com/itspasindu/adzmate-production-live",
} as const;

export const NAV_LINKS = [
  { href: "/features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/about", label: "About" },
  { href: "/faq", label: "FAQ" },
  { href: "/contact", label: "Contact" },
] as const;

export const FOOTER_LINKS = {
  product: [
    { href: "/features", label: "Features" },
    { href: "/pricing", label: "Pricing" },
    { href: "/faq", label: "FAQ" },
    { href: "/dashboard", label: "Dashboard" },
  ],
  company: [
    { href: "/about", label: "About us" },
    { href: "/contact", label: "Contact" },
  ],
  legal: [
    { href: "/privacy", label: "Privacy policy" },
    { href: "/terms", label: "Terms of service" },
  ],
} as const;

export const STATS = [
  { value: "3", label: "Specialist AI agents", hint: "Creative · Sentiment · Strategy" },
  { value: "1", label: "Clear decision", hint: "LAUNCH · HOLD · HALT" },
  { value: "0", label: "Surprise publishes", hint: "Human approval required" },
] as const;

export const PROBLEMS = [
  {
    title: "Too many dashboards",
    body: "Meta, Google, and TikTok each need separate monitoring, creatives, and pause decisions — managers context-switch all day.",
  },
  {
    title: "Slow reaction time",
    body: "ROAS drops and negative comment floods happen overnight. Manual review can't keep pace with 24/7 ad spend.",
  },
  {
    title: "Fragmented launch workflow",
    body: "Brief → creative → audience → landing page → publish is split across tools, spreadsheets, and people.",
  },
  {
    title: "No unified signal",
    body: "Creative quality, brand sentiment, and performance rarely converge into one actionable recommendation.",
  },
] as const;

export const AGENTS = [
  {
    name: "Creative Agent",
    role: "Copy & visuals",
    body: "Generates headlines, primary text, CTAs, and multi-format ad images from your product brief and photo.",
    outputs: ["Meta feed ads", "Story formats", "Audience hints"],
  },
  {
    name: "Sentiment Agent",
    role: "Brand safety",
    body: "Analyzes social comments and brand tone so risky campaigns are held or halted before spend accelerates.",
    outputs: ["Sentiment score", "Comment samples", "Risk flags"],
  },
  {
    name: "Strategy Agent",
    role: "Performance",
    body: "Evaluates spend, ROAS, and cross-platform signals to recommend pause, resume, or budget shifts.",
    outputs: ["ROAS analysis", "Spend burn", "Platform breakdown"],
  },
  {
    name: "Signal Aggregator",
    role: "Decision engine",
    body: "Combines all agent outputs with rule gates and optional LLM brief into one clear LAUNCH, HOLD, or HALT.",
    outputs: ["Confidence score", "Reasoning", "Manager recommendation"],
  },
] as const;

export const WORKFLOW_STEPS = [
  { step: "01", title: "Describe your product", body: "Upload a photo, write a brief, set budget and targeting in a simple wizard." },
  { step: "02", title: "Agents run in parallel", body: "Creative, Sentiment, and Strategy agents analyze your campaign concurrently." },
  { step: "03", title: "Review the recommendation", body: "Aggregator produces LAUNCH, HOLD, or HALT — you approve or reject in the review queue." },
  { step: "04", title: "Deploy & publish", body: "Landing page goes live, Meta draft publishes to Ads Manager (PAUSED until you activate)." },
  { step: "05", title: "Optimize & auto-pause", body: "Rules boost winners, pause weak ads, and halt spend on spikes or comment floods." },
] as const;

export const FEATURES = [
  {
    title: "Multi-agent orchestration",
    body: "Specialist agents run in parallel with resilient fallbacks — one failure doesn't kill the pipeline.",
    icon: "agents",
  },
  {
    title: "Human-in-the-loop approvals",
    body: "Nothing publishes without manager sign-off. Auto-pause is configurable, not blind automation.",
    icon: "shield",
  },
  {
    title: "Meta Marketing API",
    body: "OAuth connect, draft → review → publish campaign, ad set, and ads directly to Ads Manager.",
    icon: "meta",
  },
  {
    title: "Landing page deployer",
    body: "Jinja-built product pages with your brand colors, headline, and CTA — ready for ad destinations.",
    icon: "page",
  },
  {
    title: "Audience automation",
    body: "Location, age, gender, interests, lookalikes, and retargeting with AI-generated audience hints.",
    icon: "target",
  },
  {
    title: "Optimization rules",
    body: "CPA, ROAS, CTR, CPC, and frequency rules with simulated or live ticks to shift budget to winners.",
    icon: "chart",
  },
  {
    title: "Workspace isolation",
    body: "Multi-business accounts, role-based approvals, and Supabase auth for agency client separation.",
    icon: "workspace",
  },
  {
    title: "Action timeline",
    body: "Every agent decision, deploy, publish, and auto-pause logged in a persistent audit trail.",
    icon: "timeline",
  },
  {
    title: "Gemini-powered enrichment",
    body: "Google Gemini for copy, insights, and manager briefs — with template fallback when LLM is off.",
    icon: "spark",
  },
] as const;

export const PRICING_TIERS = [
  {
    id: "starter",
    name: "Starter",
    price: 49,
    period: "month",
    description: "For freelancers and solo media buyers getting started with agent-assisted campaigns.",
    features: [
      "1 workspace",
      "5 campaigns per month",
      "1 Meta ad account",
      "Creative + Sentiment + Strategy agents",
      "Review queue & approvals",
      "Landing page deploy",
      "Email support",
    ],
    cta: "Start free trial",
    highlighted: false,
  },
  {
    id: "pro",
    name: "Pro",
    price: 149,
    period: "month",
    description: "For growing agencies managing multiple clients with real Meta publish and optimization.",
    features: [
      "3 workspaces",
      "30 campaigns per month",
      "3 Meta ad accounts",
      "Everything in Starter",
      "Meta live publish",
      "Auto-pause & optimization rules",
      "Priority support",
      "Team member invites",
    ],
    cta: "Get Pro",
    highlighted: true,
  },
  {
    id: "agency",
    name: "Agency",
    price: null,
    period: "custom",
    description: "For established agencies needing unlimited scale, white-label, and dedicated onboarding.",
    features: [
      "Unlimited workspaces",
      "Unlimited campaigns",
      "Unlimited Meta accounts",
      "Everything in Pro",
      "White-label option",
      "Google & TikTok (roadmap)",
      "Dedicated success manager",
      "SLA & custom contracts",
    ],
    cta: "Contact sales",
    highlighted: false,
  },
] as const;

export const FAQ_ITEMS = [
  {
    q: "What makes AdzMate different from a chatbot?",
    a: "AdzMate uses specialist agents (Creative, Sentiment, Strategy) that run in parallel, plus a deterministic Signal Aggregator. Decisions are auditable rule gates — not a single black-box prompt.",
  },
  {
    q: "Do ads publish automatically without my approval?",
    a: "No. Every LAUNCH or HALT recommendation goes to your review queue. You must approve before deploy and Meta publish. Auto-pause only triggers when you enable it.",
  },
  {
    q: "Which ad platforms are supported?",
    a: "Meta (Facebook & Instagram) is fully integrated for OAuth, draft, and publish. Google Ads and TikTok are on the roadmap — the Strategy agent already models multi-platform signals.",
  },
  {
    q: "What AI models does AdzMate use?",
    a: "Google Gemini (gemini-2.0-flash) for copy and insights, with optional DistilBERT for sentiment. Templates and fixtures work when LLM is disabled or quota is exceeded.",
  },
  {
    q: "Is my Meta data secure?",
    a: "Access tokens are encrypted at rest. OAuth state uses Redis in production. We request only the Marketing API scopes needed for campaign management.",
  },
  {
    q: "Can I try AdzMate without connecting Meta?",
    a: "Yes. Demo mode runs with fixture metrics and simulated publish IDs so you can explore the full agent workflow before connecting a real ad account.",
  },
  {
    q: "How does pricing work after the hackathon?",
    a: "Starter ($49/mo), Pro ($149/mo), and custom Agency plans. Campaign and workspace limits apply per tier. Contact us for early-access pricing.",
  },
] as const;

export const TEAM = [
  { name: "Pasindu Dewviman Pushpakumara", role: "Team Lead · Backend & Integrations" },
  { name: "Amasha Wijerathna", role: "Frontend · UX · Campaign flows" },
  { name: "Sandani Eshani Aramudale", role: "Integrations · QA · Meta app" },
] as const;

export const TESTIMONIALS = [
  {
    quote: "We went from a product photo to a full Meta draft in under ten minutes — with a clear LAUNCH recommendation we could defend to the client.",
    author: "Agency beta user",
    role: "Digital marketing agency",
  },
  {
    quote: "The HALT signal on low ROAS saved us from burning budget on a underperforming creative set.",
    author: "In-house growth lead",
    role: "E-commerce brand",
  },
] as const;
