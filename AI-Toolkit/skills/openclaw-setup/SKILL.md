---
name: openclaw-setup
description: Install, configure, secure and troubleshoot OpenClaw (formerly Clawdbot / Moltbot), the self-hosted personal AI assistant that answers through messaging apps. Covers installing on a Mac or Linux machine or a VPS with Docker (including Hostinger), Anthropic API setup and cost control, Telegram and iMessage channels, and hardening (gateway binding, pairing, tool limits). Use when the user mentions OpenClaw, Clawdbot or Moltbot, `openclaw onboard`, `openclaw doctor`, or setting up, fixing or hardening their OpenClaw gateway. Not for building an assistant from scratch with an SDK, generic VPS or SSH hardening unrelated to OpenClaw, or writing OpenClaw plugins. For a read-only security check of an existing install, /openclaw-audit runs the checklist.
---

# OpenClaw setup

OpenClaw runs a **Gateway** on the user's own machine or server. The Gateway connects a model provider (here, Anthropic) to messaging channels such as Telegram and iMessage, so the user can talk to an agent that can run tools on that machine. That last part is why setup is mostly about safety: anyone who can message the bot, or reach the Gateway port, can try to make it act. Your job is a working install that only its owner controls and whose spending is capped.

- Docs: https://docs.openclaw.ai (source of truth for commands and config keys)
- Source: https://github.com/openclaw/openclaw

## Working with the user

A person is present during setup, so explain choices in plain language and let them decide. Read-only checks (`openclaw --version`, `openclaw doctor`, `openclaw status`, `ss -tlnp`) can run freely. Before each of the following, say in one line what will change and get a yes:

- running the installer (`curl … | bash`), `sudo`, or package installs;
- editing `~/.openclaw/openclaw.json` (back it up first: `cp openclaw.json openclaw.json.bak`);
- firewall, SSH, or Docker changes on a server, and stopping or restarting the Gateway;
- installing third-party plugins or skills.

**Secrets stay out of the chat.** API keys, bot tokens and the gateway token go straight into the onboarding wizard, an editor, or a `.env` file with `chmod 600`, typed by the user. Refer to them as `${ANTHROPIC_API_KEY}` and so on. Check that a secret is set by its presence or length, never by printing it, and don't run commands that echo one (such as `printenv TOKEN`); if the user needs to see a token, they run that command themselves.

## Match the work to the request

- **Fresh install:** the full path below.
- **Adding a channel or changing a setting on a working install:** go straight to the relevant reference; check the version and run `openclaw doctor` afterwards. Don't walk them back through installation.
- **Something's broken:** start with `openclaw doctor`, `openclaw status --all`, `openclaw channels status --probe` and `openclaw logs --follow`, then use the troubleshooting table.
- **"Is my install safe?":** suggest `/openclaw-audit`, which runs the checklist read-only.

## Safety essentials (and why)

1. **Cap spending before any key exists.** In the Claude Console (platform.claude.com → Settings → Billing → Spend limits) set a monthly limit. A runaway loop or chatty heartbeat bills by the token, and a cap is the only hard stop.
2. **Run a current release.** OpenClaw ships security fixes often (hundreds of advisories in 2026 alone, several critical). "Current" means the latest stable or extended-stable release: compare `openclaw --version` with `npm view openclaw dist-tags`, and update with `openclaw update`. A version that was safe in January isn't safe now.
3. **Keep the Gateway private.** Native installs bind to loopback (`gateway.bind: "loopback"`) and use token auth. Reach it remotely through an SSH tunnel or Tailscale Serve, not an open port. With Docker, the container must listen on its network interface, so the protection is publishing ports only on `127.0.0.1` on the host (see `references/vps-setup.md`); a host firewall like UFW doesn't filter Docker-published ports.
4. **Only the owner talks to it.** DMs use `dmPolicy: "pairing"` (or an allowlist), groups require a mention, and DM sessions stay separate (`session.dmScope: "per-channel-peer"`).
5. **Limit what the agent can do.** Start from OpenClaw's hardened baseline (`references/security-defaults.md`): messaging tool profile, exec denied or approval-gated, file tools limited to the workspace, elevated tools off. Then widen deliberately. Instructions written into `SOUL.md` are guidance to the model, not enforcement; real limits come from tool policy and sandboxing.

## Fresh install

