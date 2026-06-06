"""Runtime-owned market provider registry."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any


MARKET_MODULES = {
    "us": "sec_provider",
    "cn": "akshare_provider",
    "hk": "akshare_provider",
    "jp": "edinet_provider",
    "kr": "dart_provider",
    "tw": "finmind_provider",
    "eu": "openesef_provider",
}


@dataclass(frozen=True)
class ModuleProvider:
    module: Any

    @property
    def name(self) -> str:
        return str(getattr(self.module, "PROVIDER", self.module.__name__.split(".")[-1]))

    def fetch(self, request: dict[str, Any]) -> dict[str, Any]:
        return self.module.fetch(request)

    def dependency_available(self) -> bool:
        check = getattr(self.module, "dependency_available", None)
        return bool(check()) if check else True


def load_provider(market: str) -> ModuleProvider:
    module_name = MARKET_MODULES.get(market)
    if not module_name:
        raise ValueError(f"unsupported market: {market}")
    module = importlib.import_module(f"{__name__}.{module_name}")
    return ModuleProvider(module)
