import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Домен по RFC 1123: буквы, цифры, дефис, точки + leading dot/wildcard для Squid
_DOMAIN_RE = re.compile(r'^[*.]?[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$')

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,  # PAC — это JS, не HTML, autoescape=True сломает кавычки
)

def _validate_domain(domain: str) -> str:
    """Raise ValueError if domain contains characters unsafe for JS template."""
    # .invalid — служебная запись Squid, пропускаем
    if domain == ".invalid":
        return domain
    check = domain.lstrip(".")  # убираем leading dot для проверки
    if not check or not _DOMAIN_RE.match(domain):
        raise ValueError(f"Unsafe domain name rejected for PAC: {domain!r}")
    return domain

def render_pac(domains: list[str], domain: str) -> str:
    validated = [_validate_domain(d) for d in domains]
    template = env.get_template("proxy.pac.j2")
    return template.render(domains=validated, domain=domain)