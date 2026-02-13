# Skill Forge — Webapp Design Document

**Date:** 2026-02-12
**Status:** Draft
**Author:** Antony + Claude

---

## 1. Product Overview

Skill Forge is a builder-first webapp with a public gallery for creating, publishing, and discovering Claude Code skills. It transforms the existing `skill-forge.md` CLI command — a 10-phase research-driven skill creation workflow — into an interactive web experience.

### Core Value Proposition

A guided, research-driven skill builder powered by Claude Opus that produces high-quality Claude Code skills grounded in real web research, not training data assumptions.

### Monetization Model

| Tier | Price | What they get |
|------|-------|--------------|
| **Free** | $0 | Full builder, all skills published publicly, rate-limited (~2-3 skills/month) |
| **Pro** | Subscription (via Stripe, post-MVP) | Private skills, higher limits, priority |
| **BYOK** | Free or reduced subscription | Bring your own Anthropic API key, unlimited usage, private skills |

**Key mechanic:** Free tier skills are always public. This populates the gallery organically. Paying buys privacy. Same model that made GitHub successful early on.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                    SKILL FORGE                       │
│                  Next.js App (Vercel)                │
├──────────────┬──────────────┬───────────────────────┤
│   Frontend   │  API Routes  │   Background Jobs     │
│  (React/TSX) │ (Next.js API)│  (Vercel Functions)   │
│              │              │                        │
│  Wizard UI   │  /api/forge  │  Multi-agent research  │
│  Gallery     │  /api/auth   │  Skill synthesis       │
│  Dashboard   │  /api/skills │  Packaging             │
│  Settings    │  /api/gallery│                        │
└──────┬───────┴──────┬───────┴───────────┬───────────┘
       │              │                   │
       │         ┌────┴────┐        ┌─────┴─────┐
       │         │ Supabase│        │ Anthropic  │
       │         │  (DB +  │        │   API      │
       │         │  Auth)  │        │  (Opus)    │
       │         └─────────┘        └───────────┘
