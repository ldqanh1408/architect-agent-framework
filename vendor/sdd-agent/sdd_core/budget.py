"""Durable cost reservations shared by a candidate and repair descendants."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from .model import SddError, Status


def candidate_root(store, change):
    seen = set()
    while change.get("parent_change"):
        identity = change["change_id"]
        if identity in seen or len(seen) >= 128:
            raise SddError("CHANGE_LINEAGE_INVALID", "Cyclic or oversized candidate lineage")
        seen.add(identity)
        change = store.read("changes", change["parent_change"])
        if change is None: raise SddError("CHANGE_LINEAGE_INVALID", "Missing parent candidate")
    return change["change_id"]


def units(value):
    try: amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise SddError("PROVIDER_BUDGET_INVALID", "Use finite nonnegative amounts") from None
    if isinstance(value, bool) or not amount.is_finite() or amount < 0:
        raise SddError("PROVIDER_BUDGET_INVALID", "Use finite nonnegative amounts")
    return int((amount * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


class Budget:
    def __init__(self, store, identity, limit):
        self.store, self.identity, self.ceiling = store, identity, units(limit)

    def _account(self):
        row = self.store.read("budgets", self.identity, {})
        return min(self.ceiling, row.get("ceiling_microusd", self.ceiling)), row.get("reserved_microusd", units(row.get("reserved_usd", 0)))

    def reserve(self, amount):
        amount = units(amount)
        with self.store.lock():
            ceiling, reserved = self._account()
            if reserved + amount > ceiling:
                raise SddError("BUDGET_EXHAUSTED", "Shared candidate and repair budget exhausted", Status.INCOMPLETE)
            self.store.write("budgets", self.identity, {"ceiling_microusd": ceiling,
                "reserved_microusd": reserved + amount, "reserved_usd": (reserved + amount) / 1_000_000})

    def report(self):
        ceiling, reserved = self._account()
        return {"account": self.identity, "ceiling_usd": ceiling / 1_000_000,
                "reserved_usd": reserved / 1_000_000, "actual_billing": "UNKNOWN"}
