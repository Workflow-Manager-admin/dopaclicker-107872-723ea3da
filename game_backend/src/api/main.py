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

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import uuid4

app = FastAPI(
    title="Dopamine Clicker Backend",
    description="API for an addictive idle clicking game focused on progression, dopamine rewards, and leaderboards.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Game", "description": "Endpoints for playing the game"},
        {"name": "Upgrades", "description": "Upgrade actions"},
        {"name": "Leaderboard", "description": "Leaderboard endpoints"},
        {"name": "Rewards", "description": "Reward claiming endpoints"},
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

############### ENDPOINTS ##################

@app.get("/", tags=["Game"])
def health_check():
    """
    Health check endpoint.

    Returns message and service health status.
    """
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.post("/click", tags=["Game"], summary="Register a click", description="Increment clicks and return updated game state.")
def click(user_id: str = Body(..., embed=True)) -> GameState:
    """
    Registers a click action for the given user, increases dopamine points, and returns the updated game state.

    - **user_id**: ID of the user performing the click.
    Returns the updated GameState.
    """
    user = get_fake_user(user_id)
    game = get_fake_game_state(user_id)
    # Apply upgrades, etc. (fake logic)
    click_value = 1.0
    for upg_id in game.upgrades:
        upg = UPGRADES.get(upg_id)
        if upg:
            click_value *= upg.multiplier
    # Update state
    game.total_clicks += int(click_value)
    game.dopamine_points += int(click_value)
    user.total_clicks = game.total_clicks
    user.dopamine_points = game.dopamine_points
    GAMES[user_id] = game
    USERS[user_id] = user
    update_leaderboard()
    return game

# PUBLIC_INTERFACE
@app.get("/game_state", tags=["Game"], summary="Get a user's game state", description="Returns the latest game state for provided user.")
def get_game_state(user_id: str) -> GameState:
    """
    Fetches the game state for a given user.

    - **user_id**: ID of the user
    """
    return get_fake_game_state(user_id)

# PUBLIC_INTERFACE
@app.post("/game_state", tags=["Game"], summary="Set game state", description="Allows setting/replacing the full game state for a user.")
def set_game_state(state: GameState) -> GameState:
    """
    Sets the provided game state for a user (overwrites existing).

    - **state**: GameState object
    """
    GAMES[state.user_id] = state
    user = USERS.get(state.user_id)
    if user:
        user.total_clicks = state.total_clicks
        user.dopamine_points = state.dopamine_points
        user.current_level = state.level
        USERS[user.id] = user
    update_leaderboard()
    return state

# PUBLIC_INTERFACE
@app.post("/upgrade/purchase", tags=["Upgrades"], summary="Purchase upgrade", description="Buy an upgrade using dopamine points.")
def purchase_upgrade(
    user_id: str = Body(..., embed=True),
    upgrade_id: str = Body(..., embed=True),
) -> GameState:
    """
    Purchases an upgrade for the user if requirements and dopamine points are met.

    - **user_id**: User ID
    - **upgrade_id**: Upgrade ID
    Returns updated GameState
    """
    user = get_fake_user(user_id)
    game = get_fake_game_state(user_id)
    upgrade = UPGRADES.get(upgrade_id)
    if not upgrade:
        raise HTTPException(status_code=404, detail="Upgrade not found")
    if upgrade.id in game.upgrades:
        raise HTTPException(status_code=400, detail="Upgrade already owned")
    if upgrade.cost > game.dopamine_points:
        raise HTTPException(status_code=400, detail="Not enough dopamine points")
    if user.current_level < upgrade.level_required:
        raise HTTPException(status_code=400, detail="Level not high enough")
    # Purchase it!
    game.dopamine_points -= upgrade.cost
    game.upgrades.append(upgrade.id)
    user.dopamine_points = game.dopamine_points
    GAMES[user_id] = game
    USERS[user_id] = user
    return game

# PUBLIC_INTERFACE
@app.get("/leaderboard", tags=["Leaderboard"], summary="Get leaderboard", description="Fetch current leaderboard standings (top 50).")
def get_leaderboard() -> List[LeaderboardEntry]:
    """
    Returns the current leaderboard sorted by dopamine points and clicks.
    """
    update_leaderboard()
    return LEADERBOARD

# PUBLIC_INTERFACE
@app.post("/reward/claim", tags=["Rewards"], summary="Claim a reward", description="Claim a dopamine reward for user.")
def claim_reward(
    user_id: str = Body(..., embed=True),
    reward_type: str = Body(..., embed=True)
) -> RewardClaim:
    """
    Claims a specified reward for a user (if available).

    - **user_id**: User ID
    - **reward_type**: Type of reward ('daily_bonus', etc.)

    Returns RewardClaim object.
    """
    key = f"{user_id}_{reward_type}"
    if key in REWARDS and REWARDS[key].claimed:
        raise HTTPException(status_code=400, detail="Reward already claimed")
    # Fake: award random dopamine (can be more clever!)
    reward = RewardClaim(
        user_id=user_id,
        reward_type=reward_type,
        claimed=True,
        dopamine_points=20  # Demo
    )
    REWARDS[key] = reward
    user = get_fake_user(user_id)
    user.dopamine_points += reward.dopamine_points
    USERS[user.id] = user
    game = get_fake_game_state(user_id)
    game.dopamine_points = user.dopamine_points
    GAMES[user_id] = game
    return reward

# --- Example Data Initialization (for testing/local dev) ---
@app.on_event("startup")
def initialize_example_data():
    """Seeds demo users, upgrades for standalone testing."""
    # Only add if not present
    if not USERS:
        u1 = User(username="PlayerOne")
        u2 = User(username="Clicky")
        USERS[u1.id] = u1
        USERS[u2.id] = u2
        GAMES[u1.id] = GameState(user_id=u1.id)
        GAMES[u2.id] = GameState(user_id=u2.id)
    if not UPGRADES:
        upg1 = Upgrade(name="Double Clicker", description="Clicks count x2!", cost=50, multiplier=2, level_required=2)
        upg2 = Upgrade(name="Quick Thumb", description="Faster dopamine gain", cost=120, multiplier=1.25, level_required=3)
        UPGRADES[upg1.id] = upg1
        UPGRADES[upg2.id] = upg2

# --- Modularization Note ---
# For production: Move models to `models.py`, implement persistent DB layer, add authentication, etc.
