import httpx
from urllib.parse import quote

BASE_URL = "https://api.linkedin.com/v2/"
REST_BASE_URL = "https://api.linkedin.com/rest/"


class LinkedInClient:
    def __init__(self, access_token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        self._rest_client = httpx.AsyncClient(
            base_url=REST_BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "LinkedIn-Version": "202401",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )

    async def __aenter__(self) -> "LinkedInClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self._client.aclose()
        await self._rest_client.aclose()

    async def get_profile(self) -> dict:
        # OIDC userinfo endpoint — works with openid+profile+email scopes.
        # Old /v2/me with projection required deprecated r_liteprofile scope.
        r = await self._client.get("userinfo")
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("sub", ""),
            "firstName": d.get("given_name", ""),
            "lastName": d.get("family_name", ""),
            "name": d.get("name", ""),
            "headline": None,
            "profilePicture": d.get("picture"),
            "emailAddress": d.get("email", ""),
        }

    async def get_email(self) -> dict:
        # Email included in userinfo — no separate call needed.
        profile = await self.get_profile()
        return {"emailAddress": profile["emailAddress"]}

    async def get_connection_count(self) -> dict:
        # Requires r_1st_connections_size (LinkedIn Partner Program only).
        # Not available with standard scopes.
        raise NotImplementedError(
            "Connection count requires r_1st_connections_size — a LinkedIn Partner scope not available to standard apps."
        )

    async def get_my_organizations(self) -> dict:
        # Requires r_organization_admin (LinkedIn Partner Program only).
        raise NotImplementedError(
            "Organization admin access requires r_organization_admin — a LinkedIn Partner scope."
        )

    async def get_organization_profile(self, org_urn: str) -> dict:
        # Requires r_organization_social (LinkedIn Partner Program only).
        raise NotImplementedError(
            "Organization profile requires r_organization_social — a LinkedIn Partner scope."
        )

    async def get_posts(self, count: int = 10, author_urn: str | None = None) -> dict:
        if not author_urn:
            profile = await self.get_profile()
            author_urn = f"urn:li:person:{profile['id']}"
        r = await self._rest_client.get("posts", params={
            "author": author_urn,
            "q": "author",
            "count": count,
            "sortBy": "LAST_MODIFIED",
        })
        r.raise_for_status()
        return r.json()

    async def get_reactions(self, post_urn: str) -> dict:
        r = await self._rest_client.get(f"reactions/{quote(post_urn, safe='')}", params={"q": "entity"})
        r.raise_for_status()
        return r.json()

    async def get_comments(self, post_urn: str) -> dict:
        r = await self._rest_client.get("socialActions", params={
            "q": "targetEntity",
            "targetEntity": post_urn,
        })
        r.raise_for_status()
        return r.json()
