from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,
)


def render_pac(domains: list[str], domain: str) -> str:
    template = env.get_template("proxy.pac.j2")
    return template.render(domains=domains, domain=domain)