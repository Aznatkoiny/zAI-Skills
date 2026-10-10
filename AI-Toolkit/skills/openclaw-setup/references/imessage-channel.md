# iMessage channel (macOS)

Checked against OpenClaw 2026.9.9 and https://docs.openclaw.ai/channels/imessage (October 2026).

BlueBubbles support was **removed** from OpenClaw. iMessage now works only through the official `@openclaw/imessage` plugin, which drives the `imsg` command-line tool. If the user has an old `channels.bluebubbles` block, migrate it to `channels.imessage` (see https://docs.openclaw.ai/channels/imessage-from-bluebubbles); an `imsg` channel key from older guides is also invalid now.

## Contents
- Requirements
- Set up (Gateway on the Messages Mac)
- Permissions
- Basic vs private-API mode
- Approve the first conversation
- Troubleshooting

## Requirements

- A Mac signed in to Messages. Usually the Gateway runs on that same Mac; if it doesn't, `imsg` can run over an SSH wrapper (see the upstream setup page).
- Ideally a **dedicated Apple ID and macOS user** for the assistant. The agent can read that account's message history, and the permissions below are broad, so keeping them off the owner's personal account limits the damage if the agent is misled.

## Set up (Gateway on the Messages Mac)

Each of these installs software or changes config, so explain and get a yes first:

```bash
openclaw plugins install @openclaw/imessage
brew install steipete/tap/imsg
imsg rpc --help                  # confirms imsg works
```

Then add the channel (the setup wizard can also do this), with the path `brew --prefix` reports and the signed-in user's Messages database:

```json5
{
  channels: {
    imessage: {
      enabled: true,
      cliPath: "/opt/homebrew/bin/imsg",                 // Apple silicon Homebrew; /usr/local/bin on Intel
      dbPath: "/Users/<user>/Library/Messages/chat.db",
    },
  },
}
```

Check with `openclaw channels status --probe`. iMessage DMs use pairing by default.

## Permissions

macOS grants these per process, to whatever runs `imsg`:

- **Full Disk Access**, to read the Messages database. Grant it to the specific process that runs the Gateway or `imsg`. Avoid granting it to Terminal broadly: every program started from that terminal (including scripts and package installers) would inherit read access to the user's protected files.
- **Automation → Messages**, to send.

If the Gateway runs as a LaunchAgent, trigger the permission prompts once from that same context, for example `imsg chats --limit 1`, and approve them.

## Basic vs private-API mode

- **Basic mode** (default): sending and receiving text and media, chat list and history. No system changes.
- **Private-API mode** adds reactions, edits, threaded replies, effects, polls and group management, but requires **disabling System Integrity Protection** and relaxing library validation so a helper can be injected into Messages (`imsg launch`). That's a real security trade-off: SIP is one of macOS's core protections, and on Apple silicon turning it off also stops iOS apps from running. Recommend basic mode unless the user wants those features and runs a dedicated Mac. If they do, follow https://docs.openclaw.ai/channels/imessage/private-api step by step with them.

## Approve the first conversation

The user messages the assistant's Apple ID from their phone, then:

```bash
openclaw pairing list imessage
openclaw pairing approve imessage <CODE>
```

Codes expire after an hour.

## Troubleshooting

| Symptom | Check |
|---|---|
| Nothing comes in | Full Disk Access for the process running `imsg`; `imsg chats --limit 1` works in that context; Messages is signed in |
| Receives but can't send ("Not authorized to send Apple events", -1743) | Automation → Messages permission for the right process; trigger it once with `imsg send <your-handle> "test"` in the Gateway's context |
| Reactions / edits / effects fail | Those need private-API mode (SIP off); basic mode can't do them |
| Config error about `bluebubbles` or `imsg` keys | Old format: migrate to `channels.imessage`, then `openclaw doctor` |
| Missed messages after a restart | Replayed automatically; no config needed |
