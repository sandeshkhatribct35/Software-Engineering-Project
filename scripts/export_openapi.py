"""Export the OpenAPI schema that the application generates.

The committed snapshot in ``docs/openapi.json`` is what proves the API
documentation is produced from the source code rather than written by hand
(GUIDE A-8). Regenerate it after changing any route or schema:

    python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Running a file inside scripts/ puts that directory on the path, not the
# project root, so the application package is made importable explicitly.
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402  (import needs the path set above)

OUTPUT_PATH = PROJECT_ROOT / "docs" / "openapi.json"


def main() -> None:
    """Write the generated schema to docs/openapi.json."""
    schema = app.openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

    operations = sum(len(methods) for methods in schema["paths"].values())
    print(f"Wrote {OUTPUT_PATH} describing {operations} operations")


if __name__ == "__main__":
    main()
