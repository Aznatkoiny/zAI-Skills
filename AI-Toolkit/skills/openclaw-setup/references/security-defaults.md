# Security defaults and hardening

Checked against OpenClaw 2026.9.9 and https://docs.openclaw.ai/gateway/security (October 2026).

The threat model, briefly: OpenClaw gives a language model tools on a real machine and lets people message it. Three things go wrong in practice. The Gateway is reachable by strangers (exposed ports, leaked token). Someone who can message the agent, or whose text reaches it through a group chat, web page or email, talks it into misusing its tools (prompt injection). Or a third-party skill or plugin is malicious. Every setting below narrows one of those.

## Contents
- Hardened baseline
- Tools, sandboxing and SOUL.md
- Skills and plugins
- Files and secrets
- Network exposure
- Staying current
- Incident response

## Hardened baseline

OpenClaw's own recommended starting point (from https://docs.openclaw.ai/gateway/security/hardened-baseline), adapted for Telegram:

```json5
{
  gateway: {
    mode: "local",
    bind: "loopback",                 // native installs; Docker uses "lan" inside the container and protects the host ports instead
    auth: { mode: "token" },          // keep the token onboarding generated
  },
  session: { dmScope: "per-channel-peer" },   // each contact gets a separate session
  tools: {
    profile: "messaging",
    deny: ["group:automation", "group:runtime", "group:fs", "sessions_spawn", "sessions_send"],
    fs: { workspaceOnly: true },
    exec: { security: "deny", ask: "always" },
    elevated: { enabled: false },
    sessions: { visibility: "agent" },
    agentToAgent: { enabled: false },
  },
  channels: {
    telegram: { dmPolicy: "pairing", groups: { "*": { requireMention: true } } },
  },
}
```

This is deliberately tight: the agent can chat and use messaging tools, but can't run commands or touch files outside its workspace. Widen it one capability at a time, for a specific agent, when the user needs something, and say what each change allows. Validate with `openclaw config validate` and `openclaw security audit --deep` after changes.

## Tools, sandboxing and SOUL.md

- **Sandboxing** is off by default. To run non-main sessions (groups, other contacts) in a container: `agents.defaults.sandbox: { mode: "non-main", scope: "session", workspaceAccess: "none" }`. See https://docs.openclaw.ai/gateway/sandboxing.
- **Elevated tools** run commands outside the sandbox. Keep `tools.elevated` off, or limited to the owner with a tight `allowFrom`, and never enable it for agents that groups or other people can reach.
- **Chat commands:** `/bash` runs host commands from chat and needs `commands.bash` enabled; leave it off unless only the owner can reach the bot. `/restart` is on by default; set `commands.restart: false` to disable it.
- **SOUL.md and memory files** shape the agent's behavior, but they're instructions to a model, not enforcement. A determined injection can talk past them. Write any rules there in plain sentences with the reason (for example, "Don't run commands that delete files, because this machine holds the owner's only copy of their notes"), and rely on tool policy and sandboxing for anything that must not happen. Don't put credentials in these files; they're sent to the model every turn.

## Skills and plugins

Third-party skills and plugins run with the agent's permissions, and malicious ones have been found on ClawHub in large numbers. Recommend bundled skills only at first. For anything from ClawHub, check its trust verdict and scan status (`openclaw skills verify @owner/<slug>`), read its source before installing, and treat a pending or missing scan as unverified. Plugins need explicit capability consent; read what they request before accepting.

## Files and secrets

- `chmod 700 ~/.openclaw` and `chmod 600 ~/.openclaw/openclaw.json`; `openclaw security audit` flags looser permissions.
- Turn on full-disk encryption (FileVault on macOS, LUKS on Linux) on machines that hold the state.
- Prefer secret references over plaintext keys in config: `openclaw secrets configure` (see https://docs.openclaw.ai/gateway/security/secrets-and-storage). Model credentials now live in a per-agent SQLite auth store; older `auth-profiles.json` files are migration sources that `openclaw doctor` imports.

## Network exposure

- Native installs: `gateway.bind: "loopback"` plus token auth; remote access through an SSH tunnel or Tailscale Serve, never Tailscale Funnel or a public port.
- Docker: publish ports only on `127.0.0.1`, and remember UFW doesn't filter Docker-published ports (`vps-setup.md` covers the override file and `DOCKER-USER` rules). The upstream compose file publishes 18789, 18790 and 3978.
- mDNS/Bonjour: keep it off on servers; on a home Mac, `discovery.mdns.mode: "minimal"` (the default when enabled) avoids broadcasting paths and hostnames.
- Check from outside: `nmap -Pn -p 18789,18790,3978 <public-ip>` should show nothing open.

## Staying current

OpenClaw publishes security advisories often, many of them high or critical. Treat "on the latest stable or extended-stable release" as the requirement: `openclaw update status`, `openclaw update`, then `openclaw doctor`. CVE-2026-25253 (a one-click remote-code-execution bug through the Control UI, fixed in 2026.1.29) is the best-known example; being past that version is not enough on its own. Advisories: https://github.com/openclaw/openclaw/security/advisories.

## Incident response

If the user suspects compromise, from https://docs.openclaw.ai/gateway/security/operator-incident-response:

1. **Contain:** stop the Gateway (`openclaw gateway stop`, or `docker compose down`). Close exposure (loopback bind, Tailscale Serve/Funnel off). Set risky channels to `dmPolicy: "disabled"`.
2. **Rotate**, writing each new secret where the Gateway actually reads it. For the gateway token, back up the config, then have the user generate a new token and put it in `gateway.auth.token` (or the Docker host's `.env`, followed by `docker compose up -d`; a restart doesn't re-read `.env`). Exporting a variable in a shell rotates nothing. Then rotate the Anthropic key in the Claude Console, every channel token (BotFather `/revoke`), and any other provider keys. Confirm the old token is rejected.
3. **Audit:** `openclaw logs` (default file `/tmp/openclaw/openclaw-YYYY-MM-DD.log`), session transcripts in `~/.openclaw/agents/<agentId>/sessions/`, recent config changes to bind, auth, DM/group policy and elevated tools, and `openclaw security audit --deep`.
4. **Report:** OpenClaw version, OS, what was exposed, and redacted transcript and log excerpts.
