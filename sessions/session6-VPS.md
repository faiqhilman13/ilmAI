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

### what’s left / next steps

1) Run the backend API on the VPS
   - Recommended: bind backend to `127.0.0.1:8000` and put a reverse proxy (Caddy/Nginx) on `443`.
   - Configure `backend/.env`:
     - `OPENAI_API_KEY`
     - `DATABASE_URL=postgresql+asyncpg://ilmuai_admin:secret123@localhost:5432/ilmuai`
     - `REDIS_URL=redis://localhost:6379/0`
     - `CORS_ORIGINS` to your Netlify domain

2) Add HTTPS and expose only ports 80/443 publicly
   - Use a temporary domain like `46.224.20.19.sslip.io` (or a real domain later).
   - Reverse proxy `https://<domain>` → `http://127.0.0.1:8000`.

3) Deploy frontend on Netlify and point it at the HTTPS API
   - Set frontend env `VITE_API_URL=https://<domain>/api`.

4) (Optional) Dockerize backend in production compose
   - Current `docker/docker-compose.yml` is infra-only.
   - Add `backend` + `caddy` services for one-command deployment.

5) (Optional) Finish embedding the remaining fiqh corpus
   - Not required for VPS migration, but still pending from Session 5.
   - This can be done from any machine as long as it writes into the VPS Postgres.
