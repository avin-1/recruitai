---
description: How to deploy the REDAI application on Nginx (Windows/Linux)
---

# Deploying REDAI on Nginx

This workflow guides you through deploying the REDAI application using Nginx as a reverse proxy and static file server.

## Prerequisites
- **Node.js** and **npm** installed.
- **Python** installed.
- **Nginx** installed.
  - Windows: Download from [nginx.org](http://nginx.org/en/download.html).
  - Linux: `sudo apt install nginx`

## Steps

### 1. Build the Frontend
Compile the React application into static files.

```bash
cd front
npm install
npm run build
```
This will create a `dist` folder in `front/`.

### 2. Configure Nginx
1.  Locate your Nginx configuration file (`nginx.conf`).
    - Windows: Usually in the `conf` folder inside the Nginx directory.
    - Linux: `/etc/nginx/nginx.conf` or `/etc/nginx/sites-available/default`.
2.  Copy the contents of `nginx.conf.example` (located in the project root) into your `nginx.conf`.
3.  **IMPORTANT**: Update the `root` directive in the `server` block to point to the absolute path of your `front/dist` folder.
    - Example (Windows): `root "C:/Users/Avinash/OneDrive/Desktop/REDAI/front/dist";`
    - Example (Linux): `root /var/www/redai/front/dist;`

### 3. Start Backend Services
Use the production startup script to run the Python backend services.

**Windows:**
```cmd
start_production.bat
```

**Linux:**
You will need to create a systemd service or use a process manager like `supervisor` or `pm2` to run the equivalent of:
- `waitress-serve --port=8080 --call backend.upload_api:app`
- `waitress-serve --port=5001 --call agents.shortlisting.api:app`
- `waitress-serve --port=5002 --call agents.interview.api:app`

### 4. Start/Reload Nginx
**Windows:**
```cmd
cd /path/to/nginx
start nginx
```
If already running: `nginx -s reload`

**Linux:**
```bash
sudo systemctl restart nginx
```

### 5. Verify Deployment
Open your browser and navigate to `http://localhost` (or your server's IP).
- The frontend should load.
- API requests should work (proxied to the backend services).
