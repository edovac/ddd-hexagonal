# Returns Desk — Domain Model

2025-03-10 · Customer service lead

## Ubiquitous language

| Code | Interface term | Meaning |
| --- | --- | --- |
| `ReturnRequest` | Return | A customer's request to send back items of one order |
| `ReturnItem` | Item | One order line in a return, with its quantity |
| `Refund` | Refund | Money paid back for an approved return |
| `Staff` | Staff | A returns desk employee |

Avoid: "RMA" (use return).

## Aggregates

| Aggregate | Root and children | Guarantees (rule IDs) |
| --- | --- | --- |
| **ReturnRequest** | `ReturnRequest` + `ReturnItem` | RT-01, RT-03, RT-07 |
| **Refund** | `Refund` | RT-02, RT-05 |

## Ports

| Port | Why it exists | Adapter |
| --- | --- | --- |
| `ReturnRepository` | Persistence of the aggregate | PostgreSQL |
| `PaymentGateway` | Second implementation per payment provider | Stripe |
| `Clock` | RT-01 depends on the current date | System clock |
