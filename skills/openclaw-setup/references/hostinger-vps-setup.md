# Hostinger VPS Deployment

Deploy OpenClaw to a Hostinger VPS using Docker for 24/7 cloud availability. This guide covers both the one-click Docker template and manual deployment.

## ⚠️ VPS Security Warning

VPS deployments are the #1 source of exposed OpenClaw instances. Security researcher Maor Dayan found **42,665 publicly exposed instances** via Shodan — 93.4% had critical auth bypasses. The root cause: Docker's default port publishing binds to `0.0.0.0` (all interfaces), making the gateway discoverable on the public internet.

**You MUST actively harden a VPS deployment.** Follow every security step in this guide and in `security-defaults.md`. If you're not comfortable with Linux server administration, use the Mac mini local deployment path instead — it's much safer by default.

## Plan Selection

| Plan | Specs | Use Case | Price |
|------|-------|----------|-------|
| **KVM 1** | 1 vCPU, 4GB RAM, 50GB NVMe | Cloud API only, 1-2 channels, personal use | ~$5-6/mo (promo) |
| **KVM 2** (recommended) | 2 vCPU, 8GB RAM, 100GB NVMe | Multiple channels, local 7B model via Ollama | ~$7-9/mo (promo) |

**Realistic minimum requirements:** 2 CPU cores, 4GB RAM, 40GB storage. Community consensus says the advertised $5/month floor is often insufficient. Plans renew at ~$12.99/month for 2-year terms.

**Critical:** Enable **daily automatic backups** in hPanel during purchase — this is essential for recovery.

## Important Limitations

- **No iMessage** — iMessage requires macOS with Messages signed in. VPS runs Linux.
- **No voice wake** — Voice Wake requires the macOS companion app.
- If you need iMessage, use the Mac mini path and optionally pair the VPS as a remote device node.

## Path A: One-Click Docker Template (recommended)

Hostinger provides a pre-configured OpenClaw Docker image in the hPanel Docker Manager Catalog.

### For a new VPS purchase:

1. Go to hostinger.com → VPS Hosting → choose a plan (KVM 2 recommended)
2. During setup, select **Docker** as the OS template
3. In the Docker Catalog, find **OpenClaw** and select it
4. Configure environment variables:
   - `OPENCLAW_GATEWAY_TOKEN` — auto-generated (save this immediately)
   - `ANTHROPIC_API_KEY` — paste your API key (with spending limits already set!)
   - Optional: `OPENAI_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`
5. Deploy — the container auto-starts

### For an existing VPS:

1. In hPanel → VPS → OS & Panel → switch to **Docker OS** (⚠️ this wipes all existing data)
2. Once Docker OS is active, open Docker Manager → Catalog → deploy OpenClaw
3. Configure environment variables as above

### Retrieve your gateway token:

The token is shown during deployment and saved in the Docker environment. To retrieve it later:

```bash
ssh root@YOUR_VPS_IP
docker compose exec openclaw-gateway printenv OPENCLAW_GATEWAY_TOKEN
```

### Access the Control UI:

```bash
# Via SSH tunnel (recommended — no public port exposure)
ssh -N -L 18789:127.0.0.1:18789 root@YOUR_VPS_IP
# Then open: http://127.0.0.1:18789/?token=YOUR_GATEWAY_TOKEN
```

## Path B: Manual Docker Deployment

For full control over the setup, deploy manually.

### 1. SSH into your VPS

```bash
ssh root@YOUR_VPS_IP
```

### 2. Create a dedicated non-root user

```bash
useradd -r -m -d /opt/openclaw -s /bin/bash openclaw
passwd openclaw
usermod -aG docker openclaw
su - openclaw
```

### 3. Install Docker (if not pre-installed)

```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker
```

### 4. Clone and configure

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
cp .env.example .env
```

Edit `.env`:
```bash
OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 32)
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 5. Fix Docker port binding (CRITICAL)

Edit `docker-compose.yml` — change the port binding from the default:

```yaml
# ❌ WRONG — binds to all interfaces, publicly accessible
ports:
  - "18789:18789"

# ✅ CORRECT — binds to localhost only
ports:
  - "127.0.0.1:18789:18789"
```

This single change prevents your gateway from being discoverable via Shodan.

### 6. Start the container

```bash
docker compose up -d
```

### 7. Verify binding

```bash
ss -tlnp | grep 18789
# Must show: 127.0.0.1:18789
# Must NOT show: 0.0.0.0:18789
```

