---
page_class: repository_documentation
---

# Running InvoiceFlow locally

## Scope and reader

How to get the invoicing stack running on a developer machine, written for someone on their first day who has
Docker and Python 3.12 and nothing else configured. It does not cover deploying to any shared environment.

## How to run

```bash
docker compose up -d postgres stripe-stub
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m invoiceflow.api --reload
```

The API is then on `http://localhost:8080`. `stripe-stub` must be up before the migration, because a seed
fixture calls it.

## Structure

`invoiceflow/api/` is the HTTP surface, `invoiceflow/invoicing/` is the aggregate and its state machine,
`invoiceflow/payments/` is the Stripe adapter, and `tests/` mirrors that layout one-to-one.

## Known limits

The Stripe stub does not implement webhooks, so slice 3 — settlement — cannot be exercised locally at all.
Hot reload drops the outbox poller; restart the process after editing anything under `invoicing/`.

## Sources

Derived from `docker-compose.yml`, `pyproject.toml`, and `alembic/env.py` as of run 7. Re-derive rather than
edit if any of those three change.