```

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Server components, API routes, streaming |
| Language | TypeScript | Type safety across full stack |
| Styling | Tailwind + shadcn/ui | Fast UI development, consistent design |
| Auth + DB | Supabase | Auth, Postgres, RLS, realtime — one service |
| AI | Anthropic API (Opus) | All Claude calls via server-side SDK |
| Hosting | Vercel | Native Next.js support, edge functions |
| File storage | Supabase (Postgres) | Skill files are just text, keep it simple |

### Claude Orchestration

All Claude calls use `claude-opus-4-6`. No model routing — consistent quality across every step.

```
┌──────────────────────────────────────┐
│  Claude Orchestration Service        │
│                                      │
│  Model: claude-opus-4-6 (always)     │
│                                      │
│  Key routing:                        │
│    BYOK user → user's key            │
│    Everyone else → platform key      │
│         + increment usage counter    │
└──────────────────────────────────────┘
```

---

## 3. The Forge Wizard

The 10 CLI phases collapse into 4 wizard steps:

```
Step 1: Describe    Step 2: Research    Step 3: Review    Step 4: Export
●━━━━━━━━━━━━━━━━━━○━━━━━━━━━━━━━━━━━━○━━━━━━━━━━━━━━━○
[Phases A+B]        [Phases C-G]        [Phases H+I]     [Phase J]
```

### Step 1: Describe (Phases A + B)

Chat-based interview. User lands on a clean page with a single prompt: "What skill do you want to build?"

- Claude drives the conversation, asking one question at a time
- After 2-3 rounds, Claude generates the Intent Summary as a structured card the user can edit inline
- Once confirmed, Claude fires off surface-scan web research in the background
- Research Brief appears as an expandable panel when complete

**UI layout:** Split — chat on the left, live-updating Intent Summary card on the right.

```
┌─────────────────────────┬──────────────────────┐
│                         │  Intent Summary      │
│   Chat with Claude      │  ┌────────────────┐  │
│                         │  │ Name: ...       │  │
│  > What skill do you    │  │ Purpose: ...    │  │
│    want to build?       │  │ Trigger: ...    │  │
│                         │  │ Must include:   │  │
│  < I want a skill that  │  │ Must exclude:   │  │
│    helps with...        │  │ Quality bar:    │  │
│                         │  └────────────────┘  │
│  > Great! Who is the    │                      │
│    target audience?     │  Research Brief  v   │
│                         │  [expandable panel]  │
└─────────────────────────┴──────────────────────┘
```

**Backend:** Claude Opus with a tool definition for `update_intent`. Frontend listens for tool calls in the SSE stream and updates the right-hand panel in real time.

### Step 2: Research (Phases C-G)

The heavy lifting — made visual and transparent. Phases C (skill-creator patterns) and D (prompt-optimizer principles) are internalized as system prompt engineering on the backend. Users never see these steps.

**Research dashboard:**

```
┌─────────────────────────────────────────────────┐
│  Researching: "Kubernetes Debugging Skill"      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━░░░░  72%      │
│                                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ Thread 1    │ │ Thread 2    │ │ Thread 3   │ │
│  │ Core APIs   │ │ Best        │ │ Common     │ │
│  │ & Tools     │ │ Practices   │ │ Pitfalls   │ │
│  │             │ │             │ │            │ │
│  │ 4 sources   │ │ searching   │ │ 3 sources  │ │
│  │   found     │ │             │ │   found    │ │
│  └─────────────┘ └─────────────┘ └────────────┘ │
│                                                  │
│  Live Feed:                                      │
│  - Found: kubernetes.io/docs/debug (Thread 1)   │
│  - Found: learnk8s.io/troubleshooting (Thread 3)│
│  - Searching: "k8s debugging 2026" (Thread 2)   │
└─────────────────────────────────────────────────┘
```

**Backend flow:**
1. Claude Opus generates research prompt from intent_summary
2. Research prompt split into 3-5 threads
3. Each thread fires as a parallel Vercel Function
4. Each function: WebSearch → WebFetch top results → Claude synthesizes findings
5. Results stream to frontend via SSE
6. Auto-advances to Step 3 when all threads complete

**User can:** Watch progress, click into threads, add a thread, or cancel and refine.

### Step 3: Review & Build (Phases H + I)

Two sub-stages:

**3a: Synthesis Review** — Claude combines research into editable sections:

- Key Findings, Best Practices, Common Pitfalls
- Each section has: Approve / Edit / Remove actions
- UNVERIFIED items highlighted for human input
- This is the human-in-the-loop step that makes skills high quality

**3b: Skill Preview** — Claude generates the skill, shown as file tree + content:

```
┌──────────────┬──────────────────────────────────────┐
│ Files        │  SKILL.md                            │
│              │                                       │
│ v my-skill/  │  ---                                 │
│   SKILL.md   │  name: k8s-debugging                 │
│   v refs/    │  description: Kubernetes debugging... │
│     core.md  │  ---                                  │
│     tips.md  │                                       │
│     anti.md  │  # Kubernetes Debugging Guide         │
│              │  ...                                  │
│ [Regenerate] │                        [Edit in-app]  │
└──────────────┴──────────────────────────────────────┘
```

User can review files, edit inline, or ask Claude to regenerate specific sections.

### Step 4: Export (Phase J)

Publishing and download:

- **Free tier:** "Public" is pre-selected and locked
- **Pro/BYOK:** Can choose private
- **Downloads:** .zip, .skill package, or copy-paste CLI install command
- **Tags:** Auto-suggested by Claude, editable by user
- **Save as Draft:** Resume later without publishing

---

## 4. The Gallery

Auto-populated by free-tier forge sessions.

**Features at launch:**
- Search + tag filtering (full-text on name, description, tags)
- Skill cards: name, description, author, download count, rating
- Skill detail page: full preview, install instructions, download, rating
- Ratings: 1-5 stars, one per user per skill
- Author profiles: username, avatar, published skills (from Supabase auth)

**Deferred:**
- Comments/discussions
- Forking/remixing
- Version history
- Curated collections

---

## 5. Auth Flow

Two providers via Supabase Auth:

- **GitHub OAuth** (primary) — natural for developers, provides avatar + username
- **Email magic link** (fallback) — no password management
- **Anonymous browsing** — gallery is fully public, no login to browse or download
- **Login required for:** creating skills, rating skills, accessing dashboard

---

## 6. Data Model

```sql
-- Users
users
  id              uuid (PK, from Supabase Auth)
  username        text (unique)
  avatar_url      text
  tier            enum('free', 'pro', 'byok')
  anthropic_key   text (encrypted, nullable)
  usage_this_month int (default 0)
  created_at      timestamp

-- Skills
skills
  id              uuid (PK)
  author_id       uuid (FK -> users)
  name            text
  slug            text (unique)
  description     text
  is_public       boolean (default true)
  status          enum('draft', 'published', 'archived')
  tags            text[]
  download_count  int (default 0)
  avg_rating      decimal
  rating_count    int (default 0)
  created_at      timestamp
  updated_at      timestamp

-- Skill Files
skill_files
  id              uuid (PK)
  skill_id        uuid (FK -> skills)
  file_path       text (e.g. "SKILL.md", "references/core.md")
  content         text
  created_at      timestamp

-- Ratings
ratings
  id              uuid (PK)
  skill_id        uuid (FK -> skills)
  user_id         uuid (FK -> users)
  score           int (1-5)
  created_at      timestamp
  UNIQUE(skill_id, user_id)

-- Forge Sessions
forge_sessions
  id              uuid (PK)
  user_id         uuid (FK -> users)
  skill_id        uuid (FK -> skills, nullable)
  status          enum('interviewing', 'researching', 'reviewing', 'complete', 'abandoned')
  intent_summary  jsonb
  research_brief  jsonb
  synthesis       jsonb
  chat_history    jsonb
  created_at      timestamp
  updated_at      timestamp
