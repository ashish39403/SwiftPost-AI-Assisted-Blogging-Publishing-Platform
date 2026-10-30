import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)

_env = os.environ.get("DJANGO_ENV", "dev").strip().lower()
if _env in {"prod", "production"}:
    from .production import *  # noqa: F403
else:
    from .local import *  # noqa: F403
