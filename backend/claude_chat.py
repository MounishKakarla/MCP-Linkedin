import os
import json
import anthropic
import db
from linkedin_client import LinkedInClient


def _make_client(api_key: str | None) -> anthropic.AsyncAnthropic:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("No Anthropic API key provided. Enter your key in the chat panel.")
    return anthropic.AsyncAnthropic(api_key=key)


TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "get_my_profile",
        "description": "Get the authenticated user's LinkedIn profile: name, headline, email, profile picture.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_my_recent_posts",
        "description": "Get the user's recent LinkedIn posts (created via this app). Returns a numbered list with snippet and URN for each post. Call this first whenever the user refers to 'my last post', 'post #1', 'that post', etc.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_post",
        "description": "Create a LinkedIn post on behalf of the user. Optionally attach one image via URL or the user's uploaded file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Post content (max 3000 characters)"},
                "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"], "description": "Who can see the post"},
                "image_url": {"type": "string", "description": "Optional public URL of an image to attach"},
                "attach_image": {"type": "boolean", "description": "Set to true to attach the image file the user uploaded to this post"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "create_article_post",
        "description": "Create a LinkedIn post with a URL link preview (article share).",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Post commentary (max 3000 characters)"},
                "url": {"type": "string", "description": "The URL to share"},
                "title": {"type": "string", "description": "Optional override for the link title"},
                "description": {"type": "string", "description": "Optional override for the link description"},
                "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"]},
            },
            "required": ["text", "url"],
        },
    },
    {
        "name": "reshare_post",
        "description": "Reshare (repost) an existing LinkedIn post, optionally adding commentary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_urn": {"type": "string", "description": "URN of the post to reshare"},
                "commentary": {"type": "string", "description": "Optional text to add when resharing"},
                "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"]},
            },
            "required": ["post_urn"],
        },
    },
    {
        "name": "edit_post",
        "description": "Edit the text of one of the user's existing LinkedIn posts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_urn": {"type": "string", "description": "URN of the post to edit"},
                "text": {"type": "string", "description": "New post content"},
            },
            "required": ["post_urn", "text"],
        },
    },
    {
        "name": "delete_post",
        "description": "Delete one of the user's LinkedIn posts.",
        "input_schema": {
            "type": "object",
            "properties": {"post_urn": {"type": "string"}},
            "required": ["post_urn"],
        },
    },
    {
        "name": "like_post",
        "description": "Like a LinkedIn post.",
        "input_schema": {
            "type": "object",
            "properties": {"post_urn": {"type": "string"}},
            "required": ["post_urn"],
        },
    },
    {
        "name": "unlike_post",
        "description": "Remove a like from a LinkedIn post.",
        "input_schema": {
            "type": "object",
            "properties": {"post_urn": {"type": "string"}},
            "required": ["post_urn"],
        },
    },
    {
        "name": "react_to_post",
        "description": "React to a LinkedIn post with an emoji reaction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_urn": {"type": "string"},
                "reaction": {
                    "type": "string",
                    "enum": ["LIKE", "CELEBRATION", "APPRECIATION", "EMPATHY", "INTEREST", "PRAISE"],
                    "description": "LIKE=👍 CELEBRATION=🎉 APPRECIATION=🙏 EMPATHY=❤️ INTEREST=💡 PRAISE=👏",
                },
            },
            "required": ["post_urn"],
        },
    },
    {
        "name": "remove_reaction",
        "description": "Remove the user's reaction from a LinkedIn post.",
        "input_schema": {
            "type": "object",
            "properties": {"post_urn": {"type": "string"}},
            "required": ["post_urn"],
        },
    },
    {
        "name": "get_post_comments",
        "description": "Get comments on a LinkedIn post.",
        "input_schema": {
            "type": "object",
            "properties": {"post_urn": {"type": "string"}},
            "required": ["post_urn"],
        },
    },
    {
        "name": "comment_on_post",
        "description": "Add a comment to a LinkedIn post.",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_urn": {"type": "string"},
                "text": {"type": "string", "description": "Comment text"},
            },
            "required": ["post_urn", "text"],
        },
    },
    {
        "name": "delete_comment",
        "description": "Delete one of the user's comments on a LinkedIn post.",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_urn": {"type": "string"},
                "comment_urn": {"type": "string", "description": "Comment URN returned by comment_on_post"},
            },
            "required": ["post_urn", "comment_urn"],
        },
    },
]


