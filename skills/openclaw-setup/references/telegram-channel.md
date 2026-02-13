# Telegram Channel Configuration

Connect OpenClaw to Telegram so you can message your AI assistant from any device. This covers bot creation, DM pairing, and group chat setup.

## Step 1: Create a Telegram Bot via BotFather

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Enter a **display name** (e.g., "My OpenClaw Assistant")
4. Enter a **username** — must end with `bot` (e.g., `myopenclaw_bot`)
5. BotFather returns a **bot token** in the format: `123456789:ABCdefGHIJKLMNOP...`
6. **Save this token securely** — it's the only credential needed

### Recommended BotFather Settings

After creating the bot, send these commands to @BotFather:

- `/setjoingroups` → Select your bot → **Allow** (lets the bot be added to groups)
- `/setprivacy` → Select your bot → **Disable** (bot can see all group messages, not just commands)

⚠️ **After changing privacy to Disabled, you must remove and re-add the bot to each existing group** for the change to take effect. New groups added after the change work automatically.

## Step 2: Configure in OpenClaw

### During Onboarding

The onboarding wizard (`openclaw onboard`) will prompt for Telegram setup. Select Telegram when asked about channels, then paste your bot token.

### Manual Configuration

Add to `~/.openclaw/openclaw.json`:

```json5
{
  channels: {
    telegram: {
      enabled: true,
      botToken: "123456789:ABCdefGHIJKLMNOP",
      dmPolicy: "pairing",
      groups: {
        "*": { requireMention: true }
      }
    }
  }
}
```

### Via Environment Variable

Alternatively, set the token as an environment variable (useful for Docker/VPS):

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIJKLMNOP"
```

Then restart: `openclaw gateway restart`

### ⚠️ CRITICAL: Telegram is a CHANNEL, not a Plugin

This is the most common configuration mistake. The config must go under `channels.telegram`:

```json5
// ✅ CORRECT
{ channels: { telegram: { enabled: true, botToken: "..." } } }

// ❌ WRONG — will cause "plugin not found" error
{ plugins: { entries: { telegram: { enabled: true, botToken: "..." } } } }
```

## Step 3: DM Pairing

With `dmPolicy: "pairing"` (recommended), unknown senders who DM the bot receive a short pairing code. You must approve each new contact.

### Pairing Flow

1. Someone DMs your bot on Telegram
2. Bot replies with a pairing code (e.g., `ABC123`)
3. On your OpenClaw host, approve the pairing:

```bash
# List pending pairing requests
openclaw pairing list telegram

# Approve a specific code
openclaw pairing approve telegram ABC123
```

**Pairing details:**
- Codes expire after **1 hour**
- Maximum **3 pending requests** per channel at a time
- After approval, the contact can message freely (within their session)

### Docker Commands

On a VPS with Docker, prefix with `docker compose exec`:

```bash
docker compose exec openclaw-gateway openclaw pairing list telegram
docker compose exec openclaw-gateway openclaw pairing approve telegram ABC123
```

## Step 4: Group Chat Configuration

Groups use isolated sessions — each group gets its own conversation context.

### Mention-Gating (recommended)

With `requireMention: true`, the bot only responds when @mentioned in group chats. This prevents it from responding to every message.

```json5
{
  channels: {
    telegram: {
      groups: {
        "*": { requireMention: true }  // All groups require @mention
      }
    }
  }
}
```

### Per-Group Configuration

Override settings for specific groups by using the group chat ID:

```json5
{
  channels: {
    telegram: {
      groups: {
        "*": { requireMention: true },
        "-1001234567890": { requireMention: false }  // This specific group doesn't need @mention
      }
    }
  }
}
```

### Privacy Mode Requirement

If `requireMention` is set to `false` for any group, the bot must have **Telegram privacy mode disabled** (via BotFather: `/setprivacy → Disable`). Otherwise, the bot only sees messages starting with `/` or messages that @mention it.

Remember: After changing privacy mode, **remove and re-add the bot** to existing groups.

### History Injection

When the bot is added to a group or when a new session starts, OpenClaw provides the last 50 unprocessed messages as context. This helps the bot understand the ongoing conversation.

## Advanced Options

### Custom Bot Commands

Register slash commands with BotFather for discoverability:

```
/setcommands → Select your bot → Enter:
new - Start a new conversation
status - Show session status
help - Show available commands
```

### Streaming Mode

Control how responses appear in Telegram:

```json5
{
  channels: {
    telegram: {
      streaming: "edit"      // Edit message in-place as tokens arrive (default)
      // streaming: "append"  // Send complete message after generation
    }
  }
}
```

### Link Previews

```json5
{
  channels: {
    telegram: {
      linkPreviews: false    // Disable link previews in bot responses
    }
  }
}
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| **401 Unauthorized** | Invalid or expired bot token | Go to BotFather → `/token` → regenerate; update config; restart gateway |
| **Bot doesn't respond in groups** | Privacy mode enabled | BotFather → `/setprivacy → Disable`; then **remove and re-add** bot to each group |
| **"plugin not found: telegram"** | Config in wrong location | Move config from `plugins.entries.telegram` to `channels.telegram` |
| **Pairing code not accepted** | Code expired (1-hour limit) or max 3 pending | Ask the contact to DM again for a fresh code |
| **"setMyCommands failed"** | DNS/firewall blocking api.telegram.org | Check DNS resolution: `nslookup api.telegram.org`; check firewall rules |
| **Bot responds to everything in group** | `requireMention: false` | Set `requireMention: true` in group config |
| **Multiple bots interfering** | Same token used across instances | Each OpenClaw instance needs its own bot with a unique token |

## Session Behavior

- **DMs** collapse to the agent's main session: `agent:main:main`
- **Groups** get isolated sessions: `agent:<agentId>:telegram:group:<chatId>`
- Use `/new` command in Telegram to start a fresh session
- Session isolation prevents cross-user context leakage when `session.dmScope: "per-channel-peer"` is set (see `security-defaults.md`)
