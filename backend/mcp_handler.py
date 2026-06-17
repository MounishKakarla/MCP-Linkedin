import json
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from mcp import types
from starlette.requests import Request
import db
from linkedin_client import LinkedInClient

_transports: dict[str, SseServerTransport] = {}


def _build_server(user_id: str, client: LinkedInClient) -> Server:
    server = Server("linkedin-mcp")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="get_my_profile",
                description="Get your LinkedIn profile including name, headline, and photo",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="get_my_posts",
                description="Get your recent LinkedIn posts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                    },
                },
            ),
            types.Tool(
                name="get_reactions_on_post",
                description="Get reactions (likes) on a specific LinkedIn post",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string", "description": "Post URN e.g. urn:li:ugcPost:123"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="get_comments_on_post",
                description="Get comments on a specific LinkedIn post",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string", "description": "Post URN e.g. urn:li:ugcPost:123"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="get_my_organizations",
                description="Get a list of LinkedIn organizations (company pages) that you administer",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="get_organization_profile",
                description="Get details about a specific LinkedIn organization",
                inputSchema={
                    "type": "object",
                    "properties": {"org_urn": {"type": "string", "description": "Organization URN e.g. urn:li:organization:123"}},
                    "required": ["org_urn"],
                },
            ),
            types.Tool(
                name="get_organization_posts",
                description="Get recent posts authored by a specific LinkedIn organization",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "org_urn": {"type": "string", "description": "Organization URN e.g. urn:li:organization:123"},
                        "count": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                    },
                    "required": ["org_urn"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent]:
        args = arguments or {}

        if name == "get_my_profile":
            await db.log_activity(user_id, name)
            result = await client.get_profile()
        elif name == "get_my_posts":
            await db.log_activity(user_id, name)
            result = await client.get_posts(args.get("count", 10))
        elif name == "get_reactions_on_post":
            await db.log_activity(user_id, name)
            result = await client.get_reactions(args["post_urn"])
        elif name == "get_comments_on_post":
            await db.log_activity(user_id, name)
            result = await client.get_comments(args["post_urn"])
        elif name == "get_my_organizations":
            await db.log_activity(user_id, name)
            result = await client.get_my_organizations()
        elif name == "get_organization_profile":
            await db.log_activity(user_id, name)
            result = await client.get_organization_profile(args["org_urn"])
        elif name == "get_organization_posts":
            await db.log_activity(user_id, name)
            result = await client.get_posts(args.get("count", 10), author_urn=args["org_urn"])
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=json.dumps(result))]

    return server


async def handle_mcp_connection(user_id: str, request: Request) -> None:
    token = await db.get_token(user_id)
    if not token:
        from fastapi.responses import JSONResponse
        # Caller checks before this; but guard anyway
        raise RuntimeError("no_token")

    async with LinkedInClient(token) as client:
        server = _build_server(user_id, client)
        transport = SseServerTransport(f"/mcp/{user_id}/messages")
        _transports[user_id] = transport

        init_options = InitializationOptions(
            server_name="linkedin-mcp",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )

        try:
            async with transport.connect_sse(
                request.scope, request.receive, request._send
            ) as (read_stream, write_stream):
                await server.run(read_stream, write_stream, init_options)
        finally:
            _transports.pop(user_id, None)


async def handle_mcp_message(user_id: str, request: Request) -> None:
    transport = _transports.get(user_id)
    if transport is None:
        raise LookupError("no_transport")
    await transport.handle_post_message(request.scope, request.receive, request._send)
