from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import BASE_DIR


def get_alembic_head() -> str:
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "migrations"))
    head = ScriptDirectory.from_config(cfg).get_current_head()
    if head is None:
        raise RuntimeError("No Alembic revisions found")
    return head