"""
JSON RPC for Hermes terminal tool calls.

Examples:
  python scripts/hermes_tool_rpc.py --list
  python scripts/hermes_tool_rpc.py --tool get_data_version
  python scripts/hermes_tool_rpc.py --tool run_full_research --args "{\"strategy_path\":\"strategies/defs/momentum_cross_section_v1.yaml\"}"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.hermes_bridge.dispatcher import dispatch_tool  # noqa: E402
from agents.hermes_bridge.tool_schemas import TOOL_SCHEMAS, list_tool_names  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes tool RPC for Trading Agent")
    parser.add_argument("--list", action="store_true", help="List tool names")
    parser.add_argument("--schemas", action="store_true", help="Print OpenAI tool schemas JSON")
    parser.add_argument("--tool", default=None, help="Tool name to invoke")
    parser.add_argument("--args", default="{}", help="JSON object of tool arguments")
    parser.add_argument("--args-file", default=None, help="Path to JSON args file")
    args = parser.parse_args()

    if args.list:
        print(json.dumps(list_tool_names(), indent=2))
        return 0
    if args.schemas:
        print(json.dumps(TOOL_SCHEMAS, indent=2))
        return 0
    if not args.tool:
        parser.error("--tool is required unless --list/--schemas")

    if args.args_file:
        payload = json.loads(Path(args.args_file).read_text(encoding="utf-8"))
    else:
        payload = json.loads(args.args)

    result = dispatch_tool(args.tool, payload)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
