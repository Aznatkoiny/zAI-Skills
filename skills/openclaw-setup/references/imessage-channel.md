# iMessage Channel Setup (macOS Only)

Connect OpenClaw to iMessage so you can message your AI assistant from any Apple device. Two methods are available: BlueBubbles (recommended) and the legacy `imsg` channel.

## Requirements

- **macOS only** — iMessage is NOT available on Linux VPS deployments
- **Messages app** signed in with your Apple ID on the Mac running OpenClaw
- **OpenClaw running locally** on the same Mac
- macOS 14 (Sonoma) or later recommended

## Method 1: BlueBubbles (Recommended)

BlueBubbles is the recommended iMessage integration. It's a bundled plugin that communicates with the BlueBubbles macOS server over HTTP, providing a richer feature set than the legacy method.

### Features

- ✅ Typing indicators
- ✅ Read receipts
- ✅ Tapback reactions
- ✅ Attachments (images, files)
- ✅ Voice memo support
- ✅ Edit/unsend support
- ✅ Reliable message handling (no race conditions)

### Setup

1. Install the **BlueBubbles Server** app on your Mac:
   - Download from bluebubbles.app or via Homebrew
   - Launch and complete initial setup
   - BlueBubbles Server runs alongside Messages.app

2. Configure OpenClaw to connect to BlueBubbles:

```json5
{
  channels: {
    bluebubbles: {
      enabled: true,
      // BlueBubbles server URL (default localhost)
      serverUrl: "http://127.0.0.1:1234",
      password: "<bluebubbles-server-password>",
      dmPolicy: "pairing",
      groups: {
        "*": { requireMention: true }
      }
    }
  }
}
```

3. Restart OpenClaw: `openclaw gateway restart`
4. Verify: `openclaw channels status --probe`

### BlueBubbles Permissions

BlueBubbles Server needs the same macOS permissions as the legacy method:
- **Full Disk Access** — to read Messages database
- **Automation** — to send messages via AppleScript

## Method 2: Legacy imsg Channel

The legacy `imsg` channel directly accesses the Messages database. It works but has known limitations.

### How It Works

1. Monitors `~/Library/Messages/chat.db` (SQLite database) for new messages
2. Sends replies via AppleScript through Messages.app
3. Polls the database at regular intervals

### Configuration

Minimal config — just enable it:

```json5
{
  channels: {
    imsg: {
      enabled: true,
      dmPolicy: "pairing",
      groups: {
        "*": { requireMention: true }
      }
    }
  }
}
```

### macOS Permissions (required for both methods)

Grant these in **System Settings → Privacy & Security**:

1. **Full Disk Access** — Add Terminal (or your terminal app) AND the OpenClaw process
   - System Settings → Privacy & Security → Full Disk Access → toggle on for Terminal
   - This allows reading `~/Library/Messages/chat.db`

2. **Automation** — Allow OpenClaw to control Messages.app
   - System Settings → Privacy & Security → Automation → enable Messages access
   - First-time use triggers a system permission dialog — click Allow

### Legacy imsg Limitations

- ⚠️ **Duplicate-message race conditions** — The database polling approach can occasionally process the same message twice, especially under load
- macOS only (no Linux/Windows support)
- Single Apple ID account only
- Mac must be awake and Messages must be signed in
- No read receipt support
- No typing indicator support
- No tapback/reaction support
- Rate limited by Apple (sending too many messages too fast may trigger throttling)

**Recommendation:** Use BlueBubbles instead of legacy `imsg` for a more reliable experience.

## DM Policy and Pairing

Same as Telegram — with `dmPolicy: "pairing"`, unknown iMessage contacts receive a pairing code:

```bash
# List pending pairing requests
openclaw pairing list imsg        # For legacy
openclaw pairing list bluebubbles # For BlueBubbles

# Approve
openclaw pairing approve imsg ABC123
openclaw pairing approve bluebubbles ABC123
```

## Group Chat Configuration

iMessage group chats work similarly to Telegram groups:

```json5
{
  channels: {
    imsg: {  // or bluebubbles
      groups: {
        "*": { requireMention: true }
      }
    }
  }
}
```

Note: iMessage group @mentions work differently than Telegram — the bot name must be typed as a mention in the group chat. The exact behavior depends on the group type (standard iMessage group vs. group chat with SMS participants).

## Keep-Awake Configuration

For a Mac mini running as an always-on iMessage gateway, the Mac must never sleep:

### System Settings

- **System Settings → Energy** → Enable "Prevent automatic sleeping when display is off"
- Enable "Wake for network access"
- Enable "Start up automatically after a power failure"

### Amphetamine (recommended)

Install the free Amphetamine app from the Mac App Store for more reliable sleep prevention. See `mac-local-setup.md` for setup details.

### Terminal (alternative)

```bash
sudo pmset -a disablesleep 1
```

### HDMI Dummy Plug

A ~$10 HDMI dummy plug prevents macOS from entering a reduced GPU mode on headless Mac minis. Recommended for always-on setups.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| **Messages not detected** | Full Disk Access not granted | System Settings → Privacy & Security → Full Disk Access → enable for Terminal and OpenClaw |
| **Can't send replies** | Automation permission missing | System Settings → Privacy & Security → Automation → enable Messages control |
| **Duplicate messages** | Legacy `imsg` race condition | Switch to BlueBubbles method |
| **Messages stop after sleep** | Mac went to sleep | Configure energy settings + Amphetamine; verify with `pmset -g assertions` |
| **iMessage not available** | Not signed into Messages | Open Messages.app → sign in with Apple ID |
| **Permission dialog doesn't appear** | Already denied previously | System Settings → Privacy & Security → reset permissions for the app |
| **VPS deployment** | iMessage requires macOS | Use Mac mini for iMessage; VPS can run Telegram/WhatsApp only |
| **Rate limiting** | Too many messages sent quickly | Reduce message frequency; Apple throttles automated sends |

## Architecture Note

iMessage integration is fundamentally different from cloud channels like Telegram:
- **Telegram**: Bot connects to Telegram's cloud API. Works from any server with internet.
- **iMessage**: Requires physical access to the Messages database on a Mac. Must run on macOS with Messages signed in. This is why iMessage only works with the Mac mini deployment path, never on a Linux VPS.
