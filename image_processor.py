"""
Orchestrates uploading a batch of local images to ImgBB while preserving
their original order, with bounded concurrency and progress callbacks.
"""
import asyncio
import logging
import os
from typing import Callable, List, Optional

import aiohttp

from config import IMGBB_API_KEY, UPLOAD_CONCURRENCY
from imgbb import upload_to_imgbb

logger = logging.getLogger(__name__)


async def upload_all_images(
    image_paths: List[str],
    progress_callback: Optional[Callable[[int, int], "asyncio.Future"]] = None,
) -> List[Optional[str]]:
    """
    Upload every image in image_paths to ImgBB.

    Returns a list the same length and order as image_paths; a failed
    upload (after retries) is represented as None at that index, so
    ordering is never disturbed even when some images are skipped.

    progress_callback(done_count, total_count), if given, is awaited after
    each individual upload completes (success or failure).
    """
    total = len(image_paths)
    results: List[Optional[str]] = [None] * total
    semaphore = asyncio.Semaphore(UPLOAD_CONCURRENCY)
    done_count = 0
    lock = asyncio.Lock()

    async with aiohttp.ClientSession() as session:

        async def worker(index: int, path: str) -> None:
            nonlocal done_count
            async with semaphore:
                url = await upload_to_imgbb(session, IMGBB_API_KEY, path)
                results[index] = url
            async with lock:
                done_count += 1
                if progress_callback:
                    await progress_callback(done_count, total)

        await asyncio.gather(*(worker(i, p) for i, p in enumerate(image_paths)))

    return results


def cleanup_files(paths: List[str]) -> None:
    """Best-effort deletion of temporary image files."""
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError as exc:
            logger.warning("Failed to remove temp file %s: %s", p, exc)
