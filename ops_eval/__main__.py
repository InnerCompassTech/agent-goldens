from __future__ import annotations

import argparse
import json

from ops_eval.agents import AGENTS
from ops_eval.goldens import load_cases
from ops_eval.runner import format_report, run_suite


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m ops_eval",
        description="Grade a support-ops agent against world state, not the transcript.",
    )
    parser.add_argument("--agent", default="reference", choices=sorted(AGENTS))
    parser.add_argument("--case", dest="case_id", help="Run one case, e.g. TC-03")
    parser.add_argument("--list", action="store_true", help="Print goldens and exit")
    parser.add_argument("--json", action="store_true", help="Machine-readable results")
    args = parser.parse_args()

    if args.list:
        for case in load_cases():
            print(f"{case['id']:6}  {case['name']}")
        return

    results = run_suite(args.agent, args.case_id)
    if args.json:
        slim = [
            {
                "id": r["id"],
                "name": r["name"],
                "agent": r["agent"],
                "passed": r["passed"],
                "tool_fails": r["tool_fails"],
                "state_fails": r["state_fails"],
                "tools_used": r["tools_used"],
                "final": r["final"],
            }
            for r in results
        ]
        print(json.dumps(slim, indent=2))
    else:
        print(format_report(results), end="")

    if any(not r["passed"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
