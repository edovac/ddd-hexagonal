import { describe, expect, it } from "vitest";
import { RefundCalculator } from "../src/domain/refund-calculator";

describe("RefundCalculator", () => {
  // @rule RT-02
  it("refunds the price paid and not the shipping", () => {
    const refund = new RefundCalculator().refundFor({ itemsPaid: 4200, shippingPaid: 495 });
    expect(refund.amount).toBe(4200);
  });
});
