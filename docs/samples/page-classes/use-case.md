---
page_class: use_case
id: UC-004
title: Freelancer sends an invoice to a client
actors: [freelancer, client, Stripe]
traces: { req: [REQ-002, REQ-007], api: [API-invoice-send], scn: [SCN-002], module: [20-invoicing] }
---

# UC-004 — Freelancer sends an invoice to a client

## Actor and trigger

The freelancer is the primary actor. The client is secondary and only receives email. The trigger is the
freelancer pressing **Send** on an invoice in `DRAFT`.

## Preconditions

The invoice exists, is in `DRAFT`, has at least one line item and a syntactically valid client email. The
Stripe account is connected — guaranteed by UC-001.

## Main flow

1. The freelancer selects a `DRAFT` invoice and confirms sending.
2. The system freezes the invoice contents and allocates a sequential invoice number.
3. The system calls `payments-adapter` to create a checkout session.
4. The system moves the invoice to `SENT`.
5. The system emails the payment link to the client.
6. The system writes an `InvoiceSent` event to the outbox.

## Alternate flows

- **3a.** The client already holds an unexpired link: reuse it, create no new session, continue at step 4.
- **5a.** The freelancer chooses to send the email themselves: skip step 5, the invoice still moves to `SENT`,
  and the delivery channel is recorded as manual.

## Exception flows

- **3b.** Stripe returns an error or a rate limit: the invoice **stays in `DRAFT`**, the allocated number is
  not reused, and the system shows the error with its code and offers a retry. No email is sent.
- **5b.** The email bounces: the invoice stays `SENT`, the system marks delivery as failed and prompts the
  freelancer to send manually.

## Postconditions

**Success:** the invoice is `SENT`, has a number, has an unexpired payment link, and one `InvoiceSent` event
exists. **Failure:** the invoice is `DRAFT`, with no link, no event, and one coded error record.

## Acceptance

Sending a two-line `DRAFT` invoice yields, within 5 seconds: status `SENT`, a Stripe link that opens, and one
message in the test mailbox. Forcing Stripe to return `429` leaves the invoice in `DRAFT` with no email sent.

## Traceability

REQ-002, REQ-007 · API-invoice-send · SCN-002 · modules `20-invoicing`, `10-payments-adapter`
