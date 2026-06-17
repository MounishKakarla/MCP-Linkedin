import os
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import db
from auth import get_authorization_url, exchange_code_for_token
from mcp_handler import handle_mcp_connection, handle_mcp_message
from claude_chat import chat as claude_chat

load_dotenv()

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


def _user_id_key(request: Request) -> str:
    return request.path_params.get("user_id", request.client.host if request.client else "unknown")


limiter = Limiter(key_func=_user_id_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield
    await db.close_pool()


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# GET /api/health
@app.get("/api/health")
async def health():
    return {"status": "ok"}


# GET /auth/linkedin — initiate OAuth
@app.get("/auth/linkedin")
async def auth_linkedin():
    state = secrets.token_hex(16)
    url = get_authorization_url(state)
    response = RedirectResponse(url)
    response.set_cookie(
        "oauth_state", state,
        httponly=True,
        samesite="lax",
        max_age=600,
        secure=os.environ.get("NODE_ENV") == "production",
    )
    return response


# GET /auth/linkedin/callback — complete OAuth
@app.get("/auth/linkedin/callback")
async def auth_callback(request: Request, code: str | None = None, state: str | None = None):
    stored_state = request.cookies.get("oauth_state")

    if not code or not state or state != stored_state:
        raise HTTPException(400, "Invalid OAuth state or missing code.")

    try:
        token_data = await exchange_code_for_token(code)
        access_token = token_data["access_token"]
        expires_in: int = token_data.get("expires_in", 5183944)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        user_id = str(uuid.uuid4())
        await db.create_user(user_id)
        await db.store_token(user_id, access_token, expires_at)

        response = RedirectResponse(f"{FRONTEND_URL}/dashboard?userId={user_id}")
        response.delete_cookie("oauth_state")
        return response
    except Exception as exc:
        raise HTTPException(500, "Failed to complete authentication.") from exc


# GET /mcp/{user_id} — SSE endpoint for MCP clients
@app.get("/mcp/{user_id}")
@limiter.limit("1000/day")
async def mcp_sse(request: Request, user_id: str):
    token = await db.get_token(user_id)
    if not token:
        raise HTTPException(401, "No valid token. Please reconnect your LinkedIn account.")
    await handle_mcp_connection(user_id, request)


# POST /mcp/{user_id}/messages — relay messages from MCP client
@app.post("/mcp/{user_id}/messages")
async def mcp_messages(request: Request, user_id: str):
    try:
        await handle_mcp_message(user_id, request)
    except LookupError:
        raise HTTPException(404, "No active MCP session for this user.")


# GET /api/activity/{user_id} — activity log for dashboard
@app.get("/api/activity/{user_id}")
async def activity_log(user_id: str):
    return await db.get_activity_log(user_id)


# DELETE /api/logout/{user_id} — revoke token and clear session
@app.delete("/api/logout/{user_id}")
async def logout(user_id: str):
    await db.revoke_token(user_id)
    return {"status": "logged out"}


# POST /api/chat/{user_id} — Claude chat with LinkedIn tools
@app.post("/api/chat/{user_id}")
async def chat_endpoint(user_id: str, request: Request):
    token = await db.get_token(user_id)
    if not token:
        raise HTTPException(401, "No valid token. Please reconnect your LinkedIn account.")

    body = await request.json()
    messages = body.get("messages", [])
    api_key = body.get("apiKey") or None

    try:
        result = await claude_chat(messages, token, api_key=api_key)
        for tool in result.get("toolsUsed", []):
            await db.log_activity(user_id, f"chat:{tool}")
        return result
    except ValueError as exc:
        raise HTTPException(500, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Chat error: {exc}") from exc
