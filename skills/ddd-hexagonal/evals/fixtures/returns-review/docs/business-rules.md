# Returns Desk — Business Rules

2025-03-10 · Customer service lead

The single home of every business rule. Other documents refer to a rule by its ID and never restate it. Tests cite the ID (`@rule RT-01`). The Code column is the English code a failed check returns.

## Returns (RT)

| ID | Rule | Code |
| --- | --- | --- |
| RT-01 | A return is requested within 14 days of delivery; the delivery day is day 0. | `return_window_closed` |
| RT-02 | The refund equals the price paid for the returned items; shipping is not refunded. | – |
| RT-03 | Items marked final sale cannot be returned. | `final_sale_item` |
| RT-04 | Only returns desk staff approve or reject a return. | `not_returns_staff` |
| RT-05 | A refund goes to the original payment method. | – |
| RT-06 | Every approval and rejection is written to the audit log with the staff ID and time. | – |
| RT-07 | A return request lists at least one item. | `empty_return` |