async def _execute_tool(
    name: str,
    inputs: dict,
    access_token: str,
    user_id: str,
    image_data: bytes | None = None,
    image_mime_type: str = "image/jpeg",
) -> str:
    if name == "get_my_recent_posts":
        result = await db.get_recent_posts(user_id)
        return json.dumps(result)

    async with LinkedInClient(access_token) as li:
        if name == "get_my_profile":
            result = await li.get_profile()

        elif name == "create_post":
            attached = image_data if inputs.get("attach_image") else None
            result = await li.create_post(
                text=inputs["text"],
                visibility=inputs.get("visibility", "PUBLIC"),
                image_url=inputs.get("image_url"),
                image_data=attached,
                image_mime_type=image_mime_type,
            )
            if result.get("postUrn"):
                await db.save_post(user_id, result["postUrn"], inputs["text"])

        elif name == "create_article_post":
            result = await li.create_article_post(
                text=inputs["text"],
                url=inputs["url"],
                title=inputs.get("title", ""),
                description=inputs.get("description", ""),
                visibility=inputs.get("visibility", "PUBLIC"),
            )
            if result.get("postUrn"):
                await db.save_post(user_id, result["postUrn"], inputs["text"])

        elif name == "reshare_post":
            result = await li.reshare_post(
                post_urn=inputs["post_urn"],
                commentary=inputs.get("commentary", ""),
                visibility=inputs.get("visibility", "PUBLIC"),
            )
            if result.get("postUrn"):
                label = inputs.get("commentary") or f"reshared {inputs['post_urn']}"
                await db.save_post(user_id, result["postUrn"], label)

        elif name == "edit_post":
            result = await li.edit_post(inputs["post_urn"], inputs["text"])

        elif name == "delete_post":
            result = await li.delete_post(inputs["post_urn"])

        elif name == "like_post":
            result = await li.like_post(inputs["post_urn"])

        elif name == "unlike_post":
            result = await li.unlike_post(inputs["post_urn"])

        elif name == "react_to_post":
            result = await li.react_to_post(inputs["post_urn"], inputs.get("reaction", "LIKE"))

        elif name == "remove_reaction":
            result = await li.remove_reaction(inputs["post_urn"])

        elif name == "get_post_comments":
            result = await li.get_post_comments(inputs["post_urn"])

        elif name == "comment_on_post":
            result = await li.comment_on_post(inputs["post_urn"], inputs["text"])

        elif name == "delete_comment":
            result = await li.delete_comment(inputs["post_urn"], inputs["comment_urn"])

        else:
            result = {"error": f"Unknown tool: {name}"}

    return json.dumps(result)


async def chat(
    messages: list[dict],
    access_token: str,
    user_id: str,
    api_key: str | None = None,
    image_data: bytes | None = None,
    image_mime_type: str = "image/jpeg",
) -> dict:
    client = _make_client(api_key)
    tools_used: list[str] = []

    anthropic_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

    image_hint = (
        " The user has attached an image file to this conversation."
        " If they ask to create a post, use attach_image: true in the create_post tool to include it."
    ) if image_data else ""

    while True:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=(
                "You are a helpful assistant with access to the user's LinkedIn account. "
                "Use available tools to answer questions about their profile or help them manage posts. "
                "When the user refers to 'my last post', 'post #1', or any post without giving a URN, "
                "always call get_my_recent_posts first to look up the URN. "
                "Be concise and friendly." + image_hint
            ),
            tools=TOOLS,
            messages=anthropic_messages,
        )

        if response.stop_reason == "end_turn":
            text = "".join(block.text for block in response.content if hasattr(block, "text"))
            return {"response": text, "toolsUsed": tools_used}

        if response.stop_reason == "tool_use":
            anthropic_messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tools_used.append(block.name)
                    result = await _execute_tool(
                        block.name, block.input, access_token, user_id, image_data, image_mime_type
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            anthropic_messages.append({"role": "user", "content": tool_results})
        else:
            break

    return {"response": "Unexpected error from Claude.", "toolsUsed": tools_used}
