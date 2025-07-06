"""
Dopamine Clicker Backend API

This module defines core models and API endpoints for the idle clicking game.
Implements endpoints for:
- Click action (increment/calculate progress)
- Get/set game state
- Upgrade purchase
- Leaderboard retrieval
- Rewards claim

All endpoints are modular and ready for further extension.
"""

from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import uuid4
import httpx
import os
from dotenv import load_dotenv

# Load .env for API keys
load_dotenv()

app = FastAPI(
    title="Dopamine Clicker Backend",
    description="API for an addictive idle clicking game focused on progression, dopamine rewards, and leaderboards.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Game", "description": "Endpoints for playing the game"},
        {"name": "Upgrades", "description": "Upgrade actions"},
        {"name": "Leaderboard", "description": "Leaderboard endpoints"},
        {"name": "Rewards", "description": "Reward claiming endpoints"},
        {"name": "Integrations", "description": "3rd party API integrations for enrichment (News, Meme, Audius)"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock in-memory data for demonstration
USERS: Dict[str, "User"] = {}
GAMES: Dict[str, "GameState"] = {}
LEADERBOARD: List["LeaderboardEntry"] = []
UPGRADES: Dict[str, "Upgrade"] = {}
REWARDS: Dict[str, "RewardClaim"] = {}

############### MODELS ##################

# PUBLIC_INTERFACE
class User(BaseModel):
    """Represents a user/player in the game."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique User ID")
    username: str = Field(..., description="Username")
    total_clicks: int = Field(0, description="Total number of clicks by user")
    current_level: int = Field(1, description="Current progression level")
    dopamine_points: int = Field(0, description="Points to spend on upgrades/rewards")

# PUBLIC_INTERFACE
class Upgrade(BaseModel):
    """Represents an upgrade option in the game."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Upgrade ID")
    name: str = Field(..., description="Upgrade display name")
    description: Optional[str] = Field("", description="Description of the upgrade")
    cost: int = Field(..., ge=0, description="Upgrade cost in dopamine points")
    multiplier: float = Field(1.0, description="How much this upgrade increases dopamine or click rate")
    level_required: int = Field(1, ge=1, description="Level required for the upgrade")

# PUBLIC_INTERFACE
class GameState(BaseModel):
    """Represents a user's game state."""
    user_id: str = Field(..., description="Associated User ID")
    total_clicks: int = Field(0, description="Total clicks registered in session")
    dopamine_points: int = Field(0, description="Current dopamine points held")
    level: int = Field(1, description="Current level")
    upgrades: List[str] = Field(default_factory=list, description="List of Upgrade IDs owned")
    last_active: Optional[str] = Field(None, description="Last active timestamp, ISO8601 string")

# PUBLIC_INTERFACE
class LeaderboardEntry(BaseModel):
    """Represents a single leaderboard entry."""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    dopamine_points: int = Field(..., description="Current dopamine points")
    total_clicks: int = Field(..., description="Total clicks")
    level: int = Field(..., description="Player level")

