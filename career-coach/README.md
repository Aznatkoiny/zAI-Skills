# career-coach

For job seekers who want help with the whole search: turning an existing resume into a reusable career profile, finding and ranking openings, tailoring resumes and cover letters, practicing interviews, and comparing offers. Everything works from one file, `career-profile.json`, which the plugin builds with you.

## Install

```
/plugin marketplace add Aznatkoiny/zAI-Skills
/plugin install career-coach@zAI-Skills
```

Restart Claude Code after installing. Start Claude in a dedicated folder for your job search: the plugin keeps its files (profile, tracker, resumes) in the folder you're working in.

## Try it

1. **Set up your profile from your resume.** Paste your resume (or LinkedIn experience text) and say "set up my career profile from this". Claude builds `career-profile.json` and then asks only about what's missing, mostly the numbers behind your achievements and the roles you're targeting.
2. **Find jobs:** `/job-hunt staff platform engineer, remote`. You get a ranked report scored against your skills, plus entries in an application tracker.
3. **Tailor a resume:** `/resume-generator https://jobs.example.com/posting --template jakes-resume`.

You don't have to start with step 1: `/job-hunt`, `/cover-letter` and `/ats-check` can run from a role or a pasted resume and will offer to build the profile along the way.

## What it needs

| | |
|---|---|
| **Required** | Node.js 18+ (runs the bundled job-data server) and Python 3 (hooks and scripts). |
| Optional: PDF output | A LaTeX install with XeLaTeX (macOS: `brew install --cask mactex-no-gui`; Ubuntu/Debian: `sudo apt install texlive-xetex texlive-fonts-extra`). Pandoc for Markdown-to-PDF. Without these you still get `.md`/`.tex` files, and Claude tells you no PDF was built. |
| Optional: location-aware job search | Free API keys for Adzuna (US jobs; https://developer.adzuna.com/signup, free tier 250 requests/day) and USAJOBS (US federal jobs; https://developer.usajobs.gov/apirequest/). Without them, search uses Remotive and RemoteOK, which list **remote jobs only** and ignore location, plus company job boards. |
| Optional: scraped sources | Glassdoor (company ratings, interview reports), Indeed and TrueUp are off by default because these sites restrict automated access. You can opt in with `JOB_INTEL_ENABLE_SCRAPERS=1` after checking their terms; expect them to be blocked often. |

Set keys in your shell profile (for example `export ADZUNA_APP_ID=...`) or under `env` in `~/.claude/settings.json`, then restart Claude Code:

| Variable | Purpose |
|---|---|
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Adzuna job search |
| `USAJOBS_API_KEY`, `USAJOBS_EMAIL` | USAJOBS search (the email must be the one you registered with) |
| `JOB_INTEL_ENABLE_SCRAPERS` | `1` to enable the Glassdoor, Indeed and TrueUp scrapers |

## Commands

| Command | Does |
|---|---|
| `/job-hunt [role, location]` | Searches, reads the top listings, scores them against your skills, adds Levels.fyi compensation, writes `job-search-results.md`, and seeds `applications.json`. |
| `/resume-generator [posting or company/role] [--template <name>] [--output-dir <dir>]` | A resume from your profile, optionally tailored, as Markdown or one of six LaTeX templates, with a PDF when LaTeX is installed. Lists any bullets that need a number from you. |
| `/cover-letter [posting or company/role]` | A 250-400 word letter tied to your real achievements; leaves a marked placeholder where only you can supply the reason you want the job. |
| `/ats-check [posting] [resume file]` | Keyword coverage of your resume against a posting, with a truthful rewrite for each gap. |
| `/mock-interview [company/role] [type]` | Live practice, one question at a time, with feedback and a saved scorecard. |
| `/compare-offers [details]` | 4-year totals with stated assumptions, cost-of-living adjustment, market benchmarks and negotiation talking points. |
| `/follow-ups [company]` | Flags stale applications and drafts follow-up emails (you send them). Can create the tracker from a list you paste. |
| `/validate-profile [path]` | Checks your profile and turns the findings into fixes. |

## Skill and agents

- **resume-updater** (skill): builds and maintains `career-profile.json`, by import or interview. Triggers on "set up my career profile", "I started a new job", "add my promotion", and similar.
- **career-director** (agent): career strategy, such as switching fields, gap analysis for a target level, or management versus IC. Returns a recommendation and a plan.
- **job-search** (agent): searches, compensation lookups, and tracker updates ("update my Stripe application, I got a phone screen").
- **interview-prep** (agent): a prep pack for a specific interview, covering company process, focus areas and STAR stories from your real achievements. Live practice runs through `/mock-interview`.

Agents use whatever model your session runs.

## Job-data server

The bundled `job-intelligence` MCP server has five tools:

| Tool | Returns | Sources |
|---|---|---|
| `job_search_jobs` | Listings with location, posted salary and URL | Remotive, RemoteOK (remote only); Adzuna, USAJOBS (with keys); company Greenhouse/Lever boards; Indeed, TrueUp (opt-in) |
| `job_get_salary_data` | Median total compensation per level, or role-wide percentiles (US) | Levels.fyi; Glassdoor base pay (opt-in) |
| `job_get_company_info` | A company's open roles from its own job board | Greenhouse/Lever; Glassdoor ratings (opt-in) |
| `job_get_interview_experiences` | Reported interview questions and process | Glassdoor (opt-in only) |
| `job_search_trending_roles` | Roles with growing demand | TrueUp (opt-in only) |

Every response ends with a Sources footer (live, cached, skipped or failed). Results are cached for 6-24 hours. The server ships prebuilt (`mcp-servers/job-intelligence/dist/index.cjs`); to rebuild after changing its source: `cd mcp-servers/job-intelligence && npm ci && npm run build`.

## Industry styles

Resume format, tone, keywords and interview weighting follow an industry style: `software-engineering`, `ai-ml`, `sales` or `consulting` (stored as `preferences.industry_style`). To add your own, put `<name>.md` in an `industry-styles/` folder in your job-search folder (copy a bundled one from `skills/resume-updater/references/industry-styles/` as a starting point) and set `preferences.industry_style` to `<name>`. Don't edit files inside the installed plugin; updates replace them.

## Hooks

- **PDF build:** when a `.md` or `.tex` file under `resumes/` is saved in a career-coach folder, a PDF is built next to it, and Claude is told whether it worked.
- **Profile check:** saving `career-profile.json` runs `scripts/validate-profile.py` and gives Claude the findings as a to-do list.

## License

MIT
