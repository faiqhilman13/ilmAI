# VPS info (IlmuAI)

This is a practical “ops cheat sheet” for the IlmuAI VPS setup (SSH + tmux + Caddy + Docker + Git).

## Basics

### VPS details
- VPS IP: `46.224.20.19`
- Public API base: `https://46.224.20.19.sslip.io`
- API endpoints are under: `https://46.224.20.19.sslip.io/api`

### SSH key used
- Private key on your Mac: `~/.ssh/ilmuai_hetzner`
- Public key (what you paste into providers / `authorized_keys`): `~/.ssh/ilmuai_hetzner.pub`

---

## SSH: connect / disconnect

### SSH in (from your Mac/Linux)
```bash
ssh -i ~/.ssh/ilmuai_hetzner root@46.224.20.19
```

### SSH out
- Type `exit` and press Enter, or press `Ctrl+D`.

### “I’m already on the VPS”
Your prompt looks like:
`root@ubuntu-4gb-nbg1-1-ilmuai:~#`

When you see that, **do not** run `ssh root@46.224.20.19 ...` again (you’re already there).

---

## tmux: keep backend running

### List sessions
```bash
tmux ls
```

### Attach to the backend session
```bash
tmux attach -t ilmuai
```

### Detach (leave running in background)
- Press `Ctrl+b`, then press `d`

### Kill the backend session
```bash
tmux kill-session -t ilmuai
```

### Start backend in a tmux session (recommended pattern)
```bash
tmux new -d -s ilmuai 'bash -lc "cd /opt/ilmuai/backend && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000"'
```

### View recent backend logs (without attaching)
```bash
tmux capture-pane -t ilmuai -pS -200
```

---

## Caddy (HTTPS reverse proxy)

### Check caddy status
```bash
systemctl status caddy --no-pager
```

### View caddy logs
```bash
journalctl -u caddy -n 100 --no-pager
```

### Reload caddy after config changes
```bash
systemctl reload caddy
```

### Caddy config location
- `/etc/caddy/Caddyfile`

Current pattern:
```caddyfile
46.224.20.19.sslip.io {
  reverse_proxy 127.0.0.1:8000
}
```

---

## Backend health checks

### Local (from VPS)
```bash
curl -v http://127.0.0.1:8000/health
```

### Public (from anywhere)
```bash
curl -v https://46.224.20.19.sslip.io/health
```

If local works but public doesn’t:
- check caddy logs (`journalctl -u caddy`)
- check firewall ports 80/443

---

## Backend config (.env)

### Where it lives
- `/opt/ilmuai/backend/.env`

### Edit it
```bash
nano /opt/ilmuai/backend/.env
```

### Nano save/exit
- Save: `Ctrl+O` then `Enter`
- Exit: `Ctrl+X`

### IMPORTANT
If you change `.env`, you must restart backend (tmux kill + tmux new) for changes to apply.

---

## Docker (Postgres + Redis + pgAdmin)

### Where compose lives
- `/opt/ilmuai/docker/docker-compose.yml`

### Start / stop containers
```bash
cd /opt/ilmuai/docker
docker compose up -d
docker compose ps
docker compose logs -n 100 postgres
docker compose logs -n 100 redis
docker compose logs -n 100 pgadmin
```

### Exec into Postgres container
```bash
cd /opt/ilmuai/docker
docker compose exec -T postgres psql -U ilmuai_admin -d ilmuai
```

### Check Postgres env vars (useful for DB URL)
```bash
cd /opt/ilmuai/docker
docker compose exec -T postgres printenv | egrep 'POSTGRES_(USER|PASSWORD|DB)'
```

### DB URL that must match Postgres env
Example from this setup:
```env
DATABASE_URL=postgresql+asyncpg://ilmuai_admin:secret123@localhost:5432/ilmuai
```

---

## Git: update code on VPS

### Pull latest code
```bash
cd /opt/ilmuai
git pull
```

If you pull new backend changes, restart tmux backend session.

---

## Debug checklist (when something breaks)

### 1) Is backend running?
```bash
tmux ls
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
```

### 2) Is caddy working?
```bash
systemctl status caddy --no-pager
journalctl -u caddy -n 50 --no-pager
curl -s -o /dev/null -w "%{http_code}\n" https://46.224.20.19.sslip.io/health
```

### 3) Is Postgres up?
```bash
cd /opt/ilmuai/docker
docker compose ps
docker compose logs -n 50 postgres
```

### 4) What does the backend say?
```bash
tmux capture-pane -t ilmuai -pS -200
```

---

## Using the VPS from a different PC

### Option A (recommended): create a new SSH key per machine
On each new machine, generate a new key and add it to the server:

**Mac/Linux:**
```bash
ssh-keygen -t ed25519 -C "ilmuai-<machine-name>" -f ~/.ssh/ilmuai_hetzner_<machine-name>
cat ~/.ssh/ilmuai_hetzner_<machine-name>.pub
```

Then append the public key to the server:
```bash
ssh -i ~/.ssh/ilmuai_hetzner root@46.224.20.19
mkdir -p /root/.ssh
nano /root/.ssh/authorized_keys
```

Paste the entire `ssh-ed25519 AAAA... comment` line on a new line, save, exit.

Now SSH from that machine with:
```bash
ssh -i ~/.ssh/ilmuai_hetzner_<machine-name> root@46.224.20.19
```

### Option B: reuse the same private key on multiple machines
This works but is weaker security.
- Copy the private key file (`ilmuai_hetzner`) to the new machine securely.
- Keep it secret. Anyone with the private key can access your server.

### Windows notes
Best path: **WSL (Ubuntu)** on Windows.
- Put the key inside WSL under `~/.ssh/`
- `chmod 600 ~/.ssh/<keyfile>`
- Use the normal `ssh -i ...` command.

If you use native Windows OpenSSH or PuTTY, the permissions/key formats differ.

---

## Power down / costs

- Powering off the VPS stops compute billing, but the IP/volumes behavior depends on provider plan.
- If the VPS is off, your Netlify frontend loads but API calls fail until the VPS is back on.

