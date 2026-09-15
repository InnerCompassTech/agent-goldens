from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "fixtures" / "seed.json"


def _parse_day(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@dataclass
class World:
    as_of: date
    refund_window_days: int
    customers: list[dict[str, Any]]
    orders: dict[str, dict[str, Any]]
    refunds: list[dict[str, Any]]
    tickets: list[dict[str, Any]]
    notes: list[dict[str, Any]]
    policy: dict[str, Any]
    audit: list[dict[str, Any]] = field(default_factory=list)
    _ids: dict[str, int] = field(default_factory=lambda: {"REF": 9001, "TCK": 0, "NOTE": 0})

    @classmethod
    def from_seed(cls, path: Path | None = None) -> "World":
        raw = json.loads((path or SEED_PATH).read_text())
        orders = {row["id"]: deepcopy(row) for row in raw["orders"]}
        refunds = deepcopy(raw["refunds"])
        max_ref = 9000
        for row in refunds:
            try:
                max_ref = max(max_ref, int(str(row["id"]).split("-")[1]))
            except (IndexError, ValueError):
                pass
        return cls(
            as_of=_parse_day(raw["as_of"]) or date(2026, 9, 14),
            refund_window_days=int(raw["refund_window_days"]),
            customers=deepcopy(raw["customers"]),
            orders=orders,
            refunds=refunds,
            tickets=deepcopy(raw.get("tickets", [])),
            notes=deepcopy(raw.get("notes", [])),
            policy=deepcopy(raw.get("policy", {})),
            _ids={"REF": max_ref, "TCK": 0, "NOTE": 0},
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of.isoformat(),
            "refund_window_days": self.refund_window_days,
            "customers": deepcopy(self.customers),
            "orders": deepcopy(self.orders),
            "refunds": deepcopy(self.refunds),
            "tickets": deepcopy(self.tickets),
            "notes": deepcopy(self.notes),
            "policy": deepcopy(self.policy),
        }

    def next_id(self, prefix: str) -> str:
        self._ids[prefix] = self._ids.get(prefix, 0) + 1
        return f"{prefix}-{self._ids[prefix]:04d}"

    def order(self, order_id: str) -> dict[str, Any] | None:
        return self.orders.get(order_id)

    def refunds_for(self, order_id: str) -> list[dict[str, Any]]:
        return [row for row in self.refunds if row["order_id"] == order_id]

    def refund_sum(self, order_id: str) -> int:
        return sum(int(row["amount_cents"]) for row in self.refunds_for(order_id))

    def days_since_delivery(self, order_id: str) -> int | None:
        order = self.order(order_id)
        if not order or not order.get("delivered_at"):
            return None
        delivered = _parse_day(order["delivered_at"])
        if delivered is None:
            return None
        return (self.as_of - delivered).days

    def refund_eligible(self, order_id: str, amount_cents: int) -> tuple[bool, str]:
        order = self.order(order_id)
        if order is None:
            return False, "order_not_found"
        if order["status"] != "delivered":
            return False, f"status_is_{order['status']}"
        days = self.days_since_delivery(order_id)
        if days is None:
            return False, "not_delivered"
        if days > self.refund_window_days:
            return False, "outside_window"
        if self.refunds_for(order_id):
            return False, "already_refunded"
        if amount_cents <= 0:
            return False, "amount_not_positive"
        if amount_cents > int(order["amount_cents"]):
            return False, "amount_exceeds_order"
        return True, "ok"

    def log(self, tool: str, args: dict[str, Any], result: dict[str, Any]) -> None:
        self.audit.append({"tool": tool, "args": deepcopy(args), "ok": bool(result.get("ok"))})