If you see `0.0.0.0:18789`, stop immediately and fix the docker-compose port binding.

## CLI Commands in Docker

Prefix all `openclaw` commands with `docker compose exec`:

```bash
docker compose exec openclaw-gateway openclaw --version
docker compose exec openclaw-gateway openclaw doctor
docker compose exec openclaw-gateway openclaw security audit --deep
docker compose exec openclaw-gateway openclaw channels status --probe
docker compose exec openclaw-gateway openclaw gateway logs --follow
docker compose exec openclaw-gateway openclaw pairing list telegram
docker compose exec openclaw-gateway openclaw pairing approve telegram <CODE>
```

## VPS Network Security (mandatory)

### Tailscale (zero public ports — recommended)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Expose gateway only to your Tailnet devices
tailscale serve https / http://127.0.0.1:18789
```

### UFW Firewall

```bash
sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp        # SSH
sudo ufw enable
```

**Do NOT add a UFW rule for port 18789.** Access the gateway via SSH tunnel or Tailscale only.

### fail2ban (SSH brute-force protection)

```bash
sudo apt install fail2ban unattended-upgrades -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Disable root SSH and password auth

Edit `/etc/ssh/sshd_config`:
```
PermitRootLogin no
PasswordAuthentication no
```

Then: `sudo systemctl restart sshd`

### Disable mDNS broadcasting

```bash
export OPENCLAW_DISABLE_BONJOUR=1
```

Or in `openclaw.json`:
```json
{ "discovery": { "mdns": { "mode": "off" } } }
```

## VPS-Specific Security Checklist

After deployment, verify ALL of these:

- [ ] Gateway bound to 127.0.0.1, NOT 0.0.0.0 (`ss -tlnp | grep 18789`)
- [ ] OpenClaw version is 2026.1.29+ (`openclaw --version`)
- [ ] Gateway auth token is set and strong (32+ hex chars)
- [ ] UFW enabled with only SSH allowed
- [ ] fail2ban running
- [ ] Root SSH disabled
- [ ] Password auth disabled (key-only)
- [ ] API spending limits set at provider console
- [ ] DM policy set to "pairing" (not "open")
- [ ] Tailscale or SSH tunnel for gateway access (no public port)
- [ ] mDNS disabled
- [ ] File permissions locked: `chmod 700 ~/.openclaw`, `chmod 600 ~/.openclaw/openclaw.json`
- [ ] `openclaw security audit --deep` passes clean

## Docker Network Isolation

For enhanced isolation, create a dedicated Docker network:

```yaml
# docker-compose.yml
services:
  openclaw-gateway:
    # ... existing config
    networks:
      - openclaw-net

networks:
  openclaw-net:
    driver: bridge
    internal: false  # Needs outbound for API calls
```

**Never mount `/var/run/docker.sock` into the OpenClaw container** — a container escape would grant full Docker control.

Consider **rootless Podman** as an alternative to Docker — a container escape lands as an unprivileged user (UID 1000), not root.

## Backup and Recovery

### Hostinger Automatic Backups

Enable daily auto-backups in hPanel during VPS purchase or in VPS settings. Hostinger retains backups for the plan's retention period.

### Manual Backup

```bash
# Backup OpenClaw config and state
docker compose exec openclaw-gateway tar -czvf /tmp/openclaw-backup.tar.gz -C /root .openclaw
docker cp openclaw-gateway:/tmp/openclaw-backup.tar.gz ./openclaw-backup-$(date +%F).tar.gz
```

### Recovery

```bash
# Fresh deploy, then restore config
docker compose down
docker compose up -d
docker cp ./openclaw-backup-YYYY-MM-DD.tar.gz openclaw-gateway:/tmp/
docker compose exec openclaw-gateway tar -xzvf /tmp/openclaw-backup-YYYY-MM-DD.tar.gz -C /root
docker compose restart
```

## Updating

```bash
docker compose pull
docker compose down
docker compose up -d
docker compose exec openclaw-gateway openclaw --version    # Verify
docker compose exec openclaw-gateway openclaw doctor       # Health check
```

## Alternative VPS Providers

This skill focuses on Hostinger, but OpenClaw also has official deployment support for:

- **DigitalOcean** — 1-Click Marketplace image, $6-12/month, $200 free credit for new accounts
- **Cloudflare Workers** — Experimental via `moltworker`, $5/month Workers Paid plan + compute
- **Emergent.sh** — Fully managed, no infrastructure knowledge required, 50 credits/month per app
