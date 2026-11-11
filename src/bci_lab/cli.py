"""Command-line entry point. No download or training happens on import."""
import argparse
from pathlib import Path
from .evaluation import run_benchmark


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate EEG imagery on a separate recording day.")
    parser.add_argument("--subjects", nargs="+", type=int, choices=range(1, 10), default=list(range(1, 10)))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("web/data/benchmark.json"))
    parser.add_argument("--sources", type=Path, default=Path("data/sources.json"))
    parser.add_argument("--download", action="store_true", help="Download missing original BNCI recordings (up to ~800 MB for all participants)")
    args = parser.parse_args(argv)
    try:
        report = run_benchmark(args.subjects, args.raw_dir, args.output, args.sources, args.download)
    except (ValueError, OSError) as error:
        parser.exit(1, f"BCI Lab: {error}\n")
    print(f"Report: {args.output} ({len(report['subjects'])} participants)")


if __name__ == "__main__":
    main()
