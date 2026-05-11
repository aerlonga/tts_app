from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.repositories.db import initialize_database


def main() -> None:
    settings = get_settings()
    initialize_database(settings.database_url)
    print(f"Database initialized at {settings.database_url}")


if __name__ == "__main__":
    main()
