from __future__ import annotations

from typing import Any

from ops_eval.agents import AGENTS
from ops_eval.goldens import load_cases
from ops_eval.oracle import check_expected_state, check_tools
from ops_eval.tools import Toolbelt
from ops_eval.world import World


def run_case(agent_name: str, case: dict[str, Any]) -> dict[str, Any]:
    cls = AGENTS[agent_name]
    agent = cls()
    world = World.from_seed()
    tools = Toolbelt(world)
    output = agent.run(case["task"], tools)
    tool_fails = check_tools(
        world.audit,
        case.get("expected_tools") or [],
        case.get("forbidden_tools") or [],
        int(case.get("max_steps") or 8),
    )
    state_fails = check_expected_state(world, case.get("expected_state") or {})
    passed = not tool_fails and not state_fails
    return {
        "id": case["id"],
        "name": case["name"],
        "agent": agent.name,
        "passed": passed,
        "tool_fails": tool_fails,
        "state_fails": state_fails,
        "tools_used": [row["tool"] for row in world.audit],
        "refunds": list(world.refunds),
        "tickets": list(world.tickets),
        "final": output.get("final"),
        "failure_mode": case.get("failure_mode"),
    }


def run_suite(agent_name: str, case_id: str | None = None) -> list[dict[str, Any]]:
    if agent_name not in AGENTS:
        raise SystemExit(f"unknown agent {agent_name!r}. choose: {', '.join(AGENTS)}")
    cases = load_cases()
    if case_id:
        cases = [c for c in cases if c["id"] == case_id]
        if not cases:
            raise SystemExit(f"unknown case {case_id}")
    return [run_case(agent_name, case) for case in cases]


def format_report(results: list[dict[str, Any]]) -> str:
    lines = []
    passed = sum(1 for r in results if r["passed"])
    lines.append(f"agent={results[0]['agent'] if results else '?'}  {passed}/{len(results)} passed")
    lines.append("")
    for row in results:
        mark = "PASS" if row["passed"] else "FAIL"
        lines.append(f"  {mark}  {row['id']}  {row['name']}")
        lines.append(f"        tools: {', '.join(row['tools_used']) or '(none)'}")
        for fail in row["tool_fails"]:
            lines.append(f"        tool  — {fail}")
        for fail in row["state_fails"]:
            lines.append(f"        state — {fail}")
        if row["id"] == "TC-03" and not row["passed"]:
            extra = [r["id"] for r in row["refunds"] if r["order_id"] == "ORD-1003"]
            lines.append(f"        teaching clip: ORD-1003 refund rows = {extra}")
            if row.get("failure_mode"):
                lines.append(f"        {row['failure_mode']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
