# LinkedIn MCP Server

A Model Context Protocol (MCP) server that securely connects Claude to your LinkedIn account, allowing you to seamlessly fetch profiles, posts, comments, and reactions from both your personal profile and any company pages you manage.

## Features

This project exposes 7 powerful MCP tools to Claude:

*   **`get_my_profile`**: Get your LinkedIn profile including name, headline, and photo.
*   **`get_my_posts`**: Get your recent personal LinkedIn posts.
*   **`get_reactions_on_post`**: Get reactions (likes) on a specific LinkedIn post using its URN.
*   **`get_comments_on_post`**: Get comments on a specific LinkedIn post using its URN.
*   **`get_my_organizations`**: Get a list of LinkedIn company pages that you administer.
*   **`get_organization_profile`**: Get details about a specific LinkedIn organization.
*   **`get_organization_posts`**: Get recent posts authored by a specific LinkedIn organization.

## Architecture

The project consists of three main components:
1.  **Frontend (React + Vite)**: A simple dashboard allowing users to log in with their LinkedIn credentials and retrieve their personal MCP Server URL.
2.  **Backend (Python + FastAPI)**: Handles the OAuth 2.0 flow, token storage, and runs the MCP server via an SSE (Server-Sent Events) endpoint.
3.  **Database (PostgreSQL)**: Stores user IDs, OAuth access tokens, and an activity log of MCP tool usage.

## Setup Instructions

### 1. LinkedIn Developer Portal
1. Create a new app in the [LinkedIn Developer Portal](https://developer.linkedin.com/).
2. Request the following OAuth scopes: `r_liteprofile`, `r_emailaddress`, `r_1st_connections_size`, `r_member_social`, `r_organization_admin`, and `r_organization_social`.
3. Set your redirect URI to `http://localhost:3000/auth/linkedin/callback` (or your production URL).
4. Save your Client ID and Client Secret.

### 2. Environment Variables
Create a `.env` file in the `backend/` directory:
```env
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:3000/auth/linkedin/callback
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/linkedin_mcp
FRONTEND_URL=http://localhost:5173
PORT=3000
```

Create a `.env` file in the `frontend/` directory:
```env
VITE_API_URL=http://localhost:3000
```

### 3. Running Locally (Docker)
The easiest way to run the application is using Docker Compose:

```bash
docker compose up -d --build
```
This will start:
- PostgreSQL database on port 5432
- FastAPI Backend on port 3000
- React Frontend on port 5173

Access the frontend dashboard at `http://localhost:5173` to log in.

## Connecting to Claude

1. Log into the local dashboard at `http://localhost:5173`.
2. Authenticate with LinkedIn.
3. The dashboard will generate a custom endpoint URL (e.g., `http://localhost:3000/mcp/your-uuid`).
4. Copy this URL.
5. In Claude desktop app, go to **Settings → Integrations → Add MCP Server**.
6. Paste the URL. Claude can now fetch your LinkedIn data on demand!

## Security Notes
- The OAuth tokens are securely stored in the backend database and are **never** exposed to the frontend.
- The MCP server only asks for **read-only** permissions. It cannot create posts, send messages, or modify your profile.
