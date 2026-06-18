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
                name="get_my_recent_posts",
                description="Get your recent LinkedIn posts (created via this app) as a numbered list with snippets and URNs.",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="create_post",
                description="Publish a post to LinkedIn. Optionally attach one image via URL.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Post content (plain text, max 3000 chars)"},
                        "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"], "default": "PUBLIC"},
                        "image_url": {"type": "string", "description": "Optional public URL of an image to attach"},
                        "image_base64": {"type": "string", "description": "Optional raw base64 encoded string of an image file to attach (without the data:image/png;base64, prefix)"},
                    },
                    "required": ["text"],
                },
            ),
            types.Tool(
                name="create_article_post",
                description="Publish a post with a URL link preview.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Post commentary"},
                        "url": {"type": "string", "description": "URL to share"},
                        "title": {"type": "string", "description": "Optional link title override"},
                        "description": {"type": "string", "description": "Optional link description override"},
                        "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"], "default": "PUBLIC"},
                    },
                    "required": ["text", "url"],
                },
            ),
            types.Tool(
                name="reshare_post",
                description="Reshare an existing LinkedIn post with optional commentary.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_urn": {"type": "string"},
                        "commentary": {"type": "string", "description": "Text to add when resharing"},
                        "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"], "default": "PUBLIC"},
                    },
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="edit_post",
                description="Edit the text of one of your LinkedIn posts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_urn": {"type": "string"},
                        "text": {"type": "string", "description": "New post content"},
                    },
                    "required": ["post_urn", "text"],
                },
            ),
            types.Tool(
                name="delete_post",
                description="Delete one of your LinkedIn posts.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="like_post",
                description="Like a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="unlike_post",
                description="Remove your like from a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="react_to_post",
                description="React to a post: LIKE, CELEBRATION, APPRECIATION, EMPATHY, INTEREST, or PRAISE.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_urn": {"type": "string"},
                        "reaction": {
                            "type": "string",
                            "enum": ["LIKE", "CELEBRATION", "APPRECIATION", "EMPATHY", "INTEREST", "PRAISE"],
                            "default": "LIKE",
                        },
                    },
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="remove_reaction",
                description="Remove your reaction from a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="get_post_comments",
                description="Get comments on a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {"post_urn": {"type": "string"}},
                    "required": ["post_urn"],
                },
            ),
            types.Tool(
                name="comment_on_post",
                description="Add a comment to a LinkedIn post.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_urn": {"type": "string"},
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
                        "post_urn": {"type": "string"},
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
        elif name == "get_my_recent_posts":
            result = await db.get_recent_posts(user_id)
        elif name == "create_post":
            image_data = None
            image_mime_type = "image/jpeg"
            if "image_base64" in args:
                import base64
                image_data = base64.b64decode(args["image_base64"])
                # We can assume jpeg, or let LinkedIn's API handle it if we guess wrong.

            result = await client.create_post(
                text=args["text"],
                visibility=args.get("visibility", "PUBLIC"),
                image_url=args.get("image_url"),
                image_data=image_data,
                image_mime_type=image_mime_type,
            )
            if result.get("postUrn"):
                await db.save_post(user_id, result["postUrn"], args["text"])
        elif name == "create_article_post":
            result = await client.create_article_post(
                text=args["text"],
                url=args["url"],
                title=args.get("title", ""),
                description=args.get("description", ""),
                visibility=args.get("visibility", "PUBLIC"),
            )
            if result.get("postUrn"):
                await db.save_post(user_id, result["postUrn"], args["text"])
        elif name == "reshare_post":
            result = await client.reshare_post(
                post_urn=args["post_urn"],
                commentary=args.get("commentary", ""),
                visibility=args.get("visibility", "PUBLIC"),
            )
            if result.get("postUrn"):
                label = args.get("commentary") or f"reshared {args['post_urn']}"
                await db.save_post(user_id, result["postUrn"], label)
        elif name == "edit_post":
            result = await client.edit_post(args["post_urn"], args["text"])
        elif name == "delete_post":
            result = await client.delete_post(args["post_urn"])
        elif name == "like_post":
            result = await client.like_post(args["post_urn"])
        elif name == "unlike_post":
            result = await client.unlike_post(args["post_urn"])
        elif name == "react_to_post":
            result = await client.react_to_post(args["post_urn"], args.get("reaction", "LIKE"))
        elif name == "remove_reaction":
            result = await client.remove_reaction(args["post_urn"])
        elif name == "get_post_comments":
            result = await client.get_post_comments(args["post_urn"])
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
