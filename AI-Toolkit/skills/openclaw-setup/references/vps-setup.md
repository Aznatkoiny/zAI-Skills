# OpenClaw on a Linux VPS (Docker)

Checked against OpenClaw 2026.9.9 (October 2026). Works on any Ubuntu/Debian VPS (Hostinger, Hetzner, DigitalOcean, ...); Hostinger's own options are at the end. Upstream guides: https://docs.openclaw.ai/vps, https://docs.openclaw.ai/install/docker, https://docs.openclaw.ai/gateway/security/network-exposure.

A VPS is reachable by the whole internet, so the order of steps matters more here than anywhere else. Every step that changes the server gets a one-line explanation and the user's OK first.

## Contents
- 1. Secure admin access without locking yourself out
- 2. Install Docker and OpenClaw
- 3. Keep every published port on loopback
- 4. Reach the dashboard
- 5. Verify
- Day-2: updates, backups, CLI
- Hostinger options

## 1. Secure admin access without locking yourself out

Locking down SSH before a working key login exists is the classic way to lose the server. Do it in this order:

1. As root (or the provider's initial user), create a normal user with sudo: `adduser claw && usermod -aG sudo claw`.
2. Install the user's SSH **public** key for that user (`ssh-copy-id claw@SERVER` from their computer, or paste it into `/home/claw/.ssh/authorized_keys` with `chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys`).
3. **In a second terminal**, have the user log in as `claw` with the key and run `sudo -v`. Don't continue until this works. Keep the first session open.
4. Only then disable root and password logins (`PermitRootLogin no`, `PasswordAuthentication no` in `/etc/ssh/sshd_config` or a file in `sshd_config.d/`), check with `sudo sshd -t`, and `sudo systemctl reload ssh`. Test a new login again before closing the old session.
5. Firewall: `sudo ufw allow OpenSSH && sudo ufw enable`. If the user prefers Tailscale for admin access, set that up and confirm a login over the Tailscale address before restricting public SSH.

If something goes wrong, most providers offer a browser console (Hostinger: hPanel → VPS → Browser terminal) to recover.

## 2. Install Docker and OpenClaw

As `claw`:

```bash
curl -fsSL https://get.docker.com | sudo sh          # Docker Engine + Compose v2
sudo usermod -aG docker claw && newgrp docker
git clone https://github.com/openclaw/openclaw.git && cd openclaw
export OPENCLAW_IMAGE="ghcr.io/openclaw/openclaw:latest"   # use the official prebuilt image
./scripts/docker/setup.sh
```

`setup.sh` creates `.env`, generates the Gateway token into it, runs onboarding (the user types their Anthropic API key at the prompt), and starts the stack. Afterwards: `chmod 600 .env`. The token lives in `.env`; the user reads it there themselves when they need it.

## 3. Keep every published port on loopback

The upstream `docker-compose.yml` publishes three ports on **all** interfaces: 18789 (Gateway), 18790 (bridge) and 3978 (Microsoft Teams webhook). Inside the container the Gateway has to listen on its network interface (`gateway.bind: "lan"`, which `setup.sh` sets on purpose), so what keeps it private is how Docker publishes it on the host. UFW doesn't help here: Docker-published ports bypass UFW's normal rules.

Create `docker-compose.override.yml` next to `docker-compose.yml` (needs Docker Compose 2.24.4 or later for `!override`; check with `docker compose version`):

```yaml
services:
  openclaw-gateway:
    ports: !override
      - "127.0.0.1:18789:18789"
      # add "127.0.0.1:18790:18790" or "127.0.0.1:3978:3978" only if you use those features
```

Then `docker compose up -d`. Because it lives in a separate file, a `git pull` won't undo it. For defense in depth, add the `DOCKER-USER` firewall rules from the network-exposure doc linked above, which block new inbound connections to any container port from public addresses.

## 4. Reach the dashboard

From the user's computer: `ssh -N -L 18789:127.0.0.1:18789 claw@SERVER`, then open `http://127.0.0.1:18789/` and paste the token from `.env`. Or use Tailscale Serve (`gateway.tailscale.mode: "serve"`), which keeps the Gateway on loopback and publishes it only to the user's tailnet.

## 5. Verify

```bash
ss -tlnp | grep -E '18789|18790|3978'     # every line must show 127.0.0.1, never 0.0.0.0 or [::]
docker compose ps
curl -fsS http://127.0.0.1:18789/healthz
docker compose run --rm openclaw-cli security audit --deep
docker compose run --rm openclaw-cli doctor
```

From outside (the user's laptop): `nmap -Pn -p 18789,18790,3978 SERVER` should report the ports closed or filtered.

## Day-2: updates, backups, CLI

- Run OpenClaw commands through the CLI container: `docker compose run --rm openclaw-cli <command>`.
- Update: `docker compose pull && docker compose up -d`, then the verify block above.
- State lives on the host in `~/.openclaw` (mounted into the container at `/home/node/.openclaw`). Back it up from the host, for example `tar czf openclaw-backup-$(date +%F).tgz -C ~ .openclaw`, or use `openclaw backup` through the CLI container. Store backups somewhere other than the VPS.
- Environment changes (`.env`) need `docker compose up -d` to take effect; `restart` doesn't re-read `.env`.

## Hostinger options

Hostinger sells OpenClaw two ways (prices change; link to https://www.hostinger.com/openclaw rather than quoting them):

- **Managed (1-Click) OpenClaw:** Hostinger runs the infrastructure, Docker and updates, and the user manages OpenClaw from hPanel. Least work, but Hostinger, not the user, controls host hardening and how the dashboard is exposed. Still apply the OpenClaw-side settings: pairing, mention gating, tool limits, spend cap.
- **OpenClaw on a VPS via Docker Manager:** hPanel deploys the container and asks for the gateway token and API keys in a form. Afterwards, check the port publishing (section 3) and the SSH setup (section 1) yourself, since the template's defaults may publish ports publicly.
- **A plain Hostinger VPS:** follow this guide from the top.
