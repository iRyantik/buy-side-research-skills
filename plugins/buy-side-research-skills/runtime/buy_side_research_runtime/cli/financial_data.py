"""Financial Data public CLI."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ..financial_data import FactsRepository, LegacyMigrator
from ..financial_data.pipeline import FinancialDataPipeline, FinancialRequest
from ..financial_data.providers import MARKET_MODULES, load_provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch, migrate, and render canonical financial facts")
    parser.add_argument("command", choices=("fetch", "render", "migrate", "check-deps"))
    parser.add_argument("ticker", nargs="?")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--company-root")
    parser.add_argument("--market", choices=sorted(MARKET_MODULES))
    parser.add_argument("--profile", choices=("lite", "full"), default="lite")
    parser.add_argument("--from", dest="from_value")
    parser.add_argument("--to", dest="to_value")
    parser.add_argument("--periods", choices=("3Y",), help="Deprecated compatibility option")
    parser.add_argument("--all", action="store_true", dest="all_companies")
    parser.add_argument("--group")
    return parser


def _find_company(workspace: Path, ticker: str) -> Path:
    matches = [
        path
        for path in (workspace / "industry").glob("*/companies/*")
        if path.is_dir() and path.name.lower() == ticker.lower()
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one company directory for {ticker}, found {len(matches)}")
    return matches[0]


def infer_market(ticker: str | None) -> str:
    """Best-effort market inference for zero-to-one skill workflows."""
    if not ticker:
        return "us"
    normalized = ticker.strip().upper()
    known_aliases = {
        "2330": "tw",  # TSMC; bare four-digit TW tickers conflict with JP codes.
    }
    if normalized in known_aliases:
        return known_aliases[normalized]
    suffix_map = {
        ".HK": "hk",
        ".KS": "kr",
        ".KQ": "kr",
        ".TW": "tw",
        ".TT": "tw",
        ".SS": "cn",
        ".SH": "cn",
        ".SZ": "cn",
        ".ST": "eu",
    }
    for suffix, market in suffix_map.items():
        if normalized.endswith(suffix):
            return market
    if normalized.isdigit():
        if len(normalized) == 6:
            return "cn"
        if len(normalized) == 4:
            return "jp"
    return "us"


def _default_company_root(workspace: Path, ticker: str) -> Path:
    safe_ticker = ticker.strip().replace("\\", "-").replace("/", "-")
    return workspace / "industry" / "uncategorized" / "companies" / safe_ticker


def _resolve_companies(args: argparse.Namespace, workspace: Path) -> list[Path]:
    if args.all_companies:
        return [path for path in (workspace / "industry").glob("*/companies/*") if path.is_dir()]
    if not args.ticker and not args.company_root:
        raise SystemExit("ticker or --company-root is required")
    if args.company_root:
        return [Path(args.company_root).resolve()]
    if args.command == "fetch":
        try:
            return [_find_company(workspace, args.ticker)]
        except RuntimeError as exc:
            if "found 0" not in str(exc):
                raise
            return [_default_company_root(workspace, args.ticker).resolve()]
    return [_find_company(workspace, args.ticker)]


def migrate_actuals(company_root: Path) -> dict[str, str | list[str]]:
    company_root = Path(company_root).resolve()
    internal = company_root / "_cache" / "financial-data" / "internal"
    actuals_path = internal / "actuals-resolved.json"
    if not actuals_path.exists():
        raise FileNotFoundError(actuals_path)
    data = json.loads(actuals_path.read_text(encoding="utf-8-sig"))
    if data.get("_write_policy") == "generated-read-model" and (internal / "facts-store.json").exists():
        return {
            "facts_store": str(internal / "facts-store.json"),
            "actuals_view": str(actuals_path),
            "backup": "",
            "detected_shapes": ["already-migrated"],
        }
    backup_dir = internal / "legacy-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = backup_dir / f"actuals-resolved.{stamp}.json"
    shutil.copy2(actuals_path, backup)
    stage = internal / f".migration-stage-{stamp}"

    entity = {
        "ticker": data.get("ticker") or company_root.name,
        "company": data.get("company") or data.get("company_name"),
        "market": data.get("market"),
        "currency": data.get("currency"),
    }
    migrated = LegacyMigrator().convert(data, entity)
    if not migrated.facts:
        raise RuntimeError(
            f"migration refused: no canonical facts detected in {actuals_path}; backup preserved"
        )
    repo = FactsRepository(stage, entity={key: value for key, value in entity.items() if value})
    for period in migrated.periods:
        repo.upsert_period(period)
    repo.merge(migrated.facts)
    repo.store["segments"] = migrated.segments
    existing_sources = {
        item.get("source_id"): item for item in repo.store["sources"] if item.get("source_id")
    }
    for source in migrated.sources:
        existing_sources[source.get("source_id")] = source
    repo.store["sources"] = list(existing_sources.values())
    migrated_at = datetime.now(timezone.utc).isoformat()
    if migrated.market_snapshot:
        repo.append_snapshot("market", {"as_of": migrated_at, **migrated.market_snapshot})
    if migrated.consensus_snapshot:
        repo.append_snapshot("consensus", {"as_of": migrated_at, **migrated.consensus_snapshot})
    repo.store["migration_history"].append(
        {
            "migrated_at_utc": migrated_at,
            "backup": str(backup),
            "detected_shapes": list(migrated.detected_shapes),
        }
    )
    repo.commit()
    repo.render_actuals()
    for name in (
        "facts-store.json",
        "market-snapshots.jsonl",
        "consensus-snapshots.jsonl",
        "actuals-resolved.json",
    ):
        staged = stage / name
        if staged.exists():
            staged.replace(internal / name)
    shutil.rmtree(stage, ignore_errors=True)
    return {
        "facts_store": str(internal / "facts-store.json"),
        "actuals_view": str(actuals_path),
        "backup": str(backup),
        "detected_shapes": list(migrated.detected_shapes),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace = Path(args.workspace).resolve()
    if args.command == "check-deps":
        markets = [args.group] if args.group in MARKET_MODULES else sorted(MARKET_MODULES)
        result = {}
        for market in markets:
            provider = load_provider(market)
            result[market] = {"provider": provider.name, "available": provider.dependency_available()}
        print(json.dumps(result, indent=2))
        return 0

    companies = _resolve_companies(args, workspace)

    results = []
    for company in companies:
        if args.command == "migrate":
            try:
                results.append(migrate_actuals(company))
            except Exception as exc:
                if not args.all_companies:
                    raise
                results.append({"company": str(company), "status": "skipped", "reason": str(exc)})
            continue
        internal = company / "_cache" / "financial-data" / "internal"
        if args.command == "render":
            view = FactsRepository(internal).render_actuals()
            results.append({"actuals_view": str(internal / "actuals-resolved.json"), "schema": view["_schema"]})
            continue
        market = args.market or infer_market(args.ticker or company.name)
        provider = load_provider(market)
        request = FinancialRequest(
            ticker=args.ticker or company.name,
            market=market,
            profile=args.profile,
            from_value=args.from_value,
            to_value=args.to_value,
            complete_years=3 if args.periods == "3Y" and not args.from_value else None,
        )
        results.append(FinancialDataPipeline(company, provider).fetch(request).__dict__)
    print(json.dumps(results[0] if len(results) == 1 else results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
