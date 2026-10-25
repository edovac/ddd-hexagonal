# Returns Desk — Functional Specification

2024-11-02 · Customer service lead

What the system does and why. Rules are in `business-rules.md` and are referenced here by ID.

## Purpose and context

The returns desk of an online homeware shop handles return requests from customers and refunds them.

- **Users:** about 4,000 orders a month, 3 returns desk staff.
- **Interface:** English, web.

## Users and roles

| Role | Can do | Sees |
| --- | --- | --- |
| Customer | Request a return for own orders | Own returns |
| Staff | Decide returns, see all returns | All returns |

Access rules: RT-04.

## Behaviour

### Requesting a return

- Customers can return items within 30 days of delivery (RT-01). They pick the items and give a reason.
- Final sale items are shown but cannot be selected (RT-03).

### Gift cards

- A customer may return an unused gift card; the value comes back as store credit.

### Deciding and refunding

- Staff inspect the returned parcel and approve or reject the request (RT-04).
- On approval the refund is paid automatically (RT-02, RT-05).

## Scope and rollout

**Out of scope**

- Exchanges for another item.
- Gift cards: they are sold and handled by the partner platform.

**Open points**

- [ ] Do we refund return shipping for damaged items? — customer service lead.
