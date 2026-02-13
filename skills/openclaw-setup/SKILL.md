---
name: openclaw-setup
description: Set up, install, configure, and deploy OpenClaw (formerly ClawdBot/MoltBot) — a personal AI assistant that runs on your own devices and connects to messaging channels. Use when users ask to "set up OpenClaw," "install ClawdBot," "install MoltBot," "deploy a personal AI assistant," "configure OpenClaw on Mac," "deploy OpenClaw to VPS," "set up OpenClaw on Hostinger," "connect OpenClaw to Telegram," "configure iMessage with OpenClaw," or any variation involving OpenClaw installation, gateway configuration, channel setup, Anthropic auth, or security hardening. Also triggers on "openclaw onboard," "openclaw doctor," "openclaw security audit," troubleshooting OpenClaw deployments, OpenClaw security, OpenClaw cost control, or ClawHub skills safety.
---

# OpenClaw Setup Skill

Deploy and configure OpenClaw — the open-source personal AI assistant (145k+ GitHub stars) — safely and correctly. This skill handles the full lifecycle: installation, Anthropic model auth, channel wiring (Telegram + iMessage), security hardening, cost control, and deployment to either a local Mac mini or a Hostinger VPS.

- Source: https://github.com/openclaw/openclaw
- Docs: https://docs.openclaw.ai
- Created by: Peter Steinberger (founder of PSPDFKit)

## What is OpenClaw?

OpenClaw is a self-hosted, conversation-first AI assistant built on LLMs. Originally launched as "Clawdbot" (November 2025), renamed to "Moltbot" (January 27, 2026) after Anthropic trademark concerns, then became "OpenClaw" (January 30, 2026). It runs a local Gateway (WebSocket control plane) on your machine or server and connects to messaging channels you already use — Telegram, iMessage, WhatsApp, Discord, Slack, and 50+ others. The assistant responds through those channels using models from Anthropic, OpenAI, or other providers.

Key facts:
- **Runtime:** Node.js ≥22.12.0, TypeScript, pnpm monorepo
- **Architecture:** Gateway (control plane) → Pi agent (RPC) → LLM provider
- **Recommended model:** Anthropic Claude Opus 4.5 via OAuth (Pro/Max subscription) for best prompt-injection resistance and long-context strength
- **Install method:** `curl -fsSL https://openclaw.ai/install.sh | bash` then `openclaw onboard --install-daemon`
- **Config location:** `~/.openclaw/openclaw.json` (JSON5 format)
- **Default port:** 18789 (WebSocket + HTTP multiplexed)
- **Minimum context window:** 64K tokens
- **License:** MIT

## ⚠️ CRITICAL SECURITY PREREQUISITES

Before ANY installation, these four steps are non-negotiable:

1. **Set API spending limits FIRST** — Go to console.anthropic.com → Settings → Limits → set a monthly cap ($30-50/month is achievable with smart routing). A misconfigured cron job or heartbeat can cost $750+/month. Do this BEFORE pasting any API key anywhere.

2. **Version must be 2026.1.29 or later** — CVE-2026-25253 (CVSS 8.8) affects all earlier versions. It enabled 1-click remote code execution through the Control UI. After installation, verify with `openclaw --version`.

3. **Gateway must bind to 127.0.0.1, NEVER 0.0.0.0** — Security researcher Maor Dayan found 42,665 publicly exposed OpenClaw instances via Shodan. 93.4% had critical auth bypasses. The root cause: Docker's default port publishing binds to 0.0.0.0 on VPS instances.

4. **DM policy must be "pairing" or "allowlist"** — Never use `dmPolicy: "open"` unless you fully understand the risk.

See `references/security-defaults.md` for the complete security guide.

## When to Use This Skill

Use this skill when the user wants to:
- Install OpenClaw from scratch on macOS or Linux
- Deploy OpenClaw to a Hostinger VPS using Docker
- Configure Anthropic as the model provider
- Connect Telegram or iMessage as a messaging channel
- Apply safe security defaults to a new or existing OpenClaw installation
- Run post-setup health checks (`openclaw doctor`, `openclaw security audit`)
- Troubleshoot common OpenClaw setup issues
- Understand OpenClaw costs and optimize spending

## When NOT to Use This Skill

Do not use this skill for:
- WhatsApp, Slack, Discord, Signal, or other channel setup (not covered here)
- Advanced multi-agent routing or Canvas/A2UI configuration
- iOS/Android node pairing or voice wake setup
- OpenClaw skills/plugins development
- Browser control configuration
- Ollama/local model setup

## Setup Workflow

Follow this order. Each step links to its reference file.

### Step 0: Set API Spending Limits

Before touching anything else, go to your LLM provider's console and set a monthly spending cap. See `references/anthropic-auth.md` for details.

### Step 1: Choose a Deployment Path

| Path | Best For | Reference |
|------|----------|-----------|
| **Mac mini (local)** | Personal use, always-on home server, iMessage support, safest for non-technical users | `references/mac-local-setup.md` |
| **Hostinger VPS** | 24/7 cloud availability, Telegram-focused, Docker isolation, requires active hardening | `references/hostinger-vps-setup.md` |

If the user wants iMessage, they must use the Mac path (iMessage requires macOS with Messages signed in).

### Step 2: Set Up Anthropic Auth

