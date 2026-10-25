"""Persist conservative API reservations across processes and interrupted runs."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path
import sqlite3


def micros(value):
    if isinstance(value, bool):
        raise ValueError("Budget must be a finite nonnegative amount")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Invalid budget") from error
    if not amount.is_finite() or amount < 0 or amount > 1000:
        raise ValueError("Budget outside the supported range")
    return int((amount * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


class ReservationLedger:
    """One fixed ceiling per ledger, including requests with unknown billing.

    Reservations are never automatically refunded after timeout or failure.
    Reopening the ledger cannot reset or increase its ceiling.
    """
    def __init__(self, path, limit_usd=5):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        limit = micros(limit_usd)
        with sqlite3.connect(self.path, timeout=30) as db:
            db.execute("CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY CHECK(id=1), ceiling INTEGER NOT NULL, reserved INTEGER NOT NULL)")
            db.execute("INSERT OR IGNORE INTO budget VALUES(1,?,0)", (limit,))
            if db.execute("SELECT ceiling FROM budget WHERE id=1").fetchone()[0] != limit:
                raise ValueError("Existing ledger ceiling differs; it cannot be reset")

    def reserve(self, amount):
        from sdd_core.model import SddError, Status
        charge = micros(amount)
        with sqlite3.connect(self.path, timeout=30) as db:
            db.execute("BEGIN IMMEDIATE")
            changed = db.execute("UPDATE budget SET reserved=reserved+? WHERE id=1 AND reserved+?<=ceiling", (charge, charge)).rowcount
            if not changed:
                raise SddError("BUDGET_EXHAUSTED", "Shared pilot reservation ceiling reached", Status.INCOMPLETE)

    def report(self):
        with sqlite3.connect(self.path, timeout=30) as db:
            ceiling, reserved = db.execute("SELECT ceiling,reserved FROM budget WHERE id=1").fetchone()
        return {"ceiling_usd": ceiling / 1_000_000, "reserved_usd": reserved / 1_000_000,
                "billing": "UNKNOWN; conservative reservations are not invoices"}
