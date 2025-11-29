# Share the REDAI app through Nginx

Use this guide to expose your locally running REDAI stack through a disposable public URL so that teammates can try the app remotely.

## 1. Prerequisites
- Docker Desktop (or any engine that supports `docker compose`)
- Backend services running locally (use `start_production.bat`, which now launches the Settings API on port 5003 as well)
- Frontend bundle built once with:
  ```
  cd front
  npm install
  npm run build
  ```

## 2. What the sharing stack does
- `redai-nginx` serves the contents of `front/dist` and reverse-proxies to the locally running APIs via `host.docker.internal`.
- `share-tunnel` (Cloudflare Tunnel, using the `cloudflare/cloudflared:latest` image) publishes Nginx to the internet and prints a `https://*.trycloudflare.com` link in the logs.

## 3. Start sharing
From the project root (`C:\Users\Avinash\OneDrive\Desktop\REDAI`):
```
docker compose -f docker-compose.share.yml up
```

Watch the `share-tunnel` logs; once you see a line similar to:
```
INF | Your quick Tunnel has started! Visit it at https://<random>.trycloudflare.com
```
share that URL with collaborators. The link stays active while the compose stack is running.

## 4. Stop sharing
Press `Ctrl+C` in the compose terminal or run:
```
docker compose -f docker-compose.share.yml down
```

## 5. Troubleshooting
- **Blank page/404** – ensure `front/dist` exists and rebuild if necessary.
- **APIs unreachable** – confirm `start_production.bat` (or equivalent) is running so the services are listening on ports `8080`, `5001`, and `5002`.
- **Port 8088 already in use** – edit `docker-compose.share.yml` and change the host port mapping under `redai-nginx`.
- **Need a custom domain** – switch from quick tunnels to an authenticated Cloudflare Tunnel and update the `share-tunnel` service command accordingly.

