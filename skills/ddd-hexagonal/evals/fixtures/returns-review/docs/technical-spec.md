# Returns Desk — Technical Specification

2025-01-20 · Customer service lead

How the system is built. Rule text is in `business-rules.md`.

## Stack

| Layer | Choice |
| --- | --- |
| Language | TypeScript 5, Node 22 |
| Framework | Fastify |
| Database | PostgreSQL 16 |
| Tests | Vitest, dependency-cruiser |

## Routes and permissions

| Method | Path | Purpose | Role |
| --- | --- | --- | --- |
| POST | `/returns` | Request a return | Customer |
| GET | `/returns/{id}` | See a return | Customer (own), Staff |
| POST | `/returns/{id}/decision` | Approve or reject a return | Customer, Staff |

## Business logic

### `RefundCalculator`

The refund equals the price paid for the returned items, and shipping is never refunded. Items marked final sale are rejected before any amount is computed.

### `DecideReturn`

Enforces RT-04 in the application layer as well as on the route.

## Testing

- Unit tests per rule, tagged `@rule RT-nn`; integration tests against PostgreSQL in Docker.
