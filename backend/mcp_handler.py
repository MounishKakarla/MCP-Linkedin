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
                        "text": {
                            "type": "string",
                            "description": "Post content (plain text, max 3000 chars)",
                        },
                        "visibility": {
                            "type": "string",
                            "enum": ["PUBLIC", "CONNECTIONS"],
                            "default": "PUBLIC",
                            "description": "Who can see the post",
                        },
                    },
                    "required": ["text"],
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
        elif name == "create_post":
            await db.log_activity(user_id, name)
            result = await client.create_post(
                text=args["text"],
                visibility=args.get("visibility", "PUBLIC"),
            )
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
