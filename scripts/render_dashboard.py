"""CLI: render HTML dashboard from a research_report.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reports_ui.render_dashboard import write_dashboard  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Stage 10 research dashboard HTML")
    parser.add_argument("report_json", help="Path to research_report.json")
    parser.add_argument("--out", default=None, help="Output HTML path")
    args = parser.parse_args()
    out = write_dashboard(args.report_json, args.out)
    print(json.dumps({"dashboard": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
