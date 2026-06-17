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
                description="Get your LinkedIn profile: name, email, and profile photo.",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="create_post",
                description="Publish a text post to LinkedIn on your behalf.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Post content (plain text, max 3000 chars)"},
                        "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"], "default": "PUBLIC"},
                    },
                    "required": ["text"],
                },
            ),
            types.Tool(
                name="get_post",
                description="Get a specific LinkedIn post by its URN.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string", "description": "e.g. urn:li:ugcPost:123456"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="delete_post",
                description="Delete one of your LinkedIn posts.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string", "description": "e.g. urn:li:ugcPost:123456"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="like_post",
                description="Like a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string", "description": "e.g. urn:li:ugcPost:123456"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="unlike_post",
                description="Remove your like from a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string", "description": "e.g. urn:li:ugcPost:123456"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="comment_on_post",
                description="Add a comment to a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_urn": {"type": "string", "description": "e.g. urn:li:ugcPost:123456"},
                        "text": {"type": "string", "description": "Comment text"},
                    },
                    "required": ["post_urn", "text"],
                },
            ),
            types.Tool(
                name="delete_comment",
                description="Delete one of your comments on a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_urn": {"type": "string", "description": "Post URN"},
                        "comment_urn": {"type": "string", "description": "Comment URN returned by comment_on_post"},
                    },
                    "required": ["post_urn", "comment_urn"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent]:
        args = arguments or {}

        if name == "get_my_profile":
            result = await client.get_profile()
        elif name == "create_post":
            result = await client.create_post(
                text=args["text"],
                visibility=args.get("visibility", "PUBLIC"),
            )
        elif name == "get_post":
            result = await client.get_post(args["post_urn"])
        elif name == "delete_post":
            result = await client.delete_post(args["post_urn"])
        elif name == "like_post":
            result = await client.like_post(args["post_urn"])
        elif name == "unlike_post":
            result = await client.unlike_post(args["post_urn"])
        elif name == "comment_on_post":
            result = await client.comment_on_post(args["post_urn"], args["text"])
        elif name == "delete_comment":
            result = await client.delete_comment(args["post_urn"], args["comment_urn"])
        else:
            raise ValueError(f"Unknown tool: {name}")

        await db.log_activity(user_id, name)
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