Configure Anthropic as the primary model provider during or after onboarding.

→ Read `references/anthropic-auth.md`

### Step 3: Connect Channels

| Channel | Platform Requirement | Reference |
|---------|---------------------|-----------|
| **Telegram** | Any (Mac or VPS) | `references/telegram-channel.md` |
| **iMessage** | macOS only | `references/imessage-channel.md` |

### Step 4: Apply Security Defaults

Harden the installation with safe defaults before going live.

→ Read `references/security-defaults.md`

### Step 5: Verify

```bash
openclaw --version              # Must be 2026.1.29+
openclaw doctor
openclaw security audit --deep
openclaw gateway status
openclaw channels status --probe
openclaw status --all
```

On VPS, verify the gateway is NOT bound to 0.0.0.0:
```bash
ss -tlnp | grep 18789
# Must show 127.0.0.1:18789, NOT 0.0.0.0:18789
```

## Interactive Setup Mode

When running commands for the user, Claude Code should:

1. **Set spending limits first** — Walk the user through setting API caps at console.anthropic.com
2. **Check prerequisites** — Verify Node.js ≥22.12.0, Xcode CLI tools (macOS), and gather credentials
3. **Run the install script** — Execute the curl installer or npm global install
4. **Verify version** — Confirm `openclaw --version` shows 2026.1.29+
5. **Launch the onboarding wizard** — Run `openclaw onboard --install-daemon` and guide the user through each interactive prompt
6. **Generate secure config** — Produce a `~/.openclaw/openclaw.json` with safe defaults
7. **Warn about skills** — During the wizard's skills step, advise installing only bundled skills. ClawHub community skills should be treated with extreme caution (Cisco found 26% contain vulnerabilities; 341 malicious skills found including macOS malware installers)
8. **Warn about heartbeat costs** — If heartbeat is enabled, recommend switching it to Haiku model or disabling it. Default Opus heartbeat costs ~$54/month.
9. **Configure channels** — Set up Telegram bot token and/or iMessage
10. **Run health checks** — Execute `openclaw doctor` and `openclaw security audit --deep`
11. **Verify binding** — On VPS, run `ss -tlnp | grep 18789` to confirm loopback binding
12. **Test connectivity** — Send a test message or open the dashboard

For each interactive prompt in the wizard, explain what the option means and recommend the safe choice. Non-technical users need plain-language explanations; developers can get the concise version.

## Non-Interactive Setup (for scripting)

```bash
openclaw onboard --non-interactive \
  --mode local --auth-choice apiKey \
  --anthropic-api-key "$ANTHROPIC_API_KEY" \
  --gateway-port 18789 --gateway-bind loopback \
  --install-daemon --daemon-runtime node --skip-skills
```

## Key Config Structure

Minimal safe config (Anthropic + Telegram + secure defaults):

```json5
{
  agent: {
    model: "anthropic/claude-opus-4-5"
  },
  gateway: {
    bind: "loopback",
    port: 18789,
    auth: { mode: "token", token: "<auto-generated>" }
  },
  channels: {
    telegram: {
      enabled: true,
      botToken: "<from-botfather>",
      dmPolicy: "pairing",
      groups: { "*": { requireMention: true } }
    }
  },
  discovery: {
    mdns: { mode: "minimal" }
  }
}
```

## Troubleshooting Quick Reference

| Issue | Fix |
|-------|-----|
| `openclaw --version` < 2026.1.29 | Update immediately: `openclaw update --channel stable` — critical RCE vulnerability |
| `node --version` < 22 | Install Node 22+ via nvm, Homebrew, or system package manager |
| Gateway won't start | Check port 18789 not in use; run `openclaw doctor --fix` |
| Gateway bound to 0.0.0.0 | Fix Docker port binding to `"127.0.0.1:18789:18789"` and restart |
| Telegram 401 Unauthorized | Regenerate bot token in BotFather; update config and restart |
| "plugin not found: telegram" | Telegram is a CHANNEL, not a plugin — config goes under `channels.telegram` |
| Pairing code not working | `openclaw pairing approve telegram <code>` — codes expire after 1 hour |
| iMessage not connecting | Verify Messages signed in; consider BlueBubbles for better reliability |
| High API costs ($100+/mo) | Set spending limits; switch heartbeat to Haiku; use tiered model routing |
| Heartbeat costing $54+/month | Switch heartbeat model to Haiku with 1-hour intervals (~$0.30/month) |
| Security audit warnings | `openclaw security audit --fix` to auto-apply safe defaults |
| WhatsApp status=515 error | Click Update in Control UI or restart gateway |
| ClawHub skill suspicious | Do NOT install. 26% contain vulnerabilities per Cisco research |

## Reference Files

| File | Content |
|------|---------|
| `references/mac-local-setup.md` | Complete Mac mini local deployment walkthrough |
| `references/hostinger-vps-setup.md` | Hostinger VPS Docker deployment guide |
| `references/anthropic-auth.md` | Anthropic auth, cost control, and smart model routing |
| `references/telegram-channel.md` | Telegram bot creation and channel configuration |
| `references/imessage-channel.md` | iMessage channel setup — BlueBubbles (recommended) + legacy |
| `references/security-defaults.md` | CVE-2026-25253, safe defaults, hardening, incident response |
