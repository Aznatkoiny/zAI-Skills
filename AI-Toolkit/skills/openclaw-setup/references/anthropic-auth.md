# Anthropic auth, models and cost control

Checked against OpenClaw 2026.9.9 and https://docs.openclaw.ai/providers/anthropic (October 2026). Model IDs and prices change; confirm them at https://platform.claude.com/docs/en/about-claude/models/overview and https://platform.claude.com/docs/en/about-claude/pricing before quoting numbers to the user.

## Contents
- Spend cap first
- Choosing an auth route
- Setting it up
- Choosing models
- Heartbeat, caching and other cost levers
- Watching spend

## Spend cap first

Before the user creates or pastes any key, have them set a monthly spend limit in the Claude Console: platform.claude.com → Settings → Billing → Spend limits (workspaces can have their own lower limits). Limits are monthly; there's no daily cap. The reason: OpenClaw runs unattended, so a loop, a busy group chat, or a leaked key keeps billing until something stops it, and the cap is the only hard stop.

## Choosing an auth route

| Route | How it bills | When to use it |
|---|---|---|
| **Anthropic API key** (recommended) | Pay per token on the user's API account, capped by the spend limit | Default for OpenClaw. OpenClaw's own docs call it preferable for automation and predictable spend. |
| Claude CLI login or `claude setup-token` | Draws on a Claude subscription's limits | Only if the user understands the trade-offs and has checked Anthropic's current terms for using a subscription with third-party tools. Whether that's allowed is set by Anthropic and can change, and this skill can't confirm the current policy, so don't present it as the default. |

## Setting it up

**API key:** the user creates a key in the Claude Console (API Keys) and pastes it into the onboarding wizard when asked, or into a `.env` / secret store, never into this conversation. Non-interactively: `openclaw onboard --non-interactive --accept-risk --auth-choice apiKey --anthropic-api-key "$ANTHROPIC_API_KEY" …` with the key already in the environment. To add or replace credentials later: `openclaw models auth login --provider anthropic`.

**Subscription routes, if the user chooses them:** Claude CLI reuse expects Claude Code to be logged in on the same host as the Gateway (Docker needs extra setup; see the provider docs). For a setup token, the user runs `claude setup-token` themselves (it prints a long-lived `sk-ant-oat01-` token) and then `openclaw models auth login --provider anthropic --method setup-token`.

Verify with `openclaw models list --provider anthropic` and `openclaw models status`.

## Choosing models

Model refs look like `anthropic/<model-id>`. As of October 2026 the current models are Opus 5.5 (`claude-opus-5-5`), Sonnet 5.5 (`claude-sonnet-5-5`) and Haiku 5.5 (`claude-haiku-5-5`); run `openclaw models list --provider anthropic` to see what the install offers.

- **Primary:** Sonnet 5.5 is a sensible default for a personal assistant. Opus 5.5 is the stronger choice when the agent reads untrusted content (group chats, email, web pages), because Anthropic reports it resists prompt injection better than earlier models, and when it runs long multi-step tasks. Either way, injection resistance is a second line of defense behind pairing and tool limits.
- **Light work:** Haiku 5.5 is far cheaper and fine for heartbeats and simple replies. It's weaker with tools, so keep it off agents that run exec or file tools on untrusted input.

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-sonnet-5-5",
        fallbacks: ["anthropic/claude-haiku-5-5"],   // used if the primary is unavailable
      },
    },
  },
}
```

## Heartbeat, caching and other cost levers

**Heartbeat.** The Gateway wakes the agent on a schedule (default every 30 minutes; every hour when using subscription or token auth) to check for things that need attention. Each wake is a model call that carries context, so on an expensive model it adds up. Options: run it on Haiku, run it less often, limit it to waking hours, or turn it off.

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "1h",                              // "0m" turns the recurring heartbeat off
        model: "anthropic/claude-haiku-5-5",
        activeHours: { start: "08:00", end: "22:00" },
      },
    },
  },
}
```

**Prompt caching** is applied automatically for API-key auth (5-minute retention). For chats with long gaps, 1-hour retention can save money: cache reads cost a small fraction of normal input (about 5% on Opus 5.5 and Sonnet 5.5, 10% on Haiku 5.5), while 1-hour cache writes cost double.

```json5
{ agents: { defaults: { models: { "anthropic/claude-sonnet-5-5": { params: { cacheRetention: "long" } } } } } }
```

**Other levers:** keep groups mention-gated so the bot doesn't answer every message; keep `SOUL.md` and memory files short, since they're sent with every turn; and set background exec to not wake the agent on completion if the user doesn't need that (`tools.exec.notifyOnExit: false`).

## Watching spend

- Control UI → **Usage**, or `openclaw gateway usage-cost`, for OpenClaw's estimate.
- For actual billed cost, the Claude Console's usage page, or an Admin API key in OpenClaw (`ANTHROPIC_ADMIN_KEY`) to show provider-reported cost in Control UI.
- Check after the first day of real use and again after a week, before the spend limit becomes the thing that tells you.

If costs jump, look at heartbeat frequency and model, group-chat volume, cron jobs, and background exec notifications first.
