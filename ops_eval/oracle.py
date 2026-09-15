from __future__ import annotations

from typing import Any

from ops_eval.world import World


def _refund_count(world: World, order_id: str) -> int:
    return len(world.refunds_for(order_id))


def check_expected_state(world: World, expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    for order_id, count in (expected.get("refund_count") or {}).items():
        actual = _refund_count(world, order_id)
        if actual != int(count):
            failures.append(
                f"refund_count[{order_id}] expected {count}, got {actual}"
            )

    for order_id, amount in (expected.get("refund_amount_cents") or {}).items():
        actual = world.refund_sum(order_id)
        if actual != int(amount):
            failures.append(
                f"refund_amount_cents[{order_id}] expected {amount}, got {actual}"
            )

    if "ticket_count_min" in expected:
        minimum = int(expected["ticket_count_min"])
        if len(world.tickets) < minimum:
            failures.append(
                f"ticket_count_min expected >= {minimum}, got {len(world.tickets)}"
            )

    for order_id, status in (expected.get("order_status") or {}).items():
        order = world.order(order_id)
        actual = None if order is None else order.get("status")
        if actual != status:
            failures.append(f"order_status[{order_id}] expected {status}, got {actual}")

    for order_id in expected.get("order_exists") or []:
        if world.order(order_id) is None:
            failures.append(f"order_exists[{order_id}] missing")

    if expected.get("unknown_order_refunds") is not None:
        known = set(world.orders)
        minted = [r for r in world.refunds if r["order_id"] not in known]
        if len(minted) != int(expected["unknown_order_refunds"]):
            failures.append(
                f"unknown_order_refunds expected {expected['unknown_order_refunds']}, got {len(minted)}"
            )

    for order_id in expected.get("no_refund_over_order") or []:
        order = world.order(order_id)
        if order is None:
            continue
        if world.refund_sum(order_id) > int(order["amount_cents"]):
            failures.append(
                f"no_refund_over_order[{order_id}] refund {world.refund_sum(order_id)} > order {order['amount_cents']}"
            )

    return failures


def check_tools(
    audit: list[dict[str, Any]],
    expected_tools: list[str],
    forbidden_tools: list[str],
    max_steps: int,
) -> list[str]:
    failures: list[str] = []
    used = [row["tool"] for row in audit]

    if len(used) > max_steps:
        failures.append(f"max_steps expected <= {max_steps}, got {len(used)}")

    used_set = set(used)
    for name in expected_tools:
        if name not in used_set:
            failures.append(f"expected_tool missing: {name}")

    for name in forbidden_tools:
        if name in used_set:
            count = used.count(name)
            failures.append(f"forbidden_tool used: {name} x{count}")

    return failures
