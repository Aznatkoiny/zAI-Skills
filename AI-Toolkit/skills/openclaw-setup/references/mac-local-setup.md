# OpenClaw on a Mac (always-on Mac mini or a daily-use Mac)

Checked against OpenClaw 2026.9.9 (October 2026). Details: https://docs.openclaw.ai/platforms/macos and https://docs.openclaw.ai/gateway.

## Contents
- Before installing
- Install and onboard
- Running 24/7
- Remote access
- Web search
- Updating and files

## Before installing

- **Hardware:** any Apple-silicon Mac works when models run in the cloud; the Gateway itself is light. A dedicated Mac mini that stays on is the usual choice for an always-available assistant. Running local models is a separate project and needs much more memory.
- **macOS:** the OpenClaw.app menu-bar app needs macOS 15 (Sequoia) or later; the CLI runs on older versions.
- **Have ready:** the Anthropic spend limit already set and an API key (`anthropic-auth.md`), and a Telegram bot token if using Telegram (`telegram-channel.md`). The user keeps these in their password manager and pastes them into the wizard; they don't go into the chat.
- **Consider a separate macOS user** for the assistant on a shared Mac, so the agent's file tools can't see the owner's personal files and accounts. The iMessage deployment guide covers this pattern.

## Install and onboard

Two equivalent starts; let the user pick:

- **App:** download the `OpenClaw-<version>.dmg` from https://github.com/openclaw/openclaw/releases, install, launch, and follow first-run setup (it can start a local Gateway).
- **CLI:** `curl -fsSL https://openclaw.ai/install.sh | bash`. It installs a supported Node (26 on macOS) if needed, installs OpenClaw, and launches onboarding. Ask before running it, since it installs software.

During onboarding (`openclaw onboard --install-daemon` if it didn't start on its own), recommend: Anthropic with an API key, `local` mode, loopback bind, token auth, pairing for DMs, and only bundled skills. Explain each step briefly; non-technical users need the "why", developers need less.

Then check:

```bash
openclaw --version          # compare with: npm view openclaw dist-tags
openclaw doctor
openclaw status --all
openclaw security audit --deep
```

## Running 24/7

`--install-daemon` installs a LaunchAgent (label `ai.openclaw.gateway`) that starts the Gateway at login and restarts it if it crashes. Manage it through OpenClaw rather than raw `launchctl`:

```bash
openclaw gateway status
openclaw gateway restart        # not stop + start
openclaw gateway stop --disable # stop and keep it from respawning across reboots
```

So the Mac doesn't sleep: System Settings → Energy → turn on "Prevent automatic sleeping when the display is off" and "Start up automatically after a power failure". For a headless Mac mini, an HDMI dummy plug avoids display-related issues with screen sharing. A terminal alternative is `sudo pmset -a sleep 0 disksleep 0` (ask first; it changes system settings).

## Remote access

The Gateway stays on loopback. To reach the Control UI from elsewhere:

- **SSH tunnel:** `ssh -N -L 18789:127.0.0.1:18789 user@mac`, then open `http://127.0.0.1:18789/`.
- **Tailscale Serve (tailnet only):** set `gateway.tailscale.mode: "serve"` (or run `openclaw gateway --tailscale serve`); the Gateway stays on `127.0.0.1` and Tailscale publishes it to the user's tailnet only. Don't use Funnel, which makes it public.

## Web search

`openclaw configure --section web` sets up a search provider (Brave, Tavily and others; each needs its own API key, entered in that flow). Pricing and free tiers change, so check the provider's page rather than quoting numbers.

## Updating and files

- Update with `openclaw update` (`openclaw update status` shows what's available), then `openclaw doctor`.
- Config: `~/.openclaw/openclaw.json`. Workspace (`SOUL.md`, memory, workspace skills): `~/.openclaw/workspace/`. Channel credentials and pairing allowlists: `~/.openclaw/credentials/`. Logs: `openclaw logs --follow`.
- Back up with `openclaw backup` or by copying `~/.openclaw/` while the Gateway is stopped.
- Keep `~/.openclaw` readable only by the user (`chmod 700 ~/.openclaw`); `openclaw security audit` checks this.
