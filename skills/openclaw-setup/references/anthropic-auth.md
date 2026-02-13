# Anthropic Model Authentication & Cost Control

Configure Anthropic as the primary model provider for OpenClaw. This guide covers auth setup, model selection, smart routing to control costs, and spending safeguards.

## ⚠️ STEP ZERO: Set Spending Limits

**Do this BEFORE pasting any API key into OpenClaw.**

1. Go to **console.anthropic.com** → Settings → Limits
2. Set a **monthly spending cap** — $30-50/month is achievable with optimized routing
3. Set per-day limits if available

Why this matters: A single misconfigured heartbeat or cron job can cost $750/month. One user's leaked API key was exploited for 11 days before discovery. Unoptimized setups regularly hit $1,500+/month. Spending limits are your safety net.

## Auth Methods

### Option 1: Anthropic API Key (recommended for simplicity)

Direct pay-per-token. Most straightforward setup.

1. Go to console.anthropic.com → API Keys → Create key
2. Key format: `sk-ant-...`
3. During onboarding wizard, select **"Anthropic API key"** and paste the key
4. Or set via environment variable:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```

**Cost model:** Pay per token. No subscription required. Costs scale with usage — which is why spending limits are critical.

### Option 2: Claude Pro/Max Subscription via Setup Token

Uses your Claude Pro ($20/mo) or Max ($100-200/mo) subscription credits instead of direct API billing. Natural spending ceiling — you can't exceed your subscription tier.

1. Install Claude Code CLI if not already installed
2. Generate a setup token:
   ```bash
   claude setup-token
   ```
3. During onboarding, select **"Anthropic setup-token"** and paste the token:
   ```bash
   openclaw onboard --auth-choice setup-token
   ```
   Or configure after onboarding:
   ```bash
   openclaw models auth setup-token --provider anthropic
   ```

**Trade-off:** Subscription auth does NOT honor prompt cache settings. You get rate-limited usage with a natural spending ceiling, but miss the 90% cache discount on repeated system prompts.

### Option 3: Anthropic OAuth via Claude Code CLI

Browser-based OAuth flow. Works well for local Mac setups.

1. During onboarding, select **"Anthropic OAuth via Claude Code CLI"**
2. Browser opens for authorization
3. Approve and return to terminal

**For headless VPS:** The browser won't open. Copy the redirect URL from the terminal output and complete auth on your local machine, then paste the callback URL back.

## Recommended Model Configuration

### Primary Model

```json5
{
  agent: {
    model: "anthropic/claude-opus-4-5"
  }
}
```

**Claude Opus 4.5** is recommended as the primary model for:
- Strongest prompt-injection resistance
- Best reasoning and complex task handling
- Most capable tool use
- Longest effective context utilization

### Model Selection by Use Case

| Model | Best For | Input Cost | When to Use |
|-------|----------|------------|-------------|
| **Opus 4.5** | Critical decisions, complex reasoning, security-sensitive tasks | ~$15/1M tokens | Default for important work |
| **Sonnet 4.5** | Writing, research, code generation, daily tasks | ~$3/1M tokens | Good balance of cost/capability |
| **Haiku 4.5** | Simple commands, routine tasks, heartbeat | ~$0.25/1M tokens | 75% of typical interactions |

⚠️ **Avoid Haiku for security-sensitive or tool-enabled agents** — smaller models are more susceptible to prompt injection.

## Smart Model Routing (Cost Optimization)

The proven pattern that brings costs from $1,500+/month down to $30-50/month:

| Tier | Model | % of Work | Use Case |
|------|-------|-----------|----------|
| Default | **Haiku** | ~75% | Simple commands, routine tasks, quick answers |
| Elevated | **Sonnet** | ~10% | Writing, research, code generation |
| Critical | **Opus** | ~5% | Architecture decisions, security analysis, complex debugging |
| Free | **Ollama/local** | ~10% | Heartbeat, health checks |

Add routing guidance to your SOUL.md:
```markdown
## Model Usage Rules
Default: Always use Haiku for routine tasks.
Switch to Sonnet ONLY when: writing content, research, code generation, detailed analysis.
Switch to Opus ONLY when: architecture decisions, production code review, security analysis, complex debugging, critical reasoning.
```

Or use OpenRouter's auto model (`openrouter/openrouter/auto`) which automatically selects cost-effective models per prompt.

### Model Switch Command

```bash
/model claude-haiku-4-5     # Switch to Haiku
/model claude-sonnet-4-5    # Switch to Sonnet
/model claude-opus-4-5      # Switch to Opus
```

## Heartbeat Cost Warning

The heartbeat feature runs periodic agent turns in the main session. Default interval: 30 minutes (1 hour for subscription auth).

**Cost reality:**
- Opus heartbeat at 30-min intervals: **~$54/month** ($5-30/day)
- Haiku heartbeat at 1-hour intervals: **~$0.30/month**

Recommendation: Either disable heartbeat entirely, or switch to Haiku:

```json5
{
  heartbeat: {
    model: "anthropic/claude-haiku-4-5",
    interval: 3600,  // 1 hour in seconds
    activeHours: { start: "08:00", end: "24:00" }
  }
}
```

## Prompt Caching

Anthropic auto-applies a 5-minute cache (`cacheRetention: "short"`) for API key auth. The system prompt alone is 5,000-10,000 tokens resent with every call — caching gives a **90% discount** on this repeated content.

Extended 1-hour cache is available:
```json5
{
  models: {
    cacheRetention: "long"  // Requires beta flag
  }
}
```

**Note:** Subscription (setup-token) auth does NOT benefit from prompt caching.

## Model Failover

Configure fallback models so OpenClaw switches automatically if the primary is unavailable:

```json5
{
  models: {
    fallback: [
      "anthropic/claude-sonnet-4-5",
      "anthropic/claude-haiku-4-5"
    ]
  }
}
```

Priority order when multiple API keys are present: Anthropic → OpenAI → OpenRouter → Gemini.

## Auth Storage and Security

Auth profiles are stored at:
```
~/.openclaw/agents/<agentId>/agent/auth-profiles.json
```

Lock permissions:
```bash
chmod 600 ~/.openclaw/agents/*/agent/auth-profiles.json
chmod 700 ~/.openclaw/credentials/
```

**Never store API keys in:**
- SOUL.md or MEMORY.md (loaded into LLM context — could leak via prompt injection)
- Public git repositories
- Shared documents or chat messages
- Docker images (use environment variables or `.env` files with proper permissions)

## Verification

```bash
openclaw models status        # Shows configured providers and auth status
openclaw models list          # Lists available models
openclaw status --all         # Includes model info in full status
```

## Hostinger VPS Notes

For Hostinger Docker deployments, API keys are configured via:

1. **During one-click deploy:** Enter `ANTHROPIC_API_KEY` in the environment variables form
2. **After deploy:** Add to `.env` file and restart:
   ```bash
   docker compose exec openclaw-gateway bash
   echo 'ANTHROPIC_API_KEY=sk-ant-your-key' >> .env
   exit
   docker compose restart
   ```
3. **Via web UI:** Some Hostinger Docker configurations expose environment variable editing in hPanel

## Monthly Cost Targets

| Usage Level | Monthly Cost | How |
|-------------|-------------|-----|
| **Minimal** | $5-10 | Haiku default, Sonnet for writing, no heartbeat |
| **Light** | $10-30 | Haiku default, Sonnet elevated, Opus rare, Haiku heartbeat |
| **Moderate** | $30-50 | Smart routing with all three tiers, Haiku heartbeat |
| **Heavy** | $50-100 | Sonnet default, Opus for critical, active daily use |
| **Unoptimized** | $200-1,500+ | Opus for everything, frequent heartbeat — avoid this |
