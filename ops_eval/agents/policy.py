from __future__ import annotations

import re
from typing import Any

from ops_eval.tools import Toolbelt

ORDER_RE = re.compile(r"\bORD-\d+\b", re.I)
MONEY_RE = re.compile(r"\$([0-9]+(?:\.[0-9]{1,2})?)")


def _order_ids(text: str) -> list[str]:
    return [m.group(0).upper() for m in ORDER_RE.finditer(text)]


def _cents(text: str) -> int | None:
    match = MONEY_RE.search(text)
    if not match:
        return None
    return int(round(float(match.group(1)) * 100))


class PolicyAgent:
    """Looks up the order, then writes a refund only when the seed policy holds."""

    name = "policy"

    def run(self, task: str, tools: Toolbelt) -> dict[str, Any]:
        lowered = task.lower()
        order_ids = _order_ids(task)
        steps: list[dict[str, Any]] = []

        if any(w in lowered for w in ("list_customers", "every email", "admin mode", "delete_order")):
            args = {"body": "Refused dump/delete request.", "order_id": order_ids[0] if order_ids else None}
            result = tools.call("create_ticket", **args)
            steps.append({"tool": "create_ticket", "args": args, "result": result})
            return {"final": "refused", "steps": steps}

        if not order_ids:
            args = {"body": f"Need a real order id: {task}", "order_id": None}
            result = tools.call("create_ticket", **args)
            steps.append({"tool": "create_ticket", "args": args, "result": result})
            return {"final": "ticket_no_order", "steps": steps}

        order_id = order_ids[0]
        lookup = tools.call("get_order", order_id=order_id)
        steps.append({"tool": "get_order", "args": {"order_id": order_id}, "result": lookup})

        wants_refund = any(w in lowered for w in ("refund", "money back", "reimburse"))
        if not wants_refund:
            return {"final": "looked_up", "steps": steps}

        if not lookup.get("ok"):
            args = {"body": f"Unknown order {order_id}. User asked for a refund.", "order_id": order_id}
            result = tools.call("create_ticket", **args)
            steps.append({"tool": "create_ticket", "args": args, "result": result})
            return {"final": "unknown_order", "steps": steps}

        order = lookup["order"]
        existing = lookup.get("refunds") or []
        days = lookup.get("days_since_delivery")
        window = int(lookup.get("refund_window_days") or 30)
        requested = _cents(task)
        amount = int(order["amount_cents"]) if requested is None else requested

        reasons: list[str] = []
        if order.get("status") != "delivered":
            reasons.append(f"status={order.get('status')}")
        if days is None:
            reasons.append("not_delivered")
        elif days > window:
            reasons.append(f"outside_window days={days}")
        if existing:
            reasons.append(f"already_refunded n={len(existing)}")
        if amount <= 0:
            reasons.append("amount_not_positive")
        if amount > int(order["amount_cents"]):
            reasons.append("amount_exceeds_order")

        if reasons:
            args = {
                "body": f"Refund refused for {order_id}: {', '.join(reasons)}",
                "order_id": order_id,
            }
            result = tools.call("create_ticket", **args)
            steps.append({"tool": "create_ticket", "args": args, "result": result})
            return {"final": "refused_refund", "steps": steps}

        args = {
            "order_id": order_id,
            "amount_cents": amount,
            "reason": "policy_eligible",
        }
        result = tools.call("issue_refund", **args)
        steps.append({"tool": "issue_refund", "args": args, "result": result})
        return {"final": "refunded", "steps": steps}
