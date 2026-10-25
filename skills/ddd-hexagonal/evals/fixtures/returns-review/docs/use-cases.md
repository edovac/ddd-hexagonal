# Returns Desk — Use Cases

2025-03-10 · Customer service lead

A use case names the rules it applies by ID; `business-rules.md` states them.

## Returns

| ID | Use case | Actor | Main flow | Rules | Home |
| --- | --- | --- | --- | --- | --- |
| UC-01 | Request a return | Customer | Pick order → pick items → give reason → request saved as pending | RT-01, RT-03, RT-07 | `RequestReturn` |
| UC-02 | Decide a return | Staff | Open pending request → inspect items → approve or reject | RT-04, RT-09 | `DecideReturn` |
| UC-03 | Issue a refund | System | Approved return → compute refund → pay back | RT-02, RT-05 | `IssueRefund` |
