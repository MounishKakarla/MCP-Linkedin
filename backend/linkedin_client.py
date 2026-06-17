import os
import httpx
from urllib.parse import quote

BASE_URL = "https://api.linkedin.com/v2/"
REST_BASE_URL = "https://api.linkedin.com/rest/"

# LinkedIn retires API versions on ~1-year rolling window.
# Override via LINKEDIN_API_VERSION env var to bump without redeploy.
_LINKEDIN_VERSION = os.environ.get("LINKEDIN_API_VERSION", "202604")


def _raise_for_status(r: httpx.Response) -> None:
    if r.is_error:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise httpx.HTTPStatusError(
            f"LinkedIn API {r.status_code}: {detail}",
            request=r.request,
            response=r,
        )


def _enc(urn: str) -> str:
    return quote(urn, safe="")


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
                "LinkedIn-Version": _LINKEDIN_VERSION,
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )

    async def __aenter__(self) -> "LinkedInClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self._client.aclose()
        await self._rest_client.aclose()

    # ── Profile ──────────────────────────────────────────────────────────────

    async def get_profile(self) -> dict:
        r = await self._client.get("userinfo")
        _raise_for_status(r)
        d = r.json()
        return {
            "id": d.get("sub", ""),
            "firstName": d.get("given_name", ""),
            "lastName": d.get("family_name", ""),
            "name": d.get("name", ""),
            "profilePicture": d.get("picture"),
            "emailAddress": d.get("email", ""),
        }

    # ── Posts ─────────────────────────────────────────────────────────────────

    async def create_post(self, text: str, visibility: str = "PUBLIC") -> dict:
        profile = await self.get_profile()
        author_urn = f"urn:li:person:{profile['id']}"
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
        }
        r = await self._client.post("ugcPosts", json=payload)
        _raise_for_status(r)
        post_urn = r.headers.get("x-restli-id", "")
        return {"status": "published", "postUrn": post_urn}

    async def get_post(self, post_urn: str) -> dict:
        r = await self._client.get(f"ugcPosts/{_enc(post_urn)}")
        _raise_for_status(r)
        return r.json()

    async def delete_post(self, post_urn: str) -> dict:
        r = await self._client.delete(f"ugcPosts/{_enc(post_urn)}")
        _raise_for_status(r)
        return {"status": "deleted", "postUrn": post_urn}

    # ── Reactions ─────────────────────────────────────────────────────────────

    async def like_post(self, post_urn: str) -> dict:
        profile = await self.get_profile()
        actor_urn = f"urn:li:person:{profile['id']}"
        payload = {"actor": actor_urn, "object": post_urn}
        r = await self._client.post(
            f"socialActions/{_enc(post_urn)}/likes", json=payload
        )
        _raise_for_status(r)
        return {"status": "liked", "postUrn": post_urn}

    async def unlike_post(self, post_urn: str) -> dict:
        profile = await self.get_profile()
        person_urn = f"urn:li:person:{profile['id']}"
        r = await self._client.delete(
            f"socialActions/{_enc(post_urn)}/likes/{_enc(person_urn)}"
        )
        _raise_for_status(r)
        return {"status": "unliked", "postUrn": post_urn}

    # ── Comments ──────────────────────────────────────────────────────────────

    async def comment_on_post(self, post_urn: str, text: str) -> dict:
        profile = await self.get_profile()
        actor_urn = f"urn:li:person:{profile['id']}"
        payload = {
            "actor": actor_urn,
            "object": post_urn,
            "message": {"text": text},
        }
        r = await self._client.post(
            f"socialActions/{_enc(post_urn)}/comments", json=payload
        )
        _raise_for_status(r)
        comment_urn = r.headers.get("x-restli-id", "")
        return {"status": "commented", "commentUrn": comment_urn}

    async def delete_comment(self, post_urn: str, comment_urn: str) -> dict:
        r = await self._client.delete(
            f"socialActions/{_enc(post_urn)}/comments/{_enc(comment_urn)}"
        )
        _raise_for_status(r)
        return {"status": "deleted", "commentUrn": comment_urn}
