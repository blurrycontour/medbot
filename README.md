# medbot

```bash
# dev
docker compose build
docker compose up
docker push blurrycontour/medbot:app

# release
docker pull blurrycontour/medbot:app
docker compose up -d

## database
docker compose pull
docker compose --env-file=../.env up -d
```
