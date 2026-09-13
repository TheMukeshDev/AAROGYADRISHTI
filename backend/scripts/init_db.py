"""Dev helper - create tables directly from the ORM metadata.

Useful for quick local SQLite runs; production/real PostgreSQL should use
Alembic migrations instead. Run from ``backend/``:

    python -m scripts.init_db
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.base import Base  # noqa: E402
from app.database.session import engine  # noqa: E402
from app import models  # noqa: E402,F401  ensure all tables are registered


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print(f"Tables ensured on {engine.url.render_as_string(hide_password=True)}")


if __name__ == "__main__":
    main()