import os
import httpx
from urllib.parse import urlencode

# Standard scopes available to all LinkedIn apps (OIDC + social write).
# r_liteprofile / r_emailaddress / r_1st_connections_size / r_member_social /
# r_organization_admin / r_organization_social are deprecated or require
# LinkedIn Partner Program approval — requesting them breaks the OAuth page.
SCOPES = "openid profile email w_member_social"


def _redirect_uri() -> str:
    return os.environ["LINKEDIN_REDIRECT_URI"].strip()


def get_authorization_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": os.environ["LINKEDIN_CLIENT_ID"],
        "redirect_uri": _redirect_uri(),
        "state": state,
        "scope": SCOPES,
    }
    return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _redirect_uri(),
                "client_id": os.environ["LINKEDIN_CLIENT_ID"],
                "client_secret": os.environ["LINKEDIN_CLIENT_SECRET"],
            },
        )
        response.raise_for_status()
        return response.json()
