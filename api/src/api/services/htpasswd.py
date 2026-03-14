import logging
import os
import subprocess
import tempfile
from pathlib import Path

from api.config import settings

logger = logging.getLogger(__name__)


def generate_hash(password: str) -> str:
    result = subprocess.run(
        ["openssl", "passwd", "-apr1", password],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return result.stdout.strip()


def rebuild_htpasswd(users: list[tuple[str, str]]) -> None:
    lines = []
    for username, password in users:
        hashed = generate_hash(password)
        lines.append(f"{username}:{hashed}")

    content = "\n".join(lines) + "\n" if lines else ""
    target = settings.htpasswd_file
    dir_name = os.path.dirname(target) or "."

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=dir_name,
            delete=False,
            suffix=".tmp",
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        os.replace(tmp_path, target)
        logger.debug("Rebuilt htpasswd with %d users", len(users))
    except Exception as e:
        logger.error("Failed to write htpasswd file: %s", e)
        if "tmp_path" in dir() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise