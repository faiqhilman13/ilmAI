## session 6 — VPS deployment (Hetzner)

### goal

Move the existing IlmuAI stack to a VPS (Docker-based) without re-downloading/re-processing/re-embedding data, by migrating the existing local Postgres (pgvector) database into the VPS.

### what we did

- Provisioned a Hetzner server (Ubuntu 24.04) and set up SSH key auth.
- Created inbound firewall rules (recommended):
  - Allow `22/tcp` (SSH) from your public IP
  - Allow `80/tcp` and `443/tcp` from the internet
  - Keep `5432/tcp` (Postgres) and `6379/tcp` (Redis) closed to the public
- Installed Docker + Docker Compose plugin on the VPS.
- Cloned repo to the VPS:
  - `/opt/ilmuai`
- Started infra containers using `docker/docker-compose.yml`:
  - `ilmuai-postgres` (pgvector/pg16)
  - `ilmuai-redis`
  - `ilmuai-pgadmin`

### database migration (important)

Initial restore attempt failed because the VPS Postgres container automatically initialized schema from:

- `backend/sql/schema.sql` mounted into `/docker-entrypoint-initdb.d/01-schema.sql`

So restoring a **full pg_dump** (schema + data) caused “already exists” errors and foreign key violations.

Fix: use a **data-only dump** from local and restore into VPS (schema already exists).

Local (Mac) dump:
- `pg_dump --data-only --column-inserts` → `ilmuai_data.sql`

Transfer:
- `scp` the dump to the VPS: `/root/ilmuai_data.sql`

VPS restore:
- `psql` into the running `ilmuai-postgres` container and restored data-only dump.

Result:
- VPS `knowledge_chunks` counts match local DB.

### current state

- VPS infrastructure containers are running (Postgres/Redis/pgAdmin).
- Database is migrated; embeddings and vectors are present on VPS.
- Backend is running on the VPS (Python venv) bound to `127.0.0.1:8000` inside a `tmux` session.
- Caddy is installed and serving HTTPS:
  - `https://46.224.20.19.sslip.io` → reverse proxy to `127.0.0.1:8000`
  - Verified `GET https://46.224.20.19.sslip.io/health` returns `200`.

### what’s left / next steps

1) Deploy frontend on Netlify and point it at the HTTPS API
   - Netlify env: `VITE_API_URL=https://46.224.20.19.sslip.io/api`
   - Ensure backend `CORS_ORIGINS` includes the Netlify site URL.

2) Make backend process persistent (recommended)
   - `tmux` works for now, but consider a `systemd` service for auto-restart on reboot.

3) (Optional) Dockerize backend + Caddy (one-command deploy)
   - Current `docker/docker-compose.yml` is infra-only.
   - Add `backend` + `caddy` services for one-command deployment + env management.

4) (Optional) Finish embedding remaining fiqh corpus
   - Not required for VPS migration, but still pending from Session 5.
   - Can be done on any machine as long as it writes into the VPS Postgres.

### can we delete local data?

Yes, once you’ve verified the VPS is your source of truth:

- Keep locally (recommended minimum):
  - The git repo (code)
  - Your SSH private key: `~/.ssh/ilmuai_hetzner`
  - A Postgres dump backup (optional but recommended)

- You can turn off local Docker and remove local DB volumes if:
  - The VPS Postgres has the correct counts and app answers look correct.
  - You have at least one backup dump stored somewhere safe.

Suggested safety checklist before deleting local data:
1) VPS DB counts match local (done).
2) `GET https://46.224.20.19.sslip.io/health` works (done).
3) Run 3–5 test prompts in the app and confirm citations work.
4) Take a VPS backup dump:
   - `docker exec -i ilmuai-postgres pg_dump -U ilmuai_admin -d ilmuai > /root/ilmuai_backup.sql`
   - Download it to your Mac or store in cloud storage.

---

## noob ops guide (SSH + tmux + services)

### SSH in / out

- SSH into the VPS:
  ```bash
  ssh -i ~/.ssh/ilmuai_hetzner root@46.224.20.19
  ```
- Exit the SSH session (does not stop the server):
  ```bash
  exit
  ```

### tmux basics (backend runs inside tmux)

- List tmux sessions:
  ```bash
  tmux ls
  ```
- Attach to the backend session:
  ```bash
  tmux attach -t ilmuai
  ```
- Detach (leave it running in background):
  - Press `Ctrl+b` then `d`

### Start / stop backend (uvicorn)

Assumption: backend runs in tmux session `ilmuai` and listens on `127.0.0.1:8000`.

- Start backend in tmux (creates session if missing):
  ```bash
  tmux new -d -s ilmuai 'bash -lc "cd /opt/ilmuai/backend && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000"'
  ```
- Check backend health:
  ```bash
  curl -s http://127.0.0.1:8000/health
  curl -s https://46.224.20.19.sslip.io/health
  ```
- Stop backend (kill tmux session):
  ```bash
  tmux kill-session -t ilmuai
  ```
- If you’re attached to tmux and want to stop uvicorn gracefully:
  - Press `Ctrl+C` inside the tmux pane, then detach (`Ctrl+b`, `d`)

### Caddy (HTTPS reverse proxy)

- Caddy status:
  ```bash
  systemctl status caddy --no-pager
  ```
- Reload after editing `/etc/caddy/Caddyfile`:
  ```bash
  systemctl reload caddy
  ```
- View logs:
  ```bash
  journalctl -u caddy -n 100 --no-pager
  ```

### Docker (DB/Redis)

- Show containers:
  ```bash
  cd /opt/ilmuai/docker
  docker ps
  ```
- Start infra services:
  ```bash
  cd /opt/ilmuai/docker
  docker compose up -d
  ```
- Stop infra services:
  ```bash
  cd /opt/ilmuai/docker
  docker compose down
  ```

### Common “where is my config?”

- Backend env file:
  - `/opt/ilmuai/backend/.env`
- Caddy config:
  - `/etc/caddy/Caddyfile`
