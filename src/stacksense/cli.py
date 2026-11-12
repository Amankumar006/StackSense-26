"""Command-Line Interface (CLI) for StackSense.

Usage:
    stacksense run <scenario.json> [--output <out.json>] [--no-llm]
    stacksense batch <scenario_dir> [--output-dir <out_dir>] [--no-llm]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from stacksense.engine import RecommendationEngine


def run_single(scenario_path: str, output_path: Optional[str] = None, no_llm: bool = True) -> int:
    """Runs a single scenario JSON through StackSense."""
    path = Path(scenario_path)
    if not path.is_file():
        print(f"Error: Scenario file not found: {scenario_path}", file=sys.stderr)
        return 1

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON from {scenario_path}: {e}", file=sys.stderr)
        return 1

    engine = RecommendationEngine()
    result = engine.evaluate_scenario(raw_data, enable_llm=not no_llm)

    output_dict = result.model_dump(exclude_none=True)
    formatted_json = json.dumps(output_dict, indent=2)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(formatted_json)
            f.write("\n")
        print(f"Wrote recommendation to: {output_path}")

    # Output to stdout if no output file or if requested
    print(f"\n=== StackSense Recommendation: {result.scenario_id or path.stem} ===")
    print(f"Status:             {result.status.value}")
    print(f"Summary:            {result.summary}")
    if result.architecture_style:
        print(f"Architecture Style: {result.architecture_style.value}")
    if result.stack:
        print("Core Stack:")
        print(f"  Frontend: {result.stack.frontend.choice}")
        print(f"  Backend:  {result.stack.backend.choice}")
        print(f"  Database: {result.stack.database.choice}")
        print(f"  Hosting:  {result.stack.hosting.choice}")
        if result.stack.supporting:
            print("Supporting Services:")
            for s in result.stack.supporting:
                print(f"  - [{s.layer}]: {s.choice}")
    if result.estimated_monthly_cost_usd:
        print(f"Estimated Cost:     ${result.estimated_monthly_cost_usd.min:.0f} - ${result.estimated_monthly_cost_usd.max:.0f}/month")
    if result.warnings:
        print(f"Warnings ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"  [{w.severity.value.upper()}] {w.code}: {w.message}")
    if result.validation_errors:
        print(f"Validation Errors ({len(result.validation_errors)}):")
        for err in result.validation_errors:
            print(f"  {err.field}: {err.message}")

    return 0 if result.status.value in {"ok", "ok_with_warnings"} else 2


def run_batch(scenario_dir: str, output_dir: str = "outputs", no_llm: bool = True) -> int:
    """Runs all scenario JSON files in a directory and outputs P*_output.json."""
    dir_path = Path(scenario_dir)
    if not dir_path.is_dir():
        print(f"Error: Directory not found: {scenario_dir}", file=sys.stderr)
        return 1

    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    scenario_files = sorted(dir_path.glob("P*.json"))
    if not scenario_files:
        scenario_files = sorted(dir_path.glob("*.json"))

    print(f"Found {len(scenario_files)} scenario(s) in {scenario_dir}...")
    success_count = 0

    for sc_file in scenario_files:
        pid = sc_file.stem
        out_file = out_dir_path / f"{pid}_output.json"
        exit_code = run_single(str(sc_file), str(out_file), no_llm=no_llm)
        if exit_code in {0, 2}:
            success_count += 1

    print(f"\nBatch processing complete: {success_count}/{len(scenario_files)} scenarios processed.")
    print(f"Outputs written to: {out_dir_path.resolve()}")
    return 0


def run_web(host: str = "127.0.0.1", port: int = 8000) -> int:
    """Launches the StackSense interactive web dashboard."""
    import uvicorn
    from stacksense.web import app
    print(f"\n🚀 Starting StackSense Web Dashboard on http://{host}:{port} ...")
    print(f"Interactive UI available at: http://{host}:{port}")
    print(f"API Docs available at:        http://{host}:{port}/docs\n")
    uvicorn.run(app, host=host, port=port)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="stacksense",
        description="StackSense: An explainable, deterministic technology stack recommendation engine.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run a single scenario JSON file")
    run_parser.add_argument("scenario", type=str, help="Path to scenario JSON file")
    run_parser.add_argument("-o", "--output", type=str, default=None, help="Output path for result JSON")
    run_parser.add_argument(
        "--no-llm",
        action="store_true",
        default=True,
        help="Disable all LLM calls to guarantee 100% deterministic local evaluation (default: True)",
    )
    run_parser.add_argument(
        "--enable-llm",
        action="store_false",
        dest="no_llm",
        help="Enable optional LLM description parsing or explanation polish",
    )

    # Command: batch
    batch_parser = subparsers.add_parser("batch", help="Run a batch of scenario JSON files")
    batch_parser.add_argument("directory", type=str, help="Directory containing scenario JSON files")
    batch_parser.add_argument(
        "-o", "--output-dir", type=str, default="outputs", help="Directory where output JSONs will be saved"
    )
    batch_parser.add_argument(
        "--no-llm",
        action="store_true",
        default=True,
        help="Disable all LLM calls (default: True)",
    )

    # Command: web
    web_parser = subparsers.add_parser("web", help="Launch interactive web dashboard")
    web_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    web_parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")

    args = parser.parse_args()

    if args.command == "run":
        sys.exit(run_single(args.scenario, args.output, no_llm=args.no_llm))
    elif args.command == "batch":
        sys.exit(run_batch(args.directory, args.output_dir, no_llm=args.no_llm))
    elif args.command == "web":
        sys.exit(run_web(args.host, args.port))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
