# Mac Mini Local Deployment

Complete guide for running OpenClaw as an always-on personal AI assistant on a Mac mini.

## Hardware Recommendations

- **Cloud API only (most users):** Base Mac mini M4, 16GB RAM — $549-599. AI processing happens on cloud servers; the Mini just runs the gateway.
- **Local LLM inference:** M4 Pro with 64GB unified memory — ~$2,000. Runs 32B models at 10-15 tokens/second.
- **Budget options:** Refurbished M2 Mini (~$599) or used M1 Mini (~$450) work fine for cloud API usage.
- **Running costs:** Electricity $1-5/month (M4 idles at ~3-6W), Anthropic API $5-20/month light use, $50-100/month moderate.

## Prerequisites

### Credential Checklist (gather before starting)

Before installation, assemble:
- Apple ID details (for iMessage, App Store)
- Anthropic API key (primary — from console.anthropic.com) with **spending limits already set**
- OpenAI API key (optional fallback)
- Brave Search API key (optional — 2,000 free requests/month)
- Telegram bot token (if using Telegram — see `telegram-channel.md`)
- Password manager access for all of the above

### Developer Prerequisites

```bash
# 1. Install Xcode Command Line Tools (required)
xcode-select --install

# 2. Install Homebrew (recommended)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# 3. Install Node.js 22+ via Homebrew
brew install node@22
echo 'export PATH="/opt/homebrew/opt/node@22/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 4. Verify
node --version    # Must show v22.x.x+
npm --version     # Should show 10.x.x+
```

Alternative: Use nvm if you need multiple Node versions:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
source ~/.zshrc
nvm install 22
nvm use 22
```

### System Requirements

- macOS 14 (Sonoma) or later for menu bar companion app and voice features
- Node.js 22.12.0+
- Xcode Command Line Tools
- 64K+ token context window on chosen LLM model

## Installation

### Option A: Official One-Liner (recommended)

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

The script handles Node.js detection, installs OpenClaw globally, and prompts for onboarding.

### Option B: Manual npm Install

```bash
npm install -g openclaw@latest
```

### Option C: From Source

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
pnpm install
pnpm build
```

### Verify Installation

```bash
openclaw --version    # Must show 2026.1.29+ (critical — older versions have CVE-2026-25253)
```

⚠️ If version is below 2026.1.29, update immediately: `openclaw update --channel stable`. See `security-defaults.md` for details on the vulnerability.

## Onboarding Wizard

Run the wizard with daemon installation:

```bash
openclaw onboard --install-daemon
```

### Wizard Flow (step by step)

The wizard presents each step in order. Here's what each one means and the recommended choice:

1. **Existing config check** — If `~/.openclaw/openclaw.json` already exists, choose Keep (preserve current), Modify (edit), or Reset (start fresh). Reset uses `trash`, never `rm`, so your old config is recoverable.

2. **Risk acknowledgment** — "I understand this is powerful and inherently risky" → Select **Yes** (required to proceed).

3. **Mode selection** — **QuickStart** (recommended) applies sensible defaults: loopback binding, port 18789, token auth. **Advanced** prompts for every option individually.

4. **Gateway configuration** — Choose **Local (this machine)** for Mac mini. Advanced mode additionally asks about bind address (choose **Loopback**), port (keep **18789** default).

5. **Auth/LLM provider** — Choose **Anthropic API key** (recommended) or **Anthropic OAuth via Claude Code CLI** (if you have a Pro/Max subscription). Other options: OpenAI, Google Gemini, OpenRouter, and more. See `anthropic-auth.md` for guidance.

6. **Model selection** — Pick default model. Recommended: **claude-opus-4-5** for capability and security. Wizard validates model availability against your auth.

7. **Channel setup** — Select messaging channels to enable. See `telegram-channel.md` and `imessage-channel.md`.

8. **Pairing defaults** — Choose **pairing** (recommended). Unknown senders receive a code; you approve with `openclaw pairing approve`.

9. **Skills setup** — Choose node manager (npm or pnpm). **Only install bundled skills.** Do NOT install ClawHub community skills during onboarding — Cisco research found 26% contain vulnerabilities and 341 were actively malicious (including macOS malware installers).

10. **API keys for services** — Optional: Brave Search, Exa.ai, etc. Can be added later.

11. **Hooks setup** — Optional: boot hooks, command logger, session memory. Safe to enable boot-md and session-memory. **Be cautious with heartbeat** — on Opus it costs ~$54/month. Switch to Haiku with 1-hour intervals (~$0.30/month) or skip entirely.

12. **Daemon installation** — With `--install-daemon`, registers a macOS launchd service for auto-start on login.

13. **Health check + summary** — Wizard runs validation and shows your configuration.

### Non-Interactive Mode (for scripting)

```bash
openclaw onboard --non-interactive \
  --mode local --auth-choice apiKey \
  --anthropic-api-key "$ANTHROPIC_API_KEY" \
  --gateway-port 18789 --gateway-bind loopback \
  --install-daemon --daemon-runtime node --skip-skills
```

## Post-Install Verification

```bash
openclaw --version              # Must be 2026.1.29+
openclaw gateway status         # Gateway should be running
openclaw channels status --probe # Channels should show connected
openclaw doctor                 # Health check
openclaw security audit --deep  # Security validation
openclaw status --all           # Full system overview
```

## Directory Structure

