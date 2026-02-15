from typing import List, Optional
import os
import time

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import httpx

app = FastAPI(title="Trending Live Streams (Gaming)")


class StreamItem(BaseModel):
    user_name: str
    title: str
    viewer_count: int
    language: Optional[str]
    thumbnail_url: Optional[str]


# Simple in-memory token cache
_twitch_token = {"token": None, "expires_at": 0}


def _get_twitch_token(client_id: str, client_secret: str) -> Optional[str]:
    now = int(time.time())
    if _twitch_token["token"] and _twitch_token["expires_at"] - 60 > now:
        return _twitch_token["token"]

    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    try:
        r = httpx.post(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        expires_in = int(data.get("expires_in", 0))
        if token:
            _twitch_token["token"] = token
            _twitch_token["expires_at"] = int(time.time()) + expires_in
            return token
    except Exception:
        return None


def _fetch_twitch_streams(limit: int = 10, game_name: Optional[str] = None) -> List[StreamItem]:
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("No Twitch credentials configured")

    token = _get_twitch_token(client_id, client_secret)
    if not token:
        raise RuntimeError("Failed to obtain Twitch access token")

    headers = {"Client-Id": client_id, "Authorization": f"Bearer {token}"}

    params = {"first": str(min(limit, 100))}
    # If game_name provided, resolve game id
    if game_name:
        try:
            r = httpx.get("https://api.twitch.tv/helix/games", params={"name": game_name}, headers=headers, timeout=10)
            r.raise_for_status()
            games = r.json().get("data", [])
            if games:
                params["game_id"] = games[0]["id"]
        except Exception:
            # ignore and fetch top streams overall
            pass

    r = httpx.get("https://api.twitch.tv/helix/streams", params=params, headers=headers, timeout=10)
    r.raise_for_status()
    streams = r.json().get("data", [])

    out = []
    for s in streams[:limit]:
        out.append(
            StreamItem(
                user_name=s.get("user_name"),
                title=s.get("title"),
                viewer_count=s.get("viewer_count", 0),
                language=s.get("language"),
                thumbnail_url=s.get("thumbnail_url"),
            )
        )
    return out


def _mock_streams(limit: int = 10) -> List[StreamItem]:
    sample = []
    for i in range(limit):
        sample.append(
            StreamItem(
                user_name=f"Streamer{i+1}",
                title=f"Exciting gameplay session #{i+1}",
                viewer_count=1000 - i * 50,
                language="en",
                thumbnail_url=None,
            )
        )
    return sample


@app.get("/trending", response_model=List[StreamItem])
def trending(limit: int = Query(10, ge=1, le=100), game: Optional[str] = Query(None)):
    """Return top trending livestreaming channels for gaming.

    By default this returns mock data. Set `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET`
    environment variables to enable real Twitch data (Helix API). Optional `game` parameter
    attempts to filter by game name.
    """
    try:
        client_id = os.getenv("TWITCH_CLIENT_ID")
        client_secret = os.getenv("TWITCH_CLIENT_SECRET")
        if client_id and client_secret:
            return _fetch_twitch_streams(limit=limit, game_name=game)
        else:
            return _mock_streams(limit=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RuntimeError as e:
        # fallback to mock data if Twitch fails
        return _mock_streams(limit=limit)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, log_level="info")
