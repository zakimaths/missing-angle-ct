"""Headless entry points for repeatable runs and replay."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from .bundle import export_bundle, json_bytes, load_bundle, verify_replay
from .config import ExperimentConfig
from .experiment import run_experiment


def main():
    parser = argparse.ArgumentParser(description="Missing-Angle CT: local synthetic experiments")
    commands = parser.add_subparsers(dest="command", required=True)
    app = commands.add_parser("app", help="Open the local interactive lab")
    app.add_argument("--port", type=int, default=8501)
    app.add_argument("--open", action="store_true", help="Open the app in your default browser")
    run = commands.add_parser("run", help="Compute and save a reproducible experiment")
    run.add_argument("--config", type=Path)
    run.add_argument("--output", type=Path, required=True)
    public = commands.add_parser("public-ct", help="Simulate projections from a bundled acquired CT slice")
    public.add_argument("--slice", type=int, default=80)
    public.add_argument("--config", type=Path)
    public.add_argument("--output", type=Path, required=True)
    public.add_argument("--refine", action="store_true", help="Save SART + smoothing and its actual iteration history")
    public.add_argument("--smoothing", type=float, default=.002)
    public.add_argument("--refinement-passes", type=int, default=10)
    replay = commands.add_parser("replay", help="Check saved arrays against a fresh reconstruction")
    replay.add_argument("bundle", type=Path)
    replay.add_argument("--output", type=Path)
    bench = commands.add_parser("benchmark", help="Evaluate a known-location contrast threshold")
    bench.add_argument("--output", type=Path, required=True)
    bench.add_argument("--smoke", action="store_true", help="Small pipeline check, not a performance estimate")
    bench.add_argument("--save-bundles", action="store_true", help="Keep every experiment's actual arrays")
    args = parser.parse_args()
    try:
        if args.command == "app":
            if not 1024 <= args.port <= 65535:
                parser.error("port must be 1024..65535")
            return subprocess.call([sys.executable, "-m", "streamlit", "run",
                                    str(Path(__file__).with_name("app.py")),
                                    "--server.address=127.0.0.1", f"--server.port={args.port}",
                                    f"--server.headless={'false' if args.open else 'true'}",
                                    "--browser.gatherUsageStats=false"])
        if args.command in ("run", "public-ct"):
            config = ExperimentConfig.from_dict(json.loads(args.config.read_text())) if args.config else ExperimentConfig()
            if args.command == "public-ct":
                from .public_ct import run_public_ct
                exp = run_public_ct(args.slice, config)
                if args.refine:
                    from .refinement import refine
                    exp = refine(exp, args.refinement_passes, args.smoothing)
            else:
                exp = run_experiment(config)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(export_bundle(exp))
            print(json_bytes({"bundle": str(args.output), "metrics": exp.metrics}).decode())
        elif args.command == "replay":
            exp, manifest = load_bundle(args.bundle.read_bytes())
            report = verify_replay(exp, manifest)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_bytes(json_bytes(report))
            print(json_bytes(report).decode())
            return 0 if all(c["within_tolerance"] for c in report["checks"].values()) else 1
        else:
            from .benchmark import benchmark
            benchmark(args.output, args.smoke, args.save_bundles)
            print(f"Saved observations and summary to {args.output}")
    except (ValueError, OSError) as error:
        print(f"Could not complete the experiment: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
