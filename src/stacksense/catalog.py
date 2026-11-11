"""Technology catalogue loader and query interface."""

import json
from pathlib import Path
from typing import Any, Optional

CATALOGUE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "technology-catalog" / "catalogue.json"


class TechnologyCatalog:
    """Provides structured queries against the versioned technology catalogue."""

    def __init__(self, catalog_path: Optional[Path] = None):
        path = catalog_path or CATALOGUE_PATH
        with open(path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self.version = self._data.get("catalogue_version", "1.0.0")
        self.reviewed_at = self._data.get("reviewed_at", "2026-11-10")
        self.technologies: dict[str, dict[str, Any]] = {
            t["id"]: t for t in self._data.get("technologies", [])
        }
        self.rules: list[dict[str, Any]] = self._data.get("compatibility_rules", [])

    def get_by_id(self, tech_id: str) -> Optional[dict[str, Any]]:
        return self.technologies.get(tech_id)

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        return [t for t in self.technologies.values() if t.get("category") == category]

    def get_all(self) -> list[dict[str, Any]]:
        return list(self.technologies.values())


# Global singleton instance for high-speed local lookups
_default_catalog: Optional[TechnologyCatalog] = None


def get_default_catalog() -> TechnologyCatalog:
    global _default_catalog
    if _default_catalog is None:
        _default_catalog = TechnologyCatalog()
    return _default_catalog