# PUBLIC_INTERFACE
class RewardClaim(BaseModel):
    """Represents a claimable and/or claimed reward for a player."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Reward ID")
    user_id: str = Field(..., description="User who claims the reward")
    reward_type: str = Field(..., description="Type of Reward (e.g., 'daily_bonus', 'level_up')")
    claimed: bool = Field(False, description="Whether reward has been claimed")
    dopamine_points: int = Field(0, description="Rewarded dopamine points (if any)")
    timestamp_claimed: Optional[str] = Field(None, description="Claim timestamp (ISO8601 string)")

############### UTILITIES ##################

def get_fake_user(user_id: str) -> User:
    """Fetch user (in-memory for now)."""
    if user_id in USERS:
        return USERS[user_id]
    raise HTTPException(status_code=404, detail="User not found")

def get_fake_game_state(user_id: str) -> GameState:
    """Fetch game state (in-memory for now)."""
    if user_id in GAMES:
        return GAMES[user_id]
    raise HTTPException(status_code=404, detail="Game state not found")

def update_leaderboard():
    """Reorders leaderboard for top dopamine points and clicks."""
    global LEADERBOARD
    # In production, pull from the database and sort smartly
    entries = []
    for user in USERS.values():
        entries.append(LeaderboardEntry(
            user_id=user.id,
            username=user.username,
            dopamine_points=user.dopamine_points,
            total_clicks=user.total_clicks,
            level=user.current_level
        ))
    # Sort by: dopamine > clicks > level
    LEADERBOARD = sorted(entries, key=lambda e: (e.dopamine_points, e.total_clicks, e.level), reverse=True)[:50]

############### 3RD PARTY INTEGRATION MODELS ##################

# PUBLIC_INTERFACE
class NewsHeadline(BaseModel):
    """Single news headline from NewsAPI."""
    source_name: str
    author: Optional[str]
    title: str
    description: Optional[str]
    url: str
    urlToImage: Optional[str]
    publishedAt: str

# PUBLIC_INTERFACE
class MemeTemplate(BaseModel):
    """Meme template info from Imgflip."""
    id: str
    name: str
    url: str
    width: int
    height: int
    box_count: int

# PUBLIC_INTERFACE
class MemeCreateRequest(BaseModel):
    template_id: str = Field(..., description="ID of the Imgflip template.")
    top_text: str = Field(..., description="Text for the top of the meme.")
    bottom_text: str = Field(..., description="Text for the bottom of the meme.")

# PUBLIC_INTERFACE
class MemeCreateResponse(BaseModel):
    url: str = Field(..., description="URL of the generated meme image.")
    page_url: Optional[str] = Field(None, description="Optional page showing the meme.")

# PUBLIC_INTERFACE
class AudiusTrack(BaseModel):
    """A trending Audius track normalized for frontend."""
    id: str
    title: str
    artist: Optional[str]
    permalink: str
    artwork_url: Optional[str]

############### ENDPOINTS ##################

@app.get("/", tags=["Game"])
def health_check():
    """
    Health check endpoint.

    Returns message and service health status.
    """
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.get("/external/news_headlines", tags=["Integrations"], summary="Get news headlines", description="Fetch latest headlines from NewsAPI and return as normalized objects.")
async def get_news_headlines(
    q: str = Query("technology", description="Search topic (default: technology)"),
    language: str = Query("en", description="Language code (default: en)"),
    country: Optional[str] = Query(None, description="Optional country code"),
    max_results: int = Query(10, ge=1, le=100, description="Max headlines"),
):
    """
    Returns a list of top news headlines using NewsAPI (https://newsapi.org/).
    Parameters:
        - q: Use as news search
        - language: Language code
        - country: Optional country filter
        - max_results: Limit the number 
    """
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
    if not NEWSAPI_KEY:
        raise HTTPException(status_code=500, detail="NewsAPI key not set in environment.")
    url = "https://newsapi.org/v2/top-headlines"
    params = {"apiKey": NEWSAPI_KEY, "language": language, "pageSize": max_results, "q": q}
    if country:
        params["country"] = country
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=503, detail="Failed to fetch news headlines.")
        data = r.json()
        if "articles" not in data:
            raise HTTPException(status_code=502, detail="Invalid NewsAPI response.")
        headlines = []
        for art in data["articles"]:
            headlines.append(
                NewsHeadline(
                    source_name=art.get("source", {}).get("name", ""),
                    author=art.get("author"),
                    title=art.get("title", ""),
                    description=art.get("description"),
                    url=art.get("url", ""),
                    urlToImage=art.get("urlToImage"),
                    publishedAt=art.get("publishedAt", ""),
                )
            )
        return headlines

# PUBLIC_INTERFACE
@app.get(
    "/external/meme_templates",
    tags=["Integrations"],
    summary="Get meme templates (Imgflip)",
    description="Fetch popular meme templates from Imgflip for use in meme generation."
)
async def get_imgflip_templates(limit: int = Query(20, ge=1, le=100, description="Max templates")) -> List[MemeTemplate]:
    """
    Gets popular meme templates from the Imgflip API.
    - Returns meme templates for use in custom meme creation.
    """
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get("https://api.imgflip.com/get_memes")
        if resp.status_code != 200:
            raise HTTPException(status_code=503, detail="Imgflip API error")
        data = resp.json()
        if not data.get("success") or "memes" not in data.get("data", {}):
            raise HTTPException(status_code=502, detail="Invalid Imgflip API response")
        memes = [
            MemeTemplate(
                id=meme["id"],
                name=meme["name"],
                url=meme["url"],
                width=meme["width"],
                height=meme["height"],
                box_count=meme["box_count"]
            )
            for meme in data["data"]["memes"][:limit]
        ]
        return memes

# PUBLIC_INTERFACE
@app.post(
    "/external/create_meme",
    tags=["Integrations"],
    summary="Generate meme (Imgflip)",
    description="Generate a meme image using Imgflip meme generator."
)
async def create_imgflip_meme(req: MemeCreateRequest) -> MemeCreateResponse:
    """
    Generate a meme image using Imgflip (https://imgflip.com/api).
    Uses the official demo account as allowed by Imgflip API docs for testing.
    - template_id, top_text, bottom_text must be provided.
    """
    IMGFLIP_USERNAME = os.getenv("IMGFLIP_USERNAME", "imgflip_hubot")  # Default: demo
    IMGFLIP_PASSWORD = os.getenv("IMGFLIP_PASSWORD", "imgflip_hubot")
    payload = {
        "template_id": req.template_id,
        "username": IMGFLIP_USERNAME,
        "password": IMGFLIP_PASSWORD,
        "text0": req.top_text,
        "text1": req.bottom_text
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post("https://api.imgflip.com/caption_image", data=payload)
        if r.status_code != 200:
            raise HTTPException(status_code=503, detail="Imgflip meme generation error")
        data = r.json()
        if not data.get("success") or "url" not in data.get("data", {}):
            raise HTTPException(status_code=502, detail="Invalid Imgflip meme API response")
        return MemeCreateResponse(
            url=data["data"]["url"],
            page_url=data["data"].get("page_url")
        )

# PUBLIC_INTERFACE
@app.get(
    "/external/audius_trending",
    tags=["Integrations"],
    summary="Get trending tracks (Audius)",
    description="Fetch trending tracks from Audius for discoverable listening."
)
async def get_audius_trending(
    genre: Optional[str] = Query(None, description="Music genre filter"),
    limit: int = Query(10, ge=1, le=100, description="Max tracks")
) -> List[AudiusTrack]:
    """
    Fetch trending tracks from Audius (https://audius.co/api/docs).
    Parameters:
        - genre: Optional genre filter
        - limit: Limit to max tracks (default 10)
    """
    query = {"limit": limit}
    if genre:
        query["genre"] = genre
    async with httpx.AsyncClient(timeout=12.0) as client:
        r = await client.get("https://discoveryprovider.audius.io/v1/tracks/trending", params=query)
        if r.status_code != 200:
            raise HTTPException(status_code=503, detail="Audius trending fetch error")
        data = r.json()
        if "data" not in data:
            raise HTTPException(status_code=502, detail="Invalid Audius response")
        results = [
            AudiusTrack(
                id=tr["id"],
                title=tr["title"],
                artist=(tr["user"]["name"] if isinstance(tr.get("user"), dict) else None),
                permalink=tr.get("permalink", ""),
                artwork_url=(tr.get("artwork", {}).get("150x150") if isinstance(tr.get("artwork"), dict) else None)
            )
            for tr in data["data"][:limit]
        ]
        return results

# --- Modularization Note ---
# For production: Move models to `models.py`, implement persistent DB layer, add authentication, etc.

