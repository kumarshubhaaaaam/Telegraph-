"""
Telegraph article creation, using the `telegraph` PyPI package.

NOTE ON NAMING: this file is named telegraph_client.py rather than
telegraph.py. If it were named telegraph.py, `from telegraph import
Telegraph` inside it would try to import itself instead of the installed
`telegraph` package, causing an ImportError. Keeping the name distinct
avoids that shadowing bug.
"""
import logging
from typing import List, Optional

from telegraph import Telegraph

logger = logging.getLogger(__name__)


class TelegraphManager:
    def __init__(self, short_name: str, access_token: Optional[str] = None):
        self.telegraph = Telegraph(access_token=access_token)
        if not self.telegraph.get_access_token():
            self.telegraph.create_account(short_name=short_name)
            logger.info("Created new Telegraph account '%s'", short_name)

    def create_article(self, image_urls: List[str], title: str = "Untitled") -> str:
        """
        Build a Telegraph article containing only the embedded images, in the
        exact order given, separated by double line breaks. No text is added.
        """
        content = []
        for i, url in enumerate(image_urls):
            content.append({"tag": "img", "attrs": {"src": url}})
            if i != len(image_urls) - 1:
                content.append({"tag": "br"})
                content.append({"tag": "br"})

        response = self.telegraph.create_page(title=title, content=content)
        return response["url"]
