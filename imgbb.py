"""
Thin async client for the ImgBB upload API, with retry logic.
"""
import asyncio
import base64
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

IMGBB_URL = "https://api.imgbb.com/1/upload"


async def upload_to_imgbb(
    session: aiohttp.ClientSession,
    api_key: str,
    file_path: str,
    retries: int = 3,
) -> Optional[str]:
    """
    Upload a single image (original quality, no compression) to ImgBB.
    Returns the direct image URL on success, or None if all retries fail.
    """
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    for attempt in range(1, retries + 1):
        try:
            async with session.post(
                IMGBB_URL,
                data={"key": api_key, "image": image_data},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                result = await resp.json()
                if resp.status == 200 and result.get("success"):
                    return result["data"]["url"]
                logger.warning(
                    "ImgBB upload failed for %s (attempt %d/%d): %s",
                    file_path, attempt, retries, result,
                )
        except Exception as exc:  # noqa: BLE001 - log and retry on any network hiccup
            logger.warning(
                "ImgBB upload exception for %s (attempt %d/%d): %s",
                file_path, attempt, retries, exc,
            )

        if attempt < retries:
            await asyncio.sleep(1.5 * attempt)  # simple backoff

    logger.error("ImgBB upload permanently failed for %s after %d attempts", file_path, retries)
    return None