```

### Access Control (RLS)

```
Gallery browse:    skill.is_public = true         -> anyone
Create skill:      authenticated                  -> any logged-in user
Publish public:    any tier                       -> allowed
Publish private:   user.tier in ('pro', 'byok')   -> paid only
Rate skill:        authenticated                  -> any logged-in user
BYOK key access:   user.tier = 'byok'            -> encrypted, never exposed
```

### Usage Tracking

Increment `usage_this_month` on each forge session start. Reset monthly via Supabase cron. Free tier cap checked before starting a new session.

### Payments (Post-MVP)

The `tier` field on users is the only hook needed. When Stripe is added later:
- Stripe Checkout + Customer Portal handles subscriptions
- Webhooks -> Supabase: `checkout.session.completed` and `customer.subscription.updated` update the `tier` field
- No refactoring needed — all access control already reads from `tier`

---

## 7. API Routes

```
/api
  /auth
    callback          GET   OAuth callback (GitHub)
    session           GET   Current user session

  /forge
    sessions          POST  Start new forge session
    sessions/[id]     GET   Resume session state
    sessions/[id]/chat POST Send message in interview (SSE stream)
    sessions/[id]/confirm-intent  POST  Lock intent, trigger research
    sessions/[id]/research        GET   SSE stream of research progress
    sessions/[id]/research/thread POST  Add a custom research thread
    sessions/[id]/synthesis       GET   Get synthesis result
    sessions/[id]/synthesis       PATCH Edit synthesis sections
    sessions/[id]/build           POST  Generate skill from synthesis
    sessions/[id]/build           PATCH Regenerate a specific section

  /skills
    /                 POST  Publish skill (from forge session)
    /[slug]           GET   Skill detail
    /[slug]           PATCH Update skill (author only)
    /[slug]/download  GET   Download .zip/.skill
    /[slug]/rate      POST  Rate a skill

  /gallery
    /                 GET   Browse/search (public, paginated)
    /tags             GET   Popular tags
    /featured         GET   Top rated / most downloaded

  /user
    /me               GET   Profile + tier + usage
    /me/skills        GET   My skills (public + private)
    /me/sessions      GET   My forge sessions (resume)
    /me/api-key       PUT   Store BYOK Anthropic key (encrypted)
```

### Streaming Architecture

Every user-facing Claude call streams via SSE:

```
Client                    API Route               Claude
  |                          |                       |
  |  GET /research (SSE)     |                       |
  | <========================|                       |
  |  event: thread_started   |                       |
  |  event: source_found     |  <--- thread result --|
  |  event: thread_complete  |                       |
  |  event: source_found     |  <--- thread result --|
  |  event: thread_complete  |                       |
  |  event: all_complete     |                       |
```

---

## 8. Pages

```
/                       Landing page (hero, how it works, CTA)
/forge                  Start new forge session (redirects to /forge/[id])
/forge/[id]             The 4-step wizard
/gallery                Browse public skills
/gallery/[slug]         Skill detail page
/dashboard              My skills, drafts, sessions, usage
/settings               Profile, tier, BYOK key
/login                  Auth (GitHub OAuth + email magic link)
```

8 pages total.

---

## 9. MVP Build Order

### Phase 1: Foundation (~Week 1)
- Next.js project setup + Tailwind + shadcn/ui
- Supabase project: auth, DB schema, RLS policies
- Auth flow (GitHub OAuth + email)
- Landing page (static)
- Basic layout: nav, footer, auth state

### Phase 2: The Forge (~Week 2-3)
- /forge/[id] page with step progress bar
- Step 1: Chat UI + Intent Summary panel + Claude streaming (SSE) + intent extraction via tool_use
- Step 2: Research dashboard + parallel thread execution + real-time SSE
- Step 3: Synthesis review (editable cards) + skill generation + file preview
- Step 4: Export + publish flow
- Forge session persistence (resume support)

### Phase 3: Gallery + Dashboard (~Week 4)
- /gallery: card grid, search, tag filter
- /gallery/[slug]: detail page, download, rating
- /dashboard: my skills, sessions, usage
- /settings: profile, BYOK key management

### Phase 4: Polish (~Week 5)
- Free tier usage enforcement
- Tier-based visibility (public/private)
- Error handling + edge cases
- Mobile responsiveness
- OG meta tags for skill sharing

---

## 10. Deferred (Post-MVP)

| Feature | Why defer |
|---------|-----------|
| Stripe payments | Tier field is ready, plug in later |
| Comments on skills | Social features can wait for traction |
| Skill forking/remixing | Complex, needs versioning |
| Version history | Ship v1, worry about v2 later |
| Curated collections | Need enough skills first |
| Admin dashboard | Moderate manually early on |
| Programmatic API | Focus on web UI first |
