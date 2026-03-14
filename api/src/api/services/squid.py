import docker
from filelock import FileLock

from api.config import settings


def reload_squid() -> None:
    lock_path = "/tmp/squid_reload.lock"
    with FileLock(lock_path, timeout=10):
        client = docker.from_env()
        container = client.containers.get(settings.squid_container)
        container.exec_run("squid -k reconfigure")


def write_domains(domains: list[str]) -> None:
    """Записывает approved домены в файл для Squid"""
    lines = [f".{d}" if not d.startswith(".") else d for d in sorted(set(domains))]
    with open(settings.domains_file, "w") as f:
        f.write("\n".join(lines) + "\n")
