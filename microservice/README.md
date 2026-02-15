# Trending Live Streams Microservice

This small FastAPI microservice returns a list of top trending livestreaming channels for gaming.

Features:

- `/trending` endpoint returns a JSON list of channels (mock data by default).
- If you set `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` environment variables, the service will call the Twitch Helix API to return real streams.

Quick start (local):

1. From the microservice folder:

```bash
cd testContainer/microservice
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

2. Hit the endpoint:

```
GET http://localhost:8000/trending
```

Use `?limit=20` or `?game=Fortnite` to adjust results.

Using Twitch API (optional):

1. Create a Twitch application and get `client_id` and `client_secret` at https://dev.twitch.tv/.
2. Export variables:

```bash
export TWITCH_CLIENT_ID=your_id
export TWITCH_CLIENT_SECRET=your_secret
uvicorn app:app --reload
```

Docker:

```bash
docker build -t trending-ms .
docker run --rm -p 8000:8000 trending-ms
```

Notes:
- The service uses mock data if no Twitch credentials are present — good for development and demos.
- The Twitch Helix API requires a client credentials token; the microservice performs that exchange automatically when credentials are present.
