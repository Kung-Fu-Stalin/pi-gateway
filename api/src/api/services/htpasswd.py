import subprocess
from pathlib import Path

from api.config import settings


def generate_hash(password: str) -> str:
    result = subprocess.run(
        ["openssl", "passwd", "-apr1", password],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def rebuild_htpasswd(users: list[tuple[str, str]]) -> None:
    """users — список (proxy_user, proxy_pass)"""
    lines = []
    for username, password in users:
        hashed = generate_hash(password)
        lines.append(f"{username}:{hashed}")

    Path(settings.htpasswd_file).write_text("\n".join(lines) + "\n")
