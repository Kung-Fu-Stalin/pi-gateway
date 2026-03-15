import logging
import os
import tempfile

import docker

from api.config import settings

logger = logging.getLogger(__name__)


def reload_squid() -> None:
    try:
        client = docker.from_env()
        container = client.containers.get(settings.squid_container)
        if container.status == "running":
            result = container.exec_run("squid -k reconfigure")
            if result.exit_code != 0:
                logger.warning("squid reconfigure exited with code %d", result.exit_code)
        else:
            logger.warning("Squid container is not running: %s", container.status)
    except Exception as e:
        logger.warning("Failed to reload squid: %s", e)


def write_domains(domains: list[str]) -> None:
    lines = [f".{d}" if not d.startswith(".") else d for d in domains]
    if not lines:
        lines = [".localhost"]

    content = "\n".join(lines) + "\n"
    target = settings.domains_file
    dir_name = os.path.dirname(target) or "."
    tmp_path = None

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
        logger.debug("Wrote %d domains to %s", len(domains), target)
    except Exception as e:
        logger.error("Failed to write domains file: %s", e)
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise