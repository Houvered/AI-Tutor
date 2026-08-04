# Deployment Guide

How to put StudyMate online so you can use it from any device. The project runs
as one normal Python process, so there is no special hosting required.

## The simple way: a small virtual private server (VPS)

Any VPS with 1 CPU, 1 GB RAM, and about 1 GB of disk is enough. Good options:
Hetzner, DigitalOcean, Vultr, Contabo, or your own machine if you keep it on.

### 1. Prepare the server

```
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx nodejs npm
```

### 2. Get the code

```
git clone https://github.com/<your-account>/AI-Tutor.git
cd AI-Tutor
```

### 3. Install the backend

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 4. Set the environment

Create the `.env` file:

```
nano .env
```

Fill in your provider settings (see `docs/setup.md`).

### 5. Build the frontend

```
cd frontend
npm install
npm run build
cd ..
```

### 6. Run the app with a process manager

Install systemd or use a simple tool like `nohup`. The easiest reliable way is
a systemd service:

```
sudo nano /etc/systemd/system/studymate.service
```

With this content (change the paths to match your setup):

```
[Unit]
Description=StudyMate
After=network.target

[Service]
WorkingDirectory=/home/<user>/AI-Tutor
ExecStart=/home/<user>/AI-Tutor/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:

```
sudo systemctl daemon-reload
sudo systemctl enable studymate
sudo systemctl start studymate
```

Check it with: `curl http://127.0.0.1:8000/api/health`

### 7. Put nginx in front (for HTTPS and a real domain)

Create `/etc/nginx/sites-available/studymate`:

```
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable it:

```
sudo ln -s /etc/nginx/sites-available/studymate /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

For HTTPS, install certbot (`sudo apt install certbot python3-certbot-nginx`)
and run `sudo certbot --nginx -d yourdomain.com`.

## Hosting platforms (no VPS management)

StudyMate is a plain Python web app, so it also runs on services like:

- Render (free tier): set the start command to
  `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`, set the env vars in
  the dashboard, and set the build command to `cd frontend && npm install && npm run build`.
- Railway, Fly.io, and similar: same idea, one web service plus env vars.

You must set the four environment variables on the platform: `LLM_BASE_URL`,
`LLM_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` (or the Gemini ones with
`LLM_PROVIDER=gemini`).

## Optional: protect the app with a simple password

StudyMate has no user accounts by default. If you expose it publicly and you
are the only user, add a small secret token. One simple way is a reverse proxy
basic auth with nginx. Add to the server block:

```
auth_basic "Restricted";
auth_basic_user_file /etc/nginx/.htpasswd;
```

Create the password file with `sudo apt install apache2-utils` and then
`sudo htpasswd -c /etc/nginx/.htpasswd yourname`.

## Backup

All data lives in one file: `data/study.db`. Back up that single file.

## Checking that everything works

After deployment visit:

- `https://yourdomain.com/` - the web app.
- `https://yourdomain.com/api/health` - shows status and whether the LLM is connected.