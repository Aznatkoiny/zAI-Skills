# Software Engineering — Industry Style Reference

Formatting instructions for resumes, cover letters, and career documents targeting software
engineering roles: SWE, SRE, DevOps, Platform Engineering, and similar technical IC positions.
Read this file when `preferences.industry_style` in career-profile.json is `software-engineering`.
Follow these rules exactly; do not substitute generic resume conventions.

## Section Order

Use this order, top to bottom:

1. **Header** — name, email, phone, location, GitHub, LinkedIn, portfolio/blog if active
2. **Technical Skills** — first, because engineering screeners and ATS filters keyword-match
   the stack before reading anything else; a recruiter decides in seconds whether the stack fits
3. **Experience** — reverse chronological, the core of the document
4. **Projects** — open source, side projects, and system design work; this section differentiates
   candidates with similar employment history and shows initiative beyond the job description
5. **Education** — last, because after the first job, degrees matter far less than shipped work

Rationale: technical hiring optimizes for "can this person build what we need." Skills answer
the filter question, experience proves it at scale, projects prove intrinsic motivation.

## Technical Skills Format

Group into labeled rows, most job-relevant group first:

- **Languages**: e.g., Python, Go, TypeScript, Rust, Java
- **Frameworks**: e.g., React, Django, FastAPI, gRPC, Spring
- **Infrastructure**: e.g., AWS, Kubernetes, Terraform, Docker, CI/CD (GitHub Actions, ArgoCD)
- **Databases**: e.g., PostgreSQL, Redis, DynamoDB, Kafka (streaming counts here)
- **Tools**: e.g., Datadog, Prometheus, Grafana, Bazel

Never write a flat comma-soup of 30 technologies. List only what the candidate can defend in a
technical interview. When tailoring to a job description, reorder groups and items so required
skills appear earliest.

## Bullet Writing Rules

- Every achievement bullet needs a quantified metric. Use the numbers the profile actually has; if a strong bullet has none, write it without one and list it for the user to supply a figure. Never estimate one. Prefer these metric families:
  - **Scale**: requests/sec (RPS), daily active users (DAU), data volume (TB/PB), QPS, node count
  - **Performance**: latency (p50/p95/p99), throughput, load time
  - **Reliability**: uptime (99.9x%), error rate reduction, MTTR, incident count
  - **Efficiency**: deployment frequency, build time, test coverage, infra cost reduction
- Structure: strong verb → what was built/changed → measured outcome → method or technology.
- Name the specific technologies in the bullet when they carry signal (caching layer → Redis).
- Show ownership scope: "designed", "led migration of", "owned" beat "contributed to".
- 3-5 bullets per role; the first bullet of each role should be its biggest-scale achievement.

## Example Bullets

Use these as the voice and density target — every bullet carries a number:

1. Reduced p99 API latency from 850ms to 120ms by introducing a Redis read-through cache and
   query batching across the 3 highest-traffic endpoints, serving 40M requests/day.
2. Designed and led migration of a monolith to 14 microservices on Kubernetes, cutting deploy
   time from 45 minutes to 6 and raising deployment frequency from weekly to 12x/day.
3. Built a Kafka-based event pipeline ingesting 2TB/day of clickstream data with exactly-once
   semantics, replacing a batch job and reducing data freshness lag from 24h to 90 seconds.
4. Improved service availability from 99.5% to 99.95% by adding circuit breakers, automated
   failover, and SLO-based alerting in Prometheus, cutting pages per on-call week from 11 to 2.
5. Cut AWS spend by $38K/month (31%) by right-sizing EC2 fleets, moving batch workloads to spot
   instances, and adding S3 lifecycle policies — with zero customer-facing regressions.
6. Owned authentication platform used by 9 internal teams; drove OAuth2/OIDC migration for
   6M user accounts with zero downtime and a 4-week deprecation runway for legacy tokens.
7. Raised backend test coverage from 41% to 87% and introduced contract tests in CI, cutting
   production rollbacks from 6/quarter to 1/quarter.
8. Scaled Postgres from 5K to 60K QPS through partitioning, connection pooling (PgBouncer),
   and index tuning, deferring a $250K sharding project by 18 months.
9. Led a 4-engineer team delivering a real-time notification service (WebSockets + Redis
   pub/sub) to 2.5M DAU, sustaining 150K concurrent connections per node.
10. Open-sourced an internal Terraform module library (1.2K GitHub stars); adopted by 30+
    external companies and reduced internal environment spin-up from 2 days to 20 minutes.
11. Automated blue/green deployments with ArgoCD and feature flags, cutting release-related
    incidents by 70% year over year across 40 services.

## ATS Keyword Bank

Weave these naturally into skills and bullets when truthful (match the job description first):

- **Systems**: distributed systems, microservices, event-driven architecture, API design,
  RESTful APIs, gRPC, message queues, caching, horizontal scaling, scalability, high availability
- **Infra/DevOps**: cloud infrastructure, AWS, GCP, Azure, Kubernetes, Docker, CI/CD,
  infrastructure as code, Terraform, observability, monitoring, incident response, SRE, on-call
- **Data**: database optimization, SQL, NoSQL, data pipelines, streaming, Kafka
- **Practice**: agile, code review, unit testing, integration testing, TDD, performance
  optimization, security best practices, system design, technical leadership, mentorship

## Tone and Formatting Rules

- Direct and concrete. No adjectives that a metric could replace ("blazing fast" → "p95 90ms").
- Past tense for previous roles, present tense for the current role.
- No first person, no pronouns, no objective statement. Summary is optional and max 2 lines.
- One page up to ~8 years of experience; two pages only for staff+ with broad scope.
- Acronyms recruiters know stay as acronyms (API, CI/CD, SLA); niche ones get expanded once.
- Link GitHub prominently if it has real activity; omit it if it is empty.

## Career Ladder Framing

Frame advice and seniority against standard engineering levels: L3/Junior → L4/Mid → L5/Senior
→ L6/Staff → L7/Principal → L8/Distinguished-Fellow. Growth signals that matter: scope (component
→ system → org), complexity handled, cross-team influence, and technical depth vs. breadth
trade-offs. For senior+ candidates, emphasize design ownership and mentorship over raw output.

## Interview Weighting

Allocate prep time roughly:

- **System design: 60%** — the primary differentiator at mid-level and above; practice
  whiteboard-format architecture discussions with explicit trade-off narration
- **Coding / data structures & algorithms: 25%** — timed practice, think-aloud format
- **Behavioral: 15%** — STAR stories emphasizing technical leadership, incident response,
  and cross-team conflict; keep them metric-backed like resume bullets

Cover letters for engineering roles: short (250-350 words), technical, project-focused —
reference the company's stack or engineering blog and mirror the scale metrics above.
