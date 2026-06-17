# LinkedIn MCP Server — Implementation Instructions

---

## What You Are Building

A three-part system: a backend server that talks to LinkedIn, an MCP endpoint that Claude connects to, and a React dashboard that lets users link their LinkedIn account and copy their personal endpoint URL. Claude is the intelligence — you are only building the data bridge.

---

## Prerequisites

Before writing a single line of code, complete these steps in order.

Go to the LinkedIn Developer Portal and create a new application. Under the Auth tab, add a redirect URI pointing to your backend callback route. Request the following OAuth scopes: r_liteprofile, r_emailaddress, r_1st_connections_size, and r_member_social (r_member_social is required for reading posts, reactions, and comments — it may require LinkedIn partner approval). The r_messages scope requires a separate LinkedIn partner approval process — skip it for the initial build and apply later. Save your Client ID and Client Secret.

Set up a PostgreSQL database. Railway, Render, and Supabase all offer free-tier Postgres instances that are sufficient for this project. Note the connection string.

---

## Project Structure

Create two top-level folders: one called backend and one called frontend. The backend is a Python FastAPI application. The frontend is a React + Vite application. This separation keeps OAuth logic, MCP logic, database logic, and the LinkedIn API wrapper cleanly isolated.

```
backend/
  main.py              — FastAPI app + all routes
  db.py                — asyncpg pool + 5 helper functions
  auth.py              — LinkedIn OAuth URL builder + token exchange
  linkedin_client.py   — LinkedIn API wrapper (httpx async client)
  mcp_handler.py       — MCP Server + SSEServerTransport per user
  migrate.py           — runs schema.sql against the database
  schema.sql           — CREATE TABLE migrations
  requirements.txt
  Dockerfile
  .env.example

frontend/
  src/
    App.tsx
    components/
      ConnectButton.tsx
      EndpointCard.tsx
      ActivityLog.tsx
    api/
      activity.ts
  index.html
  vite.config.ts
  tailwind.config.js
  postcss.config.js
  Dockerfile
  nginx.conf
  .env.example

docker-compose.yml
render.yaml
```

---

## Backend — Step by Step

### Step 1: Set up the Python project

Inside the backend folder, create a virtual environment and install dependencies from requirements.txt. The key packages are: fastapi, uvicorn[standard] for the ASGI server, httpx for async HTTP requests to the LinkedIn API, asyncpg for async PostgreSQL, python-dotenv for environment variables, mcp for the Model Context Protocol SDK, slowapi for per-user rate limiting, and python-multipart for form data.

### Step 2: Set up environment variables

Create a .env file at the root of the backend with the following variables: your LinkedIn Client ID, your LinkedIn Client Secret, the full redirect URI that matches what you registered in the LinkedIn portal, your PostgreSQL connection string, the URL of your frontend app, and the port the server will run on (default 8000).

### Step 3: Build the database schema

In schema.sql, write a SQL migration that creates three tables. The first table, users, stores a UUID primary key and a created_at timestamp. The second table, tokens, stores a user_id foreign key, the access token string, and an expiry timestamp — use user_id as the primary key so each user has exactly one token row. The third table, activity_log, stores an auto-incrementing ID, the user_id, the name of the MCP tool that was called, and a timestamp. Add an index on activity_log covering user_id and called_at descending so dashboard queries are fast.

Run this migration by executing `python migrate.py` before starting the server.

### Step 4: Write the database helper (db.py)

Open a connection pool with asyncpg using your DATABASE_URL environment variable. Initialise and close the pool via FastAPI's lifespan context manager. Export five async functions: one to insert a new user row, one to upsert a token row (insert or update on conflict), one to fetch a token by user ID only if it has not expired, one to insert a row into the activity log, and one to select the most recent 100 activity rows for a given user ordered by time descending.

### Step 5: Build the LinkedIn OAuth module (auth.py)

Export a constant for the OAuth scopes joined into a space-separated string. Export a function that accepts a random state string and returns the full LinkedIn authorization URL with all required query parameters. Export an async function that accepts an authorization code and POSTs to the LinkedIn token endpoint to exchange it for an access token, returning the full token response dict.

### Step 6: Build the LinkedIn API client (linkedin_client.py)

Write a class that accepts an access token in its constructor and creates an httpx.AsyncClient configured with the LinkedIn v2 base URL and the Authorization and X-Restli-Protocol-Version headers. Implement the class as an async context manager so the httpx client is properly closed. Add async methods for: fetching the authenticated user's profile (id, name, headline, picture), fetching their email address, fetching their first-degree connection count, fetching recent UGC posts by author, fetching reactions on a post URN, and fetching comments on a post URN.

### Step 7: Build the MCP handler (mcp_handler.py)

Write a function that accepts a user_id and a LinkedInClient and returns a configured mcp.server.Server instance. Register four tools on this server using the @server.list_tools() and @server.call_tool() decorators: get_my_profile (no params), get_my_posts (count integer param), get_reactions_on_post (post_urn string param), and get_comments_on_post (post_urn string param). Each tool handler calls db.log_activity first, then calls the appropriate LinkedInClient method, then returns a list containing a TextContent object with the JSON-stringified result.

Store active SSEServerTransport instances in a module-level dict keyed by user_id. Write an async handle_mcp_connection function that retrieves the token, creates the server, creates a new SSEServerTransport pointing to /mcp/{user_id}/messages, stores it in the dict, and uses transport.connect_sse with the ASGI scope/receive/send to run the server. Write a handle_mcp_message function that looks up the transport and calls transport.handle_post_message.

