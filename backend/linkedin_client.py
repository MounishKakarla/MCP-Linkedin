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

    async def _register_image_upload(self) -> tuple[str, str]:
        """Register image upload with LinkedIn. Returns (asset_urn, upload_url)."""
        profile = await self.get_profile()
        owner_urn = f"urn:li:person:{profile['id']}"
        register_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": owner_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }
        r = await self._client.post("assets?action=registerUpload", json=register_payload)
        _raise_for_status(r)
        d = r.json()
        asset_urn = d["value"]["asset"]
        upload_url = d["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        return asset_urn, upload_url

    async def upload_image_data(self, data: bytes, content_type: str = "image/jpeg") -> str:
        """Upload raw image bytes to LinkedIn. Returns asset URN."""
        asset_urn, upload_url = await self._register_image_upload()
        async with httpx.AsyncClient() as http:
            up_r = await http.put(
                upload_url,
                content=data,
                headers={"Content-Type": content_type},
            )
            up_r.raise_for_status()
        return asset_urn

    async def upload_image(self, image_url: str) -> str:
        """Download image from URL, upload to LinkedIn. Returns asset URN."""
        asset_urn, upload_url = await self._register_image_upload()
        async with httpx.AsyncClient(follow_redirects=True) as http:
            img_r = await http.get(image_url)
            img_r.raise_for_status()
            image_bytes = img_r.content
            content_type = img_r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        async with httpx.AsyncClient() as http:
            up_r = await http.put(
                upload_url,
                content=image_bytes,
                headers={"Content-Type": content_type},
            )
            up_r.raise_for_status()
        return asset_urn

    async def create_post(
        self,
        text: str,
        visibility: str = "PUBLIC",
        image_url: str | None = None,
        image_data: bytes | None = None,
        image_mime_type: str = "image/jpeg",
    ) -> dict:
        profile = await self.get_profile()
        author_urn = f"urn:li:person:{profile['id']}"

        share_content: dict = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "NONE",
        }

        if image_data:
            asset_urn = await self.upload_image_data(image_data, image_mime_type)
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = [
                {
                    "status": "READY",
                    "description": {"text": ""},
                    "media": asset_urn,
                    "title": {"text": ""},
                }
            ]
        elif image_url:
            asset_urn = await self.upload_image(image_url)
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = [
                {
                    "status": "READY",
                    "description": {"text": ""},
                    "media": asset_urn,
                    "title": {"text": ""},
                }
            ]

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
        }
        r = await self._client.post("ugcPosts", json=payload)
        _raise_for_status(r)
        post_urn = r.headers.get("x-restli-id", "")
        return {"status": "published", "postUrn": post_urn}

    async def reshare_post(self, post_urn: str, commentary: str = "", visibility: str = "PUBLIC") -> dict:
        profile = await self.get_profile()
        author_urn = f"urn:li:person:{profile['id']}"
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": commentary},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
            "resharedEntity": post_urn,
        }
        r = await self._client.post("ugcPosts", json=payload)
        _raise_for_status(r)
        new_urn = r.headers.get("x-restli-id", "")
        return {"status": "reshared", "postUrn": new_urn}

    async def create_article_post(
        self,
        text: str,
        url: str,
        title: str = "",
        description: str = "",
        visibility: str = "PUBLIC",
    ) -> dict:
        profile = await self.get_profile()
        author_urn = f"urn:li:person:{profile['id']}"
        media_item: dict = {"status": "READY", "originalUrl": url}
        if title:
            media_item["title"] = {"text": title}
        if description:
            media_item["description"] = {"text": description}
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [media_item],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }
        r = await self._client.post("ugcPosts", json=payload)
        _raise_for_status(r)
        post_urn = r.headers.get("x-restli-id", "")
        return {"status": "published", "postUrn": post_urn}

    async def edit_post(self, post_urn: str, text: str) -> dict:
        payload = {
            "patch": {
                "$set": {
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": text}
                        }
                    }
                }
            }
        }
        r = await self._client.patch(
            f"ugcPosts/{_enc(post_urn)}",
            json=payload,
            headers={"X-Restli-Method": "PARTIAL_UPDATE"},
        )
        _raise_for_status(r)
        return {"status": "updated", "postUrn": post_urn}

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

    async def react_to_post(self, post_urn: str, reaction: str = "LIKE") -> dict:
        profile = await self.get_profile()
        actor_urn = f"urn:li:person:{profile['id']}"
        payload = {"actor": actor_urn, "reactionType": reaction}
        r = await self._client.post(
            f"socialActions/{_enc(post_urn)}/reactions", json=payload
        )
        _raise_for_status(r)
        return {"status": "reacted", "reaction": reaction, "postUrn": post_urn}

    async def remove_reaction(self, post_urn: str) -> dict:
        profile = await self.get_profile()
        person_urn = f"urn:li:person:{profile['id']}"
        r = await self._client.delete(
            f"socialActions/{_enc(post_urn)}/reactions/{_enc(person_urn)}"
        )
        _raise_for_status(r)
        return {"status": "reaction_removed", "postUrn": post_urn}

    async def get_post_comments(self, post_urn: str) -> dict:
        r = await self._client.get(f"socialActions/{_enc(post_urn)}/comments")
        _raise_for_status(r)
        return r.json()

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
