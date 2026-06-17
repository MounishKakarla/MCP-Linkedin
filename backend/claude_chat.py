import os
import json
import anthropic
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
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "create_post",
        "description": "Create a LinkedIn post on behalf of the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Post content (max 3000 characters)",
                },
                "visibility": {
                    "type": "string",
                    "enum": ["PUBLIC", "CONNECTIONS"],
                    "description": "Who can see the post",
                },
            },
            "required": ["text"],
        },
    },
]


async def _execute_tool(name: str, inputs: dict, access_token: str) -> str:
    async with LinkedInClient(access_token) as li:
        if name == "get_my_profile":
            result = await li.get_profile()
        elif name == "create_post":
            result = await li.create_post(
                text=inputs["text"],
                visibility=inputs.get("visibility", "PUBLIC"),
            )
        else:
            result = {"error": f"Unknown tool: {name}"}
    return json.dumps(result)


async def chat(messages: list[dict], access_token: str, api_key: str | None = None) -> dict:
    client = _make_client(api_key)
    tools_used: list[str] = []

    anthropic_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

    while True:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=(
                "You are a helpful assistant with access to the user's LinkedIn account. "
                "Use available tools to answer questions about their profile or help them create posts. "
                "Be concise and friendly."
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
                    result = await _execute_tool(block.name, block.input, access_token)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            anthropic_messages.append({"role": "user", "content": tool_results})
        else:
            break

    return {"response": "Unexpected error from Claude.", "toolsUsed": tools_used}
