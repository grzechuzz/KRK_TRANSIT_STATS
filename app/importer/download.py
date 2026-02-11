import tempfile
from pathlib import Path

import requests

from app.common.constants import USER_AGENT
from app.common.feeds import FeedConfig

_HEADERS = {"User-Agent": USER_AGENT}


def download_gtfs_zip(feed: FeedConfig, timeout: int = 60) -> Path:
    """
    Download GTFS Static ZIP to temporary file. Returns path to downloaded ZIP.
    """
    response = requests.get(feed.static_url, timeout=timeout, headers=_HEADERS)
    response.raise_for_status()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_file.write(response.content)
    temp_file.close()

    return Path(temp_file.name)