```
~/.openclaw/
├── openclaw.json          # Main config (JSON5)
├── state/                 # Session data, message history
├── workspace/             # Skills, SOUL.md, MEMORY.md, HEARTBEAT.md
│   └── skills/            # Installed skills (highest precedence)
├── credentials/           # OAuth tokens, API keys (chmod 700)
├── logs/                  # Command logs (if command-logger hook enabled)
└── skills/                # Shared skills (lower precedence than workspace)
```

## LaunchAgent (24/7 Daemon)

The `--install-daemon` flag creates a launchd plist at `~/Library/LaunchAgents/com.openclaw.gateway.plist` (some versions use `ai.openclaw.gateway.plist`). This auto-starts the gateway on login.

### Manual daemon control

```bash
# Load/start
launchctl load ~/Library/LaunchAgents/com.openclaw.gateway.plist
launchctl start com.openclaw.gateway

# Check status
launchctl list | grep openclaw

# Stop/unload
launchctl stop com.openclaw.gateway
launchctl unload ~/Library/LaunchAgents/com.openclaw.gateway.plist
```

### Other daemon commands

```bash
openclaw gateway start     # Start gateway
openclaw gateway stop      # Stop gateway
openclaw gateway restart   # Restart gateway
openclaw gateway logs --follow  # Tail live logs
```

## Always-On Mac Mini Configuration

### Energy Settings (System Settings → Energy)

- ✅ **Prevent automatic sleeping when display is off**
- ✅ **Wake for network access**
- ✅ **Start up automatically after a power failure**

### Amphetamine (recommended)

The free **Amphetamine** app from the Mac App Store provides more reliable sleep prevention than system settings alone:

1. Install from Mac App Store
2. Launch → Enable **Launch at login**
3. Set **Start session when Amphetamine launches** → **Indefinitely**
4. Enable **Start session after waking from sleep**
5. A filled pill icon in the menu bar = active (preventing sleep)

### HDMI Dummy Plug

A ~$10 HDMI dummy plug is critical for headless Mac mini operation. Without it, macOS runs in a reduced GPU mode that can cause display-related issues with some applications. The plug tricks macOS into thinking a display is connected, enabling full GPU acceleration.

### Keep-Awake via Terminal (alternative)

```bash
sudo pmset -a disablesleep 1
```

To revert: `sudo pmset -a disablesleep 0`

## Remote Access via Tailscale

Tailscale creates a secure private network between your devices without opening any public ports. This is the recommended way to access your Mac mini remotely.

### Setup

1. Install Tailscale from the Mac App Store on the Mac mini
2. Install Tailscale on your daily-driver device
3. Sign both into the same Tailscale account (same Tailnet)
4. Enable SSH on Mac mini: **System Settings → General → Sharing → Remote Login**

### Access the Gateway (SSH tunnel)

Since the gateway binds to loopback (127.0.0.1), use SSH port forwarding:

```bash
ssh -L 18789:127.0.0.1:18789 yourusername@100.x.x.x
# Then open: http://127.0.0.1:18789/?token=YOUR_GATEWAY_TOKEN
```

### Tailscale Serve (expose to all Tailnet devices)

```bash
tailscale serve 18789
```

This exposes the gateway to all your Tailnet devices with automatic TLS. Tailscale works even with macOS "Block all incoming connections" enabled — it routes through its own virtual network interface.

### Screen Sharing (VNC)

Enable in **System Settings → General → Sharing → Screen Sharing**, then connect from another device via `vnc://mac-mini-tailscale-ip`.

## macOS Companion App

OpenClaw offers an optional macOS companion app providing:
- Menu bar control plane (start/stop gateway)
- Voice Wake (wake word activation)
- Talk Mode overlay (speech-to-text interaction)
- WebChat (local chat interface)

Install from openclaw.ai or via the onboarding wizard. Requires macOS 14+ (Sonoma).

## File Locations

| File | Location |
|------|----------|
| Main config | `~/.openclaw/openclaw.json` |
| Credentials | `~/.openclaw/credentials/` |
| SOUL.md | `~/.openclaw/workspace/SOUL.md` |
| MEMORY.md | `~/.openclaw/workspace/MEMORY.md` |
| Gateway logs | `/tmp/openclaw/openclaw-YYYY-MM-DD.log` |
| LaunchAgent | `~/Library/LaunchAgents/com.openclaw.gateway.plist` |
| Command logs | `~/.openclaw/logs/commands.log` (if hook enabled) |

## Updating

```bash
openclaw update --channel stable
openclaw --version    # Verify new version
openclaw gateway restart
openclaw doctor       # Validate health after update
```

## Post-Setup: Web Search and Services

### Brave Search (recommended — 2,000 free requests/month)

```bash
openclaw configure --section web
# Or set directly:
export BRAVE_API_KEY="your-key-here"
```

Note: Brave requires a credit card for anti-fraud even on the free tier.

### Tavily (alternative — 1,000 free searches/month, no credit card)

```bash
openclaw mcp add --transport http tavily https://mcp.tavily.com/mcp/?tavilyApiKey=<key>
```

## Key Slash Commands

| Command | Purpose |
|---------|---------|
| `/new [model]` | Fresh session |
| `/compact [instructions]` | Trigger context compaction |
| `/model <name>` | Switch model or show picker |
| `/think <off\|minimal\|low\|medium\|high\|xhigh>` | Set thinking level |
| `/status` | Session health, tokens, cost |
| `/stop` | Abort current agent run |
| `/verbose` | Toggle verbose output |
| `/tts on\|off` | Toggle text-to-speech |
| `/bash <command>` | Host-only command execution |
