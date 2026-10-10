# Telegram channel

Checked against OpenClaw 2026.9.9 and https://docs.openclaw.ai/channels/telegram/setup (October 2026). Works on a Mac or a VPS.

## Contents
- Create the bot
- Give OpenClaw the token
- Approve the first DM (pairing)
- Groups
- Troubleshooting

## Create the bot

In Telegram, chat with **@BotFather** (check the handle is exactly that; impostors exist) or open its web app at https://t.me/BotFather?startapp. Run `/newbot`, pick a name and username, and BotFather replies with a token. The token is a password for the bot: the user keeps it in their password manager and doesn't paste it into this conversation.

Leave BotFather's **privacy mode on** (the default). With it on, the bot only sees group messages that mention it or reply to it, which matches the mention-gated setup below and keeps the bot from reading every message in a group, where any member could try to steer it. Turn it off only if the user deliberately wants the bot to see all group traffic, and explain that trade-off.

## Give OpenClaw the token

Have the user run this themselves, in their own terminal, so the token doesn't land in the conversation:

```bash
openclaw channels add --channel telegram --token <bot-token>
```

That writes the token into config. Alternatives: `botToken` or `tokenFile` (a path to a file containing the token, preferred on servers) under `channels.telegram`, or the `TELEGRAM_BOT_TOKEN` environment variable for the default account. On Docker, run it as `docker compose run --rm openclaw-cli channels add …`.

Then make sure the access settings are the safe ones:

```json5
{
  channels: {
    telegram: {
      enabled: true,
      dmPolicy: "pairing",                       // strangers can't start a conversation
      groups: { "*": { requireMention: true } }, // in groups, answer only when mentioned
    },
  },
}
```

Check: `openclaw channels status --probe`. The Gateway hot-reloads channel config; if it's offline, `openclaw gateway start`.

## Approve the first DM (pairing)

The user sends the bot any message, which creates a pairing request. Then:

```bash
openclaw pairing list telegram
openclaw pairing approve telegram <CODE>
```

Codes expire after an hour, and at most 3 can be pending; a new DM produces a fresh code. Only approve codes the user recognizes as theirs.

## Groups

Groups are off unless allowed. To use one, the user adds the bot to the group, then allows that group by its chat ID (a negative number; supergroups start with `-100`) under `channels.telegram.groups`, and allows their own Telegram user ID with `groupAllowFrom` if they want only themselves to trigger it. `openclaw logs --follow` shows the IDs when the bot receives a message, and `/whoami@<bot_username>` confirms them once the group is allowed. Keep `requireMention: true` unless there's a reason not to.

In groups the agent sees other people's messages as context, and those people can try to instruct it. Keep powerful tools away from group-facing agents (see `security-defaults.md`).

## Troubleshooting

| Symptom | Check |
|---|---|
| `channels status` shows an auth error | Token wrong or revoked: regenerate in BotFather (`/revoke`, then `/token`), and the user re-runs `channels add` |
| DMs get no reply | Pairing not approved (`openclaw pairing list telegram`), or the Gateway is down (`openclaw gateway status`) |
| Bot ignores a group | Group not allowed under `channels.telegram.groups`, or the message didn't mention the bot |
| Bot sees only some group messages | That's privacy mode working as intended; mention the bot |
| Config error mentioning Telegram keys | Run `openclaw doctor`; keys from older guides (`streaming: "edit"`, `linkPreviews`) are no longer valid; check `openclaw config schema` |
