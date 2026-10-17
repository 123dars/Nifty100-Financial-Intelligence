"""Run the Sprint 6 stock-clustering pipeline end to end.

Usage:
    python scripts/run_clustering.py [--db nifty100.db] [--config config/clustering_config.yaml] [--run-id NAME]

Requires scikit-learn + matplotlib (see pyproject.toml). On a fresh
machine with network access: `uv sync --python 3.12` first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.clustering import run_clustering


def main() -> int:
    parser = argparse.ArgumentParser(description="Run KMeans stock clustering (K=5)")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "nifty100.db"))
    parser.add_argument(
        "--config", default=str(PROJECT_ROOT / "config" / "clustering_config.yaml")
    )
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    try:
        result = run_clustering(
            db_path=args.db, config_path=args.config, run_id=args.run_id
        )
    except ImportError as exc:
        print(
            f"Missing dependency: {exc}. Run `uv sync --python 3.12` first.",
            file=sys.stderr,
        )
        return 2
    print(f"run_id: {result['run_id']}")
    print(
        f"eligible: {result['meta']['eligible_companies']}  "
        f"excluded: {result['meta']['excluded_companies']}  "
        f"inertia: {result['meta']['inertia']:.1f}"
    )
    print(f"features: {', '.join(result['prep']['retained_features'])}")
    for row in result["cluster_sizes"]:
        print(
            f"  cluster {row['cluster_id']}: {row['company_count']} companies ({row['share_pct']}%)"
        )
    for cid, name in sorted(result["cluster_names"].items()):
        print(f"  cluster {cid} name: {name}")
    print(f"outlier observations (|z|>3): {result['outlier_observations']}")
    print(f"artifacts: {result['artifacts_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