1. **Spend cap**, as above.
2. **Choose where it runs:**

   | Option | Good for | Reference |
   |---|---|---|
   | Mac (CLI or the OpenClaw.app menu-bar app, macOS 15+) | Personal use, always-on Mac mini, needed for iMessage | `references/mac-local-setup.md` |
   | Linux VPS with Docker | 24/7 availability, Telegram; requires active hardening | `references/vps-setup.md` |
   | Hostinger managed OpenClaw | Least admin work; Hostinger controls the host | `references/vps-setup.md` → Hostinger |

3. **Install:** `curl -fsSL https://openclaw.ai/install.sh | bash` (macOS, Linux, WSL2). It installs Node if needed (OpenClaw needs Node 24.16+ or 26.1+) and starts onboarding. Docker installs use the repo's `scripts/docker/setup.sh` instead.
4. **Onboard:** `openclaw onboard --install-daemon`. Explain each wizard step and recommend the safe choice: Anthropic with an API key (`references/anthropic-auth.md`), loopback bind, token auth, pairing for DMs, and bundled skills only.
5. **Connect channels:** `references/telegram-channel.md`, `references/imessage-channel.md` (Mac only).
6. **Apply the hardened baseline** and check: `openclaw security audit --deep`, `openclaw doctor`, `openclaw channels status --probe`. On a server, also `ss -tlnp` to confirm nothing listens on `0.0.0.0` that shouldn't.
7. **Test:** send the bot a DM, approve the pairing code (`openclaw pairing approve telegram <code>`), and confirm it answers.

For scripted installs, `openclaw onboard --non-interactive` requires `--accept-risk`; see https://docs.openclaw.ai/start/wizard-cli-automation.

## Editing config

`~/.openclaw/openclaw.json` is JSON5 and **validated strictly**: an unknown or misplaced key stops the Gateway from starting. So don't write keys from memory or from older guides. Take them from `openclaw config schema`, the docs, or the snippets in these references (checked against 2026.9.9), back up first, check with `openclaw config validate`, and run `openclaw doctor` after every change (`openclaw doctor --fix` migrates some older formats). Two keys that moved in 2026: the model is `agents.defaults.model.primary` (not `agent.model`), and the heartbeat lives under `agents.defaults.heartbeat`.

A minimal safe starting point:

```json5
{
  agents: { defaults: { model: { primary: "anthropic/claude-sonnet-5-5" } } },
  gateway: { mode: "local", bind: "loopback", auth: { mode: "token" } }, // keep the token onboarding generated
  session: { dmScope: "per-channel-peer" },
  channels: {
    telegram: { enabled: true, dmPolicy: "pairing", groups: { "*": { requireMention: true } } },
  },
}
```

## Troubleshooting

| Symptom | First thing to try |
|---|---|
| Gateway won't start after a config edit | `openclaw doctor`; the error names the bad key. Restore the backup or fix the key from `openclaw config schema` |
| `node` too old | The installer provisions a supported Node; otherwise install Node 24 LTS or 26 |
| Gateway reachable from the internet | Native: set `gateway.bind: "loopback"`. Docker: publish ports as `127.0.0.1:PORT:PORT`; see `vps-setup.md` |
| Telegram bot silent | `openclaw channels status --probe`; check the token, then pairing (`openclaw pairing list telegram`) |
| Pairing code rejected | Codes expire after an hour and at most 3 can be pending; send a new DM for a fresh code |
| iMessage not working | `imsg chats --limit 1` in the Gateway's context, then the permission checklist in `imessage-channel.md` |
| Costs higher than expected | Control UI → Usage, or `openclaw gateway usage-cost`; see `anthropic-auth.md` for heartbeat and model choices |
| Audit warnings | Read them with the user, then `openclaw security audit --fix` for the auto-fixable ones (with their OK) |

## Reference files

| File | Covers |
|---|---|
| `references/mac-local-setup.md` | Mac install, keep-awake, LaunchAgent, remote access |
| `references/vps-setup.md` | Linux VPS with Docker (any provider), safe SSH order, port publishing, Hostinger notes |
| `references/anthropic-auth.md` | API key vs Claude subscription login, model choice, heartbeat and cost control |
| `references/telegram-channel.md` | BotFather, pairing, groups, privacy mode |
| `references/imessage-channel.md` | `@openclaw/imessage` + `imsg`, macOS permissions |
| `references/security-defaults.md` | Hardened baseline, tool limits, skills and plugins, incident response |

These notes were checked against OpenClaw 2026.9.9 (October 2026). OpenClaw changes monthly; when a command or key here disagrees with the installed version, trust `openclaw --help`, `openclaw config schema` and docs.openclaw.ai.
