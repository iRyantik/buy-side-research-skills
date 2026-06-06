"""Source Intake public CLI."""

import argparse
import json
from pathlib import Path

from ..source_intake import IntakeRequest, SourceIntake


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register, convert, and route research sources")
    parser.add_argument("command", choices=("add", "scan", "publish", "status", "check-deps"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--topic")
    parser.add_argument("--category")
    parser.add_argument("--source-url")
    parser.add_argument("--reproducible", action="store_true")
    parser.add_argument("--recursive", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "check-deps":
        print(json.dumps({"core": {"status": "ok"}, "optional": {"pypdf": "first-use"}}))
        return 0
    intake = SourceIntake(Path(args.workspace))
    if args.command == "add":
        result = intake.add(
            IntakeRequest(
                source=Path(args.value),
                topic=args.topic,
                category=args.category,
                source_url=args.source_url,
                reproducible=args.reproducible,
            )
        )
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0
    if args.command == "scan":
        results = intake.scan(Path(args.value or "_inbox"), recursive=args.recursive)
        print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))
        return 0
    if args.command == "publish":
        result = intake.publish(args.value, args.topic, args.category)
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(intake.status(args.value), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