### Step 8: Write the FastAPI application (main.py)

Create the FastAPI app with a lifespan context manager that initialises and closes the database pool. Add CORS middleware configured to allow requests from your frontend URL. Configure slowapi with a key function that extracts the user_id from path parameters. Define five routes:

GET /api/health — returns {"status": "ok"} for deployment health checks.

GET /auth/linkedin — generates a random hex state, sets it as an httpOnly cookie, and redirects to the LinkedIn authorization URL.

GET /auth/linkedin/callback — reads the code and state query parameters, verifies the state matches the cookie, exchanges the code for a token, generates a UUID for the new user, calls create_user and store_token, then redirects to the frontend dashboard URL with userId as a query parameter.

GET /mcp/{user_id} — applies the 1000/day rate limiter, retrieves the token (401 if missing), and calls handle_mcp_connection. This is the SSE endpoint Claude connects to.

POST /mcp/{user_id}/messages — calls handle_mcp_message (404 if no active session). This receives messages from Claude and relays them to the SSE transport.

GET /api/activity/{user_id} — returns the activity log as JSON.

Start the server with uvicorn: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`.

### Step 9: Configure the rate limiter

Use slowapi with a custom key function that reads req.path_params["user_id"] so the 1,000 requests per day limit is per user rather than per IP address. Return a clear JSON error when the limit is exceeded.

---

## Frontend — Step by Step

### Step 10: Initialise the React project

Inside the frontend folder, initialise a Vite project with the React TypeScript template. Install Tailwind CSS and configure it. Set a VITE_API_URL environment variable pointing to your deployed backend URL.

### Step 11: Build the App component

The root App component should on mount read the userId from either the URL query parameters or localStorage. If a userId is found in the URL, save it to localStorage for persistence across refreshes. If no userId exists, render the ConnectButton component. If a userId exists, render the EndpointCard component and the ActivityLog component, passing userId as a prop to both.

### Step 12: Build the ConnectButton component

This component renders a card explaining that the connection is read-only. It contains a single button. When clicked, the button navigates the user to your backend's /auth/linkedin route, which kicks off the OAuth flow.

### Step 13: Build the EndpointCard component

This component receives the userId prop and constructs the full MCP endpoint URL by combining VITE_API_URL with /mcp/ and the userId. It displays a green connected indicator, the endpoint URL in a monospaced element, and a Copy button. The Copy button writes the URL to the clipboard using the Clipboard API and temporarily changes its label to confirm the copy was successful.

### Step 14: Build the ActivityLog component

This component receives the userId prop and on mount fetches from your backend's /api/activity/:userId route. It stores the result in local state and re-fetches on a 10-second interval, clearing the interval on unmount. It renders each log entry showing the tool name and the human-readable time it was called. If the log is empty, it shows a message prompting the user to start asking Claude questions about their LinkedIn.

---

## Running Locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # fill in credentials
python migrate.py
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Or with Docker:
```bash
docker compose up --build
```

---

## Deployment

### Backend

Deploy to Render. Create a new Web Service pointing at the `backend/` directory. Set the build command to `pip install -r requirements.txt` and the start command to `python migrate.py && uvicorn main:app --host 0.0.0.0 --port $PORT`. Add a PostgreSQL database via the Render dashboard — the DATABASE_URL is injected automatically. Set the remaining environment variables (LinkedIn credentials, FRONTEND_URL, LINKEDIN_REDIRECT_URI) through the dashboard.

Alternatively, use the `render.yaml` blueprint in the repository root — Render auto-detects it and provisions all three resources (backend service, static frontend, Postgres database).

### Frontend

Deploy as a Render Static Site or to Vercel. Set the VITE_API_URL build environment variable to your backend's Render URL. The SPA rewrite rule (`/* → /index.html`) is already configured in nginx.conf (Docker) and render.yaml (Render).

### DNS

Point a custom domain to both services using Cloudflare, which provides free SSL termination. The backend needs HTTPS because SSE connections over plain HTTP are blocked by browsers.

---

## Connecting to Claude

After deployment, a user visits your dashboard, clicks Connect LinkedIn, completes the OAuth flow, and lands back on the dashboard with their personal endpoint URL displayed. They copy that URL. In Claude, they go to Settings, then Integrations, then Add MCP Server, and paste the URL. Claude now has access to all four tools and can read their LinkedIn data on demand.

---

## Security Requirements

Tokens must never be returned to the frontend. The OAuth state parameter must be verified on every callback to prevent CSRF attacks. Every MCP route must be scoped to the userId in the URL — never allow one user's token to be used for another user's endpoint. Token expiry must be checked on every database read, not assumed. All endpoints must be served over HTTPS. The LinkedIn application must only be configured with read-only scopes.

---

## Scope Limitations and Workarounds

LinkedIn's public API is significantly restricted compared to what internal products access. The connection graph beyond a count is not accessible without partner status. Post impression data is not available. The messaging scope requires a formal partner application with a stated use case. For richer profile data on connections, integrate Proxycurl as a paid alternative — it accepts a LinkedIn profile URL and returns structured data without requiring OAuth. Use the official LinkedIn API for the authenticated user's own data and Proxycurl for enriching data about others.

---

## Extending the System

Once the base system works, consider adding token refresh logic so users do not have to reconnect after the token expires. Add a Stripe integration gated behind the endpoint route to monetise per-user access. Apply for the r_messages scope with LinkedIn to unlock conversation data, which enables the full relationship-mapping use case. Add an export tool that lets Claude push the relationship map it generates directly to Notion or Airtable via their own MCP servers.
