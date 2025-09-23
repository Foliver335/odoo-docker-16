# odoo-docker-16
# Odoo 16 Community on WSL2 with Docker

> Quick-start project to run **Odoo 16 Community** on **Windows via WSL2 (Ubuntu)** using **Docker + Docker Compose**.

Repo URL (SSH): `git@github.com:Foliver335/odoo-docker-16.git`

---

## TL;DR (Quick Start)

```bash
# 1) Clone (in WSL Ubuntu)
git clone git@github.com:Foliver335/odoo-docker-16.git
cd odoo-docker-16

# 2) Create project folders (if not present)
mkdir -p addons config filestore postgres-data

# 3) Create .env (edit values as needed)
cat > .env <<'EOF'
POSTGRES_DB=postgres
POSTGRES_USER=odoo
POSTGRES_PASSWORD=odoo
ADMIN_PASSWORD=admin
ODOO_PORT=8069
TZ=America/Sao_Paulo
EOF

# 4) (Optional) odoo.conf
cat > config/odoo.conf <<'EOF'
[options]
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
log_level = info
EOF

# 5) Validate and start
docker compose config
docker compose up -d

# 6) Access
# Open in your browser:
# http://localhost:8069
```

---

## Requirements

- **Windows 10/11** with **WSL2** and **Ubuntu** installed.
- Either:
  - **Docker Desktop** (recommended), with **WSL integration** enabled, **or**
  - **Docker Engine + Compose** installed directly inside WSL2 (systemd enabled).

### Option A — Docker Desktop (recommended)
1. Install Docker Desktop in **Windows** (PowerShell):
   ```powershell
   winget install -e --id Docker.DockerDesktop
   ```
   If `winget` is missing, install **App Installer** from Microsoft Store.
2. Open Docker Desktop → **Settings › Resources › WSL Integration** → enable Ubuntu.
3. Use the **WSL Ubuntu** terminal for the rest of the commands.

### Option B — Docker Engine inside WSL
Enable `systemd`, add Docker repo, and install:
```bash
echo -e "[boot]\nsystemd=true" | sudo tee /etc/wsl.conf
# In Windows PowerShell:
# wsl --shutdown
# Reopen Ubuntu:
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --yes --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) stable" \
| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
sudo systemctl enable --now docker
docker version && docker compose version
```

---

## Project Structure

```
odoo-docker-16/
├─ addons/           # your custom modules (mounted at /mnt/extra-addons)
├─ config/           # odoo.conf (mounted at /etc/odoo)
├─ filestore/        # filestore & attachments (mounted at /var/lib/odoo)
├─ postgres-data/    # Postgres data dir
├─ .env              # environment variables
└─ docker-compose.yml
```

---

## `docker-compose.yml`

> This repo expects a `docker-compose.yml` like below. If your copy is missing, create it:

```yaml
services:
  db:
    image: postgres:14
    container_name: odoo16-db
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      TZ: ${TZ}
    volumes:
      - ./postgres-data:/var/lib/postgresql/data/pgdata
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  odoo:
    image: odoo:16.0
    container_name: odoo16-web
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    env_file: .env
    environment:
      DB_HOST: db
      DB_PORT: "5432"
      DB_USER: ${POSTGRES_USER}
      DB_PASSWORD: ${POSTGRES_PASSWORD}
      TZ: ${TZ}
    ports:
      - "${ODOO_PORT}:8069"
    volumes:
      - ./addons:/mnt/extra-addons
      - ./filestore:/var/lib/odoo
      - ./config:/etc/odoo
    command: ["--dev=reload"]
```

> Why these envs? Odoo reads **DB_HOST/DB_PORT/DB_USER/DB_PASSWORD**. Using `odoo.conf` is also supported and often cleaner for production.

---

## Day-to-Day Commands

```bash
# Status & logs
docker compose ps
docker compose logs -f odoo
docker logs -f odoo16-web

# Open a shell inside Odoo
docker compose exec odoo bash

# Fix permissions (if you see 'Permission denied' in logs)
docker compose exec -u root odoo bash -lc \
'chown -R odoo:odoo /mnt/extra-addons /var/lib/odoo /etc/odoo || true'
docker compose restart odoo

# Install a custom module
# Put your module under ./addons/MY_MODULE first
docker compose exec odoo odoo -i MY_MODULE -d YOUR_DB --stop-after-init
docker compose restart odoo

# Upgrade a module
docker compose exec odoo odoo -u MY_MODULE -d YOUR_DB --stop-after-init
docker compose restart odoo
```

---

## Backup & Restore

```bash
# Backup Postgres (replace YOUR_DB)
docker compose exec -T odoo16-db pg_dump -U "$POSTGRES_USER" -Fc -d YOUR_DB > backup_YOUR_DB_$(date +%F).dump

# Backup filestore
tar -czf filestore_$(date +%F).tar.gz filestore

# Restore Postgres
docker compose exec -T odoo16-db pg_restore -U "$POSTGRES_USER" -d YOUR_DB < backup_YOUR_DB_YYYY-MM-DD.dump

# Restore filestore
tar -xzf filestore_YYYY-MM-DD.tar.gz
```

---

## Troubleshooting

- **Internal Server Error** in browser
  - Check Odoo logs: `docker compose logs -f odoo`
  - Common causes:
    - Wrong DB env vars → ensure `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD`
    - Permissions on `filestore/` or `addons/` → run the `chown` above
    - Postgres not healthy → check `docker compose logs -f db`

- **Port 8069 in use** → change `ODOO_PORT` in `.env` (e.g., `8070`) and `docker compose up -d`.

- **Slow performance on WSL** → increase WSL resources in `C:\Users\<YOU>\.wslconfig`:
  ```ini
  [wsl2]
  memory=6GB
  processors=4
  ```
  Then in PowerShell: `wsl --shutdown` and reopen Ubuntu.

---

## Contributing

PRs are welcome. Please keep the compose, env, and docs coherent and tested on WSL2.

---

## License

MIT (or your project’s license). Update this section as needed.


